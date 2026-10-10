/** I3-03C private service boundary. No student auth, no code execution. */
export const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const TOKEN = /^Bearer (rcw_[0-9a-f]{64})$/;
const OPS = new Set(['claim', 'start', 'heartbeat', 'fail']);
const REASONS = new Set(['WORKER_STOPPED', 'ENGINE_FAILURE', 'RESOURCE_LIMIT']);
const MAX = 2048;
const headers = {'content-type':'application/json','cache-control':'no-store','x-content-type-options':'nosniff'};
const error = (code,status) => new Response(JSON.stringify({error:code}),{status,headers});

// Flat JSON only. Recognize tokens, not regex-rewriting JSON; reject duplicate
// keys after decoding escapes, nested values, nonfinite numbers and trailing data.
export function parseCommand(text) {
  let i=0; const value=Object.create(null); const seen=new Set();
  const ws=()=>{while(/[\x20\t\r\n]/.test(text[i]??'!'))i++;};
  const string=()=>{const start=i++; while(i<text.length){
    if(text[i]==='\\'){i+=2;continue;} if(text[i++]==='"')return JSON.parse(text.slice(start,i));
  } throw Error('COMMAND_INVALID');};
  ws(); if(text[i++]!=='{')throw Error('COMMAND_INVALID'); ws();
  while(text[i]!=='}'){
    if(text[i]!=='"')throw Error('COMMAND_INVALID');const key=string(); ws();
    if(seen.has(key)||text[i++]!==':')throw Error('COMMAND_INVALID'); seen.add(key);ws();
    if(text[i]==='"') value[key]=string();
    else {const start=i;while(i<text.length&&!['}',','].includes(text[i]))i++;
      const raw=text.slice(start,i).trim();if(raw!=='1')throw Error('COMMAND_INVALID');value[key]=1;}
    ws();if(text[i]===','){i++;ws();if(text[i]==='}')throw Error('COMMAND_INVALID');continue;}
    if(text[i]!=='}')throw Error('COMMAND_INVALID');
  }
  i++;ws();if(i!==text.length)throw Error('COMMAND_INVALID');
  if(value.schema_version!==1||typeof value.request_id!=='string'||!UUID.test(value.request_id)||!OPS.has(value.operation))throw Error('COMMAND_INVALID');
  const expected=['schema_version','request_id','operation'];const args={};
  if(value.operation!=='claim'){
    expected.push('job_id','attempt_id','fence');
    if(typeof value.job_id!=='string'||!UUID.test(value.job_id)||typeof value.attempt_id!=='string'||!UUID.test(value.attempt_id)
      ||typeof value.fence!=='string'||!/^[1-9][0-9]{0,18}$/.test(value.fence)||BigInt(value.fence)>9223372036854775807n)throw Error('COMMAND_INVALID');
    Object.assign(args,{job_id:value.job_id,attempt_id:value.attempt_id,fence:value.fence});
    if(value.operation==='fail'){expected.push('reason');if(!REASONS.has(value.reason))throw Error('COMMAND_INVALID');args.reason=value.reason;}
  }
  if(Object.keys(value).length!==expected.length||expected.some(k=>!seen.has(k)))throw Error('COMMAND_INVALID');
  return {requestId:value.request_id,operation:value.operation,args};
}

async function boundedBody(req) {
  if(!req.body)throw Error('COMMAND_INVALID');const reader=req.body.getReader();let bytes=0;const chunks=[];
  let timer;const timeout=new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('BODY_TIMEOUT')),2000);});
  try {while(true){const {value,done}=await Promise.race([reader.read(),timeout]);if(done)break;
    bytes+=value.length;if(bytes>MAX)throw Error('BODY_TOO_LARGE');chunks.push(value);}
    const data=new Uint8Array(bytes);let at=0;for(const b of chunks){data.set(b,at);at+=b.length;}
    return new TextDecoder('utf-8',{fatal:true}).decode(data);
  } finally {clearTimeout(timer);reader.cancel().catch(()=>{});reader.releaseLock();}
}
const statusFor = new Map([
 ['CREDENTIAL_DENIED',401],['COMMAND_INVALID',400],['REQUEST_CONFLICT',409],['REQUEST_EXPIRED',409],
 ['STALE_LEASE',409],['WORKER_DENIED',401],['WORKER_BUSY',409],['RATE_LIMITED',429],['RECEIPT_LIMIT',429],['EXECUTION_DISABLED',503],
]);
export function createWorkerHandler({dispatch,enabled=false,path='/worker-control'}) {
  if(typeof dispatch!=='function'||typeof enabled!=='boolean'||!['/worker-control','/functions/v1/worker-control'].includes(path))throw Error('CONFIG_INVALID');
  return async (req)=>{
    if(!enabled)return error('EXECUTION_DISABLED',503);
    const url=new URL(req.url);
    if(url.protocol!=='https:'||url.pathname!==path||url.search||req.method!=='POST')return error('REQUEST_DENIED',403);
    if(req.headers.has('origin')||req.headers.has('cookie')||req.headers.has('content-encoding')||req.headers.has('transfer-encoding'))return error('REQUEST_DENIED',403);
    const match=TOKEN.exec(req.headers.get('authorization')??'');if(!match)return error('CREDENTIAL_DENIED',401);
    const type=req.headers.get('content-type');if(!['application/json','application/json; charset=utf-8'].includes(type))return error('COMMAND_INVALID',400);
    const len=req.headers.get('content-length');if(len!==null&&(!/^[0-9]{1,5}$/.test(len)||Number(len)>MAX))return error('COMMAND_INVALID',400);
    let command;
    try{command=parseCommand(await boundedBody(req));}catch{return error('COMMAND_INVALID',400);}
    const hash=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(match[1])));
    const digest=Array.from(hash,b=>b.toString(16).padStart(2,'0')).join('');
    try{
      const result=await dispatch(digest,command); // resolves only AFTER transaction commit
      if(!result||result.request_id!==command.requestId||result.operation!==command.operation||result.schema_version!==1)throw Error('RESPONSE_INVALID');
      const encoded=JSON.stringify(result);if(encoded.length>8192)throw Error('RESPONSE_INVALID');
      return new Response(encoded,{status:200,headers});
    }catch(e){const message=e instanceof Error?e.message:'';return statusFor.has(message)?error(message,statusFor.get(message)):error('STORAGE_UNAVAILABLE',503);}
  };
}
