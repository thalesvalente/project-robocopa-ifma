-- I3-03 internal control-plane migration. Apply once to an EMPTY isolated DB.
-- Never expose this schema or rc_broker to a browser, worker or PostgREST.
-- No COMPLETE/score endpoint: validated publication belongs to I3-04.
BEGIN;
CREATE ROLE rc_control_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE rc_broker NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
GRANT rc_control_owner TO CURRENT_USER;
CREATE SCHEMA rc_control AUTHORIZATION rc_control_owner;
SET LOCAL ROLE rc_control_owner;
REVOKE ALL ON SCHEMA rc_control FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA rc_control REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

CREATE TABLE rc_control.settings (
  singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
  enabled boolean NOT NULL DEFAULT false,
  capacity integer NOT NULL DEFAULT 32 CHECK(capacity BETWEEN 1 AND 256),
  lease_seconds integer NOT NULL DEFAULT 30 CHECK(lease_seconds BETWEEN 1 AND 60),
  attempt_limit integer NOT NULL DEFAULT 3 CHECK(attempt_limit BETWEEN 1 AND 3),
  policy_sha256 text CHECK(policy_sha256 ~ '^[0-9a-f]{64}$'),
  CHECK (NOT enabled OR policy_sha256 IS NOT NULL)
);
INSERT INTO rc_control.settings(singleton) VALUES(true);
CREATE TABLE rc_control.workers (
  worker_id uuid PRIMARY KEY,
  scope_id text NOT NULL CHECK(scope_id ~ '^[a-z][a-z0-9-]{0,31}$'),
  active boolean NOT NULL DEFAULT false
);
CREATE TABLE rc_control.jobs (
  job_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL,
  scope_id text NOT NULL,
  idempotency_key text NOT NULL CHECK(idempotency_key ~ '^[A-Za-z0-9_-]{1,64}$'),
  descriptor jsonb NOT NULL CHECK(jsonb_typeof(descriptor)='object'),
  deadline_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  available_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  state text NOT NULL DEFAULT 'QUEUED'
    CHECK(state IN ('QUEUED','LEASED','RUNNING','CANCELLED','EXPIRED','FAILED')),
  fence bigint NOT NULL DEFAULT 0 CHECK(fence >= 0),
  attempt_count integer NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
  attempt_limit integer NOT NULL CHECK(attempt_limit BETWEEN 1 AND 3),
  attempt_id uuid,
  worker_id uuid REFERENCES rc_control.workers,
  lease_until timestamptz,
  UNIQUE(owner_id,idempotency_key),
  CHECK(attempt_count <= attempt_limit),
  CHECK((state IN ('LEASED','RUNNING') AND attempt_id IS NOT NULL
          AND worker_id IS NOT NULL AND lease_until IS NOT NULL)
     OR (state NOT IN ('LEASED','RUNNING') AND attempt_id IS NULL
          AND worker_id IS NULL AND lease_until IS NULL)),
  CHECK(lease_until IS NULL OR lease_until <= deadline_at)
);
CREATE INDEX jobs_ready ON rc_control.jobs(scope_id,created_at,job_id) WHERE state='QUEUED';
CREATE INDEX jobs_leases ON rc_control.jobs(lease_until) WHERE state IN ('LEASED','RUNNING');
CREATE TABLE rc_control.attempts (
  attempt_id uuid PRIMARY KEY,
  job_id uuid NOT NULL REFERENCES rc_control.jobs,
  worker_id uuid NOT NULL REFERENCES rc_control.workers,
  fence bigint NOT NULL,
  number integer NOT NULL,
  state text NOT NULL CHECK(state IN ('LEASED','RUNNING','EXPIRED','CANCELLED','FAILED')),
  lease_until timestamptz NOT NULL,
  finished_at timestamptz,
  reason text CHECK(reason IN ('LEASE_EXPIRED','DEADLINE','CANCELLED','WORKER_REVOKED',
                              'WORKER_STOPPED','ENGINE_FAILURE','RESOURCE_LIMIT')),
  UNIQUE(job_id,fence), UNIQUE(job_id,number)
);
ALTER TABLE rc_control.settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE rc_control.settings FORCE ROW LEVEL SECURITY;
CREATE POLICY owner_only ON rc_control.settings TO rc_control_owner USING(true) WITH CHECK(true);
ALTER TABLE rc_control.workers ENABLE ROW LEVEL SECURITY;
ALTER TABLE rc_control.workers FORCE ROW LEVEL SECURITY;
CREATE POLICY owner_only ON rc_control.workers TO rc_control_owner USING(true) WITH CHECK(true);
ALTER TABLE rc_control.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE rc_control.jobs FORCE ROW LEVEL SECURITY;
CREATE POLICY owner_only ON rc_control.jobs TO rc_control_owner USING(true) WITH CHECK(true);
ALTER TABLE rc_control.attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE rc_control.attempts FORCE ROW LEVEL SECURITY;
CREATE POLICY owner_only ON rc_control.attempts TO rc_control_owner USING(true) WITH CHECK(true);

-- Internal descriptor, already admitted by the domain service. Not raw user JSON.
CREATE FUNCTION rc_control.enqueue(p_owner uuid, p_scope text, p_key text,
                                   p_descriptor jsonb, p_deadline timestamptz)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE cfg rc_control.settings; j rc_control.jobs; k text; t timestamptz;
BEGIN
  SELECT * INTO STRICT cfg FROM rc_control.settings WHERE singleton FOR UPDATE;
  IF NOT cfg.enabled THEN RAISE EXCEPTION 'EXECUTION_DISABLED'; END IF;
  IF p_owner IS NULL OR p_scope IS NULL OR p_scope !~ '^[a-z][a-z0-9-]{0,31}$'
     OR p_key IS NULL OR p_key !~ '^[A-Za-z0-9_-]{1,64}$'
     OR jsonb_typeof(p_descriptor) IS DISTINCT FROM 'object'
     OR octet_length(p_descriptor::text) > 4096 THEN
    RAISE EXCEPTION 'INPUT_INVALID';
  END IF;
  IF NOT (p_descriptor ?& ARRAY['version_id','source_sha256','program_sha256',
       'java_sha256','policy_sha256','engine_ref','rounds'])
     OR p_descriptor - ARRAY['version_id','source_sha256','program_sha256',
       'java_sha256','policy_sha256','engine_ref','rounds'] <> '{}'::jsonb THEN
    RAISE EXCEPTION 'DESCRIPTOR_INVALID';
  END IF;
  FOREACH k IN ARRAY ARRAY['source_sha256','program_sha256','java_sha256','policy_sha256'] LOOP
    IF jsonb_typeof(p_descriptor->k) IS DISTINCT FROM 'string'
       OR (p_descriptor->>k) !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'DESCRIPTOR_INVALID'; END IF;
  END LOOP;
  IF jsonb_typeof(p_descriptor->'version_id') IS DISTINCT FROM 'string'
     OR (p_descriptor->>'version_id') !~ '^[A-Za-z0-9_-]{1,64}$'
     OR (p_descriptor->>'engine_ref') IS DISTINCT FROM 'tank-royale/1.4.0'
     OR jsonb_typeof(p_descriptor->'rounds') IS DISTINCT FROM 'number'
     OR (p_descriptor->>'rounds') !~ '^[1-3]$'
     OR (p_descriptor->>'policy_sha256') IS DISTINCT FROM cfg.policy_sha256 THEN
    RAISE EXCEPTION 'DESCRIPTOR_INVALID';
  END IF;
  SELECT * INTO j FROM rc_control.jobs WHERE owner_id=p_owner AND idempotency_key=p_key;
  IF FOUND THEN
    IF j.scope_id<>p_scope OR j.descriptor<>p_descriptor OR j.deadline_at IS DISTINCT FROM p_deadline THEN
      RAISE EXCEPTION 'IDEMPOTENCY_CONFLICT';
    END IF;
    RETURN jsonb_build_object('job_id',j.job_id,'state',j.state,'duplicate',true);
  END IF;
  t := clock_timestamp();
  IF p_deadline IS NULL OR p_deadline <= t OR p_deadline > t + interval '240 seconds' THEN
    RAISE EXCEPTION 'DEADLINE_INVALID';
  END IF;
  IF (SELECT count(*) FROM rc_control.jobs WHERE state IN ('QUEUED','LEASED','RUNNING')) >= cfg.capacity THEN
    RAISE EXCEPTION 'QUEUE_FULL';
  END IF;
  INSERT INTO rc_control.jobs(owner_id,scope_id,idempotency_key,descriptor,deadline_at,attempt_limit)
    VALUES(p_owner,p_scope,p_key,p_descriptor,p_deadline,cfg.attempt_limit) RETURNING * INTO j;
  RETURN jsonb_build_object('job_id',j.job_id,'state',j.state,'duplicate',false);
END $$;

-- Reap bounded batches; no retry after deadline or beyond attempt_limit.
CREATE FUNCTION rc_control.reap() RETURNS integer LANGUAGE plpgsql
SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE j rc_control.jobs; t timestamptz; n integer:=0; reason text; next_state text;
BEGIN
  FOR j IN SELECT q.* FROM rc_control.jobs q
    WHERE q.state IN ('QUEUED','LEASED','RUNNING') AND
      (q.deadline_at<=clock_timestamp() OR q.lease_until<=clock_timestamp()
       OR (q.worker_id IS NOT NULL AND NOT EXISTS
           (SELECT 1 FROM rc_control.workers w WHERE w.worker_id=q.worker_id AND w.active)))
    ORDER BY q.created_at,q.job_id LIMIT 256 FOR UPDATE OF q SKIP LOCKED
  LOOP
    t:=clock_timestamp();
    reason:=CASE WHEN j.deadline_at<=t THEN 'DEADLINE'
                 WHEN NOT EXISTS(SELECT 1 FROM rc_control.workers w WHERE w.worker_id=j.worker_id AND w.active)
                      AND j.worker_id IS NOT NULL THEN 'WORKER_REVOKED' ELSE 'LEASE_EXPIRED' END;
    next_state:=CASE WHEN j.deadline_at<=t THEN 'EXPIRED'
                    WHEN j.attempt_count>=j.attempt_limit THEN 'FAILED' ELSE 'QUEUED' END;
    UPDATE rc_control.attempts SET state='EXPIRED',finished_at=t,reason=reap.reason
      WHERE attempt_id=j.attempt_id AND state IN ('LEASED','RUNNING');
    UPDATE rc_control.jobs SET state=next_state,fence=fence+1,attempt_id=NULL,
      worker_id=NULL,lease_until=NULL,available_at=t WHERE job_id=j.job_id;
    n:=n+1;
  END LOOP;
  RETURN n;
END $$;

CREATE FUNCTION rc_control.claim(p_worker uuid) RETURNS jsonb LANGUAGE plpgsql
SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE cfg rc_control.settings; w rc_control.workers; j rc_control.jobs; t timestamptz;
BEGIN
  SELECT * INTO STRICT cfg FROM rc_control.settings WHERE singleton FOR SHARE;
  IF NOT cfg.enabled THEN RAISE EXCEPTION 'EXECUTION_DISABLED'; END IF;
  SELECT * INTO w FROM rc_control.workers WHERE worker_id=p_worker AND active FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION 'WORKER_DENIED'; END IF;
  SELECT * INTO j FROM rc_control.jobs
    WHERE scope_id=w.scope_id AND state='QUEUED' AND deadline_at>clock_timestamp()
      AND available_at<=clock_timestamp() AND attempt_count<attempt_limit
      AND descriptor->>'policy_sha256'=cfg.policy_sha256
    ORDER BY created_at,job_id LIMIT 1 FOR UPDATE SKIP LOCKED;
  IF NOT FOUND THEN RETURN NULL; END IF;
  t:=clock_timestamp();
  IF j.deadline_at<=t THEN RETURN NULL; END IF;
  UPDATE rc_control.jobs SET state='LEASED',worker_id=p_worker,attempt_id=gen_random_uuid(),
    fence=fence+1,attempt_count=attempt_count+1,
    lease_until=least(deadline_at,t+make_interval(secs=>cfg.lease_seconds))
    WHERE job_id=j.job_id RETURNING * INTO j;
  INSERT INTO rc_control.attempts(attempt_id,job_id,worker_id,fence,number,state,lease_until)
    VALUES(j.attempt_id,j.job_id,p_worker,j.fence,j.attempt_count,'LEASED',j.lease_until);
  RETURN jsonb_build_object('job_id',j.job_id,'attempt_id',j.attempt_id,'fence',j.fence,
    'lease_until',j.lease_until,'deadline_at',j.deadline_at,'descriptor',j.descriptor);
END $$;

-- No EXECUTE grant for this internal helper. Lock worker before job everywhere.
CREATE FUNCTION rc_control.lock_lease(p_worker uuid,p_job uuid,p_attempt uuid,p_fence bigint)
RETURNS rc_control.jobs LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE j rc_control.jobs;
BEGIN
  PERFORM 1 FROM rc_control.workers WHERE worker_id=p_worker AND active FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION 'WORKER_DENIED'; END IF;
  SELECT * INTO j FROM rc_control.jobs WHERE job_id=p_job FOR UPDATE;
  IF NOT FOUND OR j.worker_id IS DISTINCT FROM p_worker OR j.attempt_id IS DISTINCT FROM p_attempt
     OR j.fence IS DISTINCT FROM p_fence OR j.state NOT IN ('LEASED','RUNNING')
     OR j.lease_until<=clock_timestamp() OR j.deadline_at<=clock_timestamp() THEN
    RAISE EXCEPTION 'STALE_LEASE';
  END IF;
  RETURN j;
END $$;

CREATE FUNCTION rc_control.heartbeat(p_worker uuid,p_job uuid,p_attempt uuid,p_fence bigint,p_start boolean DEFAULT false)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE cfg rc_control.settings; j rc_control.jobs; until_at timestamptz;
BEGIN
  SELECT * INTO STRICT cfg FROM rc_control.settings WHERE singleton FOR SHARE;
  IF NOT cfg.enabled THEN RAISE EXCEPTION 'EXECUTION_DISABLED'; END IF;
  IF p_start IS NULL THEN RAISE EXCEPTION 'INPUT_INVALID'; END IF;
  j:=rc_control.lock_lease(p_worker,p_job,p_attempt,p_fence);
  until_at:=least(j.deadline_at,greatest(j.lease_until,clock_timestamp()+make_interval(secs=>cfg.lease_seconds)));
  UPDATE rc_control.jobs SET lease_until=until_at,
    state=CASE WHEN p_start THEN 'RUNNING' ELSE state END WHERE job_id=p_job RETURNING * INTO j;
  UPDATE rc_control.attempts SET lease_until=until_at,state=j.state WHERE attempt_id=p_attempt;
  RETURN jsonb_build_object('state',j.state,'fence',j.fence,'lease_until',until_at);
END $$;

CREATE FUNCTION rc_control.fail_attempt(p_worker uuid,p_job uuid,p_attempt uuid,p_fence bigint,p_reason text)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE j rc_control.jobs; next_state text; t timestamptz;
BEGIN
  IF p_reason IS NULL OR p_reason NOT IN ('WORKER_STOPPED','ENGINE_FAILURE','RESOURCE_LIMIT') THEN
    RAISE EXCEPTION 'REASON_INVALID';
  END IF;
  j:=rc_control.lock_lease(p_worker,p_job,p_attempt,p_fence);
  t:=clock_timestamp();
  next_state:=CASE WHEN j.deadline_at<=t THEN 'EXPIRED' WHEN j.attempt_count>=j.attempt_limit THEN 'FAILED' ELSE 'QUEUED' END;
  UPDATE rc_control.attempts SET state='FAILED',finished_at=t,reason=p_reason WHERE attempt_id=p_attempt;
  UPDATE rc_control.jobs SET state=next_state,fence=fence+1,attempt_id=NULL,worker_id=NULL,
    lease_until=NULL,available_at=t+interval '1 second' WHERE job_id=p_job;
  RETURN next_state;
END $$;

CREATE FUNCTION rc_control.cancel(p_job uuid,p_owner uuid) RETURNS text LANGUAGE plpgsql
SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE j rc_control.jobs;
BEGIN
  SELECT * INTO j FROM rc_control.jobs WHERE job_id=p_job AND owner_id=p_owner FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'JOB_NOT_OWNED'; END IF;
  IF j.state IN ('CANCELLED','EXPIRED','FAILED') THEN RETURN j.state; END IF;
  UPDATE rc_control.attempts SET state='CANCELLED',reason='CANCELLED',finished_at=clock_timestamp()
    WHERE attempt_id=j.attempt_id;
  UPDATE rc_control.jobs SET state='CANCELLED',fence=fence+1,
    worker_id=NULL,attempt_id=NULL,lease_until=NULL WHERE job_id=p_job;
  RETURN 'CANCELLED';
END $$;

REVOKE ALL ON ALL TABLES IN SCHEMA rc_control FROM PUBLIC,rc_broker;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA rc_control FROM PUBLIC,rc_broker;
GRANT USAGE ON SCHEMA rc_control TO rc_broker;
GRANT EXECUTE ON FUNCTION rc_control.enqueue(uuid,text,text,jsonb,timestamptz),
  rc_control.claim(uuid),rc_control.reap(),
  rc_control.heartbeat(uuid,uuid,uuid,bigint,boolean),
  rc_control.fail_attempt(uuid,uuid,uuid,bigint,text),
  rc_control.cancel(uuid,uuid) TO rc_broker;
COMMIT;
