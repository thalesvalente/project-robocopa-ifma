-- I3-03C: additive private worker-command boundary. No student/provider tokens.
-- Apply once after 001+002. Reapplication fails atomically; never resets data.
BEGIN;
CREATE ROLE rc_worker_api NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
SET LOCAL ROLE rc_control_owner;
CREATE TABLE rc_control.worker_credentials (
  credential_sha256 text PRIMARY KEY CHECK (credential_sha256 ~ '^[0-9a-f]{64}$'),
  worker_id uuid NOT NULL REFERENCES rc_control.workers,
  scope_id text NOT NULL CHECK(scope_id ~ '^[a-z][a-z0-9-]{0,31}$'),
  issued_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  expires_at timestamptz NOT NULL,
  revoked boolean NOT NULL DEFAULT false,
  CHECK(expires_at>issued_at AND expires_at<=issued_at+interval '900 seconds')
);
CREATE TABLE rc_control.worker_request_clock (
  worker_id uuid PRIMARY KEY REFERENCES rc_control.workers,
  next_allowed_at timestamptz NOT NULL
);
CREATE TABLE rc_control.worker_receipts (
  worker_id uuid NOT NULL REFERENCES rc_control.workers,
  request_id uuid NOT NULL,
  operation text NOT NULL CHECK(operation IN ('claim','start','heartbeat','fail')),
  arguments jsonb NOT NULL CHECK(jsonb_typeof(arguments)='object'),
  response jsonb NOT NULL CHECK(jsonb_typeof(response)='object'),
  expires_at timestamptz NOT NULL,
  PRIMARY KEY(worker_id,request_id)
);
ALTER TABLE rc_control.worker_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE rc_control.worker_credentials FORCE ROW LEVEL SECURITY;
CREATE POLICY owner_only ON rc_control.worker_credentials TO rc_control_owner USING(true) WITH CHECK(true);
ALTER TABLE rc_control.worker_request_clock ENABLE ROW LEVEL SECURITY;
ALTER TABLE rc_control.worker_request_clock FORCE ROW LEVEL SECURITY;
CREATE POLICY owner_only ON rc_control.worker_request_clock TO rc_control_owner USING(true) WITH CHECK(true);
ALTER TABLE rc_control.worker_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE rc_control.worker_receipts FORCE ROW LEVEL SECURITY;
CREATE POLICY owner_only ON rc_control.worker_receipts TO rc_control_owner USING(true) WITH CHECK(true);

CREATE FUNCTION rc_control.worker_command(p_digest text,p_request uuid,p_operation text,p_args jsonb)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE c rc_control.worker_credentials; w rc_control.workers;
  receipt rc_control.worker_receipts; j rc_control.jobs; v jsonb; result jsonb;
  cfg rc_control.settings; next_allowed timestamptz; t timestamptz;
  job uuid; attempt uuid; fence_value bigint; expires timestamptz;
BEGIN
  -- Existing lock order: settings -> credential -> worker -> job -> attempt.
  SELECT * INTO STRICT cfg FROM rc_control.settings WHERE singleton FOR SHARE;
  IF p_digest IS NULL OR p_digest !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'CREDENTIAL_DENIED'; END IF;
  SELECT * INTO c FROM rc_control.worker_credentials WHERE credential_sha256=p_digest FOR SHARE;
  IF NOT FOUND OR c.revoked OR c.issued_at>clock_timestamp() OR c.expires_at<=clock_timestamp() THEN
    RAISE EXCEPTION 'CREDENTIAL_DENIED';
  END IF;
  SELECT * INTO w FROM rc_control.workers WHERE worker_id=c.worker_id FOR UPDATE;
  IF NOT FOUND OR NOT w.active OR w.scope_id<>c.scope_id THEN RAISE EXCEPTION 'CREDENTIAL_DENIED'; END IF;
  t:=clock_timestamp();
  IF c.expires_at<=t THEN RAISE EXCEPTION 'CREDENTIAL_DENIED'; END IF;
  IF NOT cfg.enabled THEN RAISE EXCEPTION 'EXECUTION_DISABLED'; END IF;
  IF p_request IS NULL OR p_operation IS NULL OR p_operation NOT IN ('claim','start','heartbeat','fail')
    OR jsonb_typeof(p_args) IS DISTINCT FROM 'object' OR octet_length(p_args::text)>1024 THEN
    RAISE EXCEPTION 'COMMAND_INVALID';
  END IF;
  IF p_operation='claim' THEN
    IF p_args<>'{}'::jsonb THEN RAISE EXCEPTION 'COMMAND_INVALID'; END IF;
  ELSE
    IF NOT p_args ?& ARRAY['job_id','attempt_id','fence'] OR
       p_args - (CASE WHEN p_operation='fail' THEN ARRAY['job_id','attempt_id','fence','reason']
                 ELSE ARRAY['job_id','attempt_id','fence'] END)<>'{}'::jsonb
       OR jsonb_typeof(p_args->'job_id') IS DISTINCT FROM 'string'
       OR jsonb_typeof(p_args->'attempt_id') IS DISTINCT FROM 'string'
       OR jsonb_typeof(p_args->'fence') IS DISTINCT FROM 'string'
       OR (p_args->>'job_id') !~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
       OR (p_args->>'attempt_id') !~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
       OR (p_args->>'fence') !~ '^[1-9][0-9]{0,18}$' THEN RAISE EXCEPTION 'COMMAND_INVALID'; END IF;
    IF p_operation='fail' AND (jsonb_typeof(p_args->'reason') IS DISTINCT FROM 'string' OR
       p_args->>'reason' NOT IN ('WORKER_STOPPED','ENGINE_FAILURE','RESOURCE_LIMIT')) THEN
       RAISE EXCEPTION 'COMMAND_INVALID'; END IF;
    job:=(p_args->>'job_id')::uuid; attempt:=(p_args->>'attempt_id')::uuid;
    BEGIN fence_value:=(p_args->>'fence')::bigint;
    EXCEPTION WHEN numeric_value_out_of_range THEN RAISE EXCEPTION 'COMMAND_INVALID'; END;
  END IF;
  SELECT * INTO receipt FROM rc_control.worker_receipts WHERE worker_id=w.worker_id AND request_id=p_request;
  IF FOUND THEN
    IF receipt.operation<>p_operation OR receipt.arguments<>p_args THEN RAISE EXCEPTION 'REQUEST_CONFLICT'; END IF;
    IF receipt.expires_at<=t THEN RAISE EXCEPTION 'REQUEST_EXPIRED'; END IF;
    IF p_operation IN ('claim','start','heartbeat') AND receipt.response->'result'<>'null'::jsonb THEN
      IF p_operation='claim' THEN
        job:=(receipt.response#>>'{result,job_id}')::uuid;
        attempt:=(receipt.response#>>'{result,attempt_id}')::uuid;
        fence_value:=(receipt.response#>>'{result,fence}')::bigint;
      END IF;
      j:=rc_control.lock_lease(w.worker_id,job,attempt,fence_value);
      IF (receipt.response#>>'{result,lease_until}')::timestamptz<=clock_timestamp() THEN
        RAISE EXCEPTION 'STALE_LEASE'; END IF;
    END IF;
    RETURN receipt.response;
  END IF;
  SELECT next_allowed_at INTO next_allowed FROM rc_control.worker_request_clock WHERE worker_id=w.worker_id;
  IF FOUND AND next_allowed>t THEN RAISE EXCEPTION 'RATE_LIMITED'; END IF;
  -- Keep request IDs for the credential lifetime; do not delete and silently re-claim.
  IF (SELECT count(*) FROM rc_control.worker_receipts WHERE worker_id=w.worker_id)>=512 THEN
    RAISE EXCEPTION 'RECEIPT_LIMIT'; END IF;
  IF p_operation='claim' THEN
    IF EXISTS(SELECT 1 FROM rc_control.jobs WHERE worker_id=w.worker_id AND state IN ('LEASED','RUNNING')
       AND lease_until>clock_timestamp() AND deadline_at>clock_timestamp()) THEN RAISE EXCEPTION 'WORKER_BUSY'; END IF;
    v:=rc_control.claim(w.worker_id);
    IF v IS NOT NULL THEN v:=jsonb_set(v,'{fence}',to_jsonb(v->>'fence')); END IF;
  ELSIF p_operation IN ('start','heartbeat') THEN
    v:=rc_control.heartbeat(w.worker_id,job,attempt,fence_value,p_operation='start');
    v:=jsonb_set(v,'{fence}',to_jsonb(v->>'fence'));
  ELSE
    v:=jsonb_build_object('state',rc_control.fail_attempt(w.worker_id,job,attempt,fence_value,p_args->>'reason'));
  END IF;
  result:=jsonb_build_object('schema_version',1,'request_id',p_request,'operation',p_operation,
    'worker_id',w.worker_id,'scope_id',w.scope_id,'result',v);
  expires:=clock_timestamp()+interval '900 seconds';
  INSERT INTO rc_control.worker_receipts VALUES(w.worker_id,p_request,p_operation,p_args,result,expires);
  INSERT INTO rc_control.worker_request_clock VALUES(w.worker_id,clock_timestamp()+interval '100 milliseconds')
    ON CONFLICT(worker_id) DO UPDATE SET next_allowed_at=EXCLUDED.next_allowed_at;
  RETURN result;
END $$;
REVOKE ALL ON rc_control.worker_credentials,rc_control.worker_request_clock,rc_control.worker_receipts FROM PUBLIC,rc_broker,rc_admission,rc_worker_api;
REVOKE ALL ON FUNCTION rc_control.worker_command(text,uuid,text,jsonb) FROM PUBLIC,rc_broker,rc_admission;
GRANT USAGE ON SCHEMA rc_control TO rc_worker_api;
GRANT EXECUTE ON FUNCTION rc_control.worker_command(text,uuid,text,jsonb) TO rc_worker_api;
COMMIT;
