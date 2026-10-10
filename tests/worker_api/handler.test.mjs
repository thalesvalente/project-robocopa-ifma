import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createWorkerHandler,parseCommand} from '../../supabase/functions/worker-control/handler.mjs';
import {createDispatch} from '../../supabase/functions/worker-control/database.mjs';
const id='00000000-0000-4000-8000-000000000001';
const token='rcw_'+'a'.repeat(64);
const body={schema_version:1,request_id:id,operation:'claim'};
const response={...body,worker_id:id,scope_id:'lab-a',result:null};
function req(data=JSON.stringify(body),overrides={}){
 return new Request('https://control.example.invalid/worker-control',{
  method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:data,...overrides});
}
test('default disabled calls no database',async()=>{
 const h=createWorkerHandler({dispatch:()=>{assert.fail('DB called');}});assert.equal((await h(req())).status,503);
});
test('valid request forwards digest only, never raw token',async()=>{
 let seen;const h=createWorkerHandler({enabled:true,dispatch:async(...args)=>{seen=args;return response;}});
 const r=await h(req());assert.equal(r.status,200);assert.deepEqual(await r.json(),response);
 assert.match(seen[0],/^[0-9a-f]{64}$/);assert.notEqual(seen[0],token);assert.equal(seen[1].requestId,id);
 assert.equal(r.headers.get('cache-control'),'no-store');assert.equal(r.headers.get('access-control-allow-origin'),null);
});
test('missing or invalid credentials refuse before database',async()=>{
 for(const auth of [null,'Bearer '+('x'.repeat(64)),'Bearer sb_secret_key','Bearer '+token+',evil']){
  const h=createWorkerHandler({enabled:true,dispatch:()=>assert.fail('DB')});const r=req();if(auth===null)r.headers.delete('authorization');else r.headers.set('authorization',auth);
  assert.equal((await h(r)).status,401);
 }
});
test('only HTTPS POST exact path, no query',async()=>{
 for(const [url,method] of [['http://control.example.invalid/worker-control','POST'],['https://control.example.invalid/wrong','POST'],['https://control.example.invalid/worker-control?q=x','POST'],['https://control.example.invalid/worker-control','GET']]){
  const h=createWorkerHandler({enabled:true,dispatch:()=>assert.fail('DB')});assert.equal((await h(new Request(url,{method}))).status,403);
 }
});
test('origin cookie encoding refused',async()=>{
 for(const key of ['origin','cookie','content-encoding','transfer-encoding']){
  const r=req();r.headers.set(key,'untrusted');assert.equal((await createWorkerHandler({enabled:true,dispatch:()=>assert.fail('DB')})(r)).status,403);
 }
});
test('malformed, duplicate escaped keys, fields, nesting and unsafe integers',async()=>{
 const invalid=['','null','[]','{}','{"schema_version":1,}',JSON.stringify({...body,owner_id:id}),JSON.stringify({...body,operation:'complete'}),
  '{"schema_version":1,"request_id":"'+id+'","operation":"claim","operat\\u0069on":"claim"}',
  JSON.stringify({...body,schema_version:true}),JSON.stringify({...body,operation:{x:1}}),
  JSON.stringify({...body,operation:'start',job_id:id,attempt_id:id,fence:1}),
  JSON.stringify({...body,operation:'start',job_id:id,attempt_id:id,fence:'9223372036854775808'}),
  JSON.stringify({...body,operation:'claim',constructor:'evil'}),'{"schema_version":NaN}',JSON.stringify(body)+'junk'];
 const h=createWorkerHandler({enabled:true,dispatch:()=>assert.fail('DB')});for(const text of invalid)assert.equal((await h(req(text))).status,400,text);
});
test('valid start heartbeat fail parse exact fields',()=>{
 for(const operation of ['start','heartbeat','fail']){
  const b={...body,operation,job_id:id,attempt_id:id,fence:'9223372036854775807'};
  if(operation==='fail')b.reason='ENGINE_FAILURE';const p=parseCommand(JSON.stringify(b));assert.equal(p.operation,operation);assert.equal(p.args.fence,b.fence);
 }
});
test('body size enforced independent of content length',async()=>{
 const h=createWorkerHandler({enabled:true,dispatch:()=>assert.fail('DB')});assert.equal((await h(req(' '.repeat(2049)))).status,400);
 const r=req();r.headers.set('content-length','9000');assert.equal((await h(r)).status,400);
});
test('slow body deadline fails closed',async()=>{
 const stream=new ReadableStream({start(c){c.enqueue(new TextEncoder().encode('{'));}});
 const h=createWorkerHandler({enabled:true,dispatch:()=>assert.fail('DB')});const r=req(stream,{duplex:'half'});
 assert.equal((await h(r)).status,400);
});
test('mapped errors sanitized and unexpected SQL diagnostics hidden',async()=>{
 for(const [message,status] of [['CREDENTIAL_DENIED',401],['REQUEST_CONFLICT',409],['RATE_LIMITED',429],['dsn password=private',503]]){
  const h=createWorkerHandler({enabled:true,dispatch:async()=>{throw Error(message);}});const r=await h(req());assert.equal(r.status,status);assert.ok(!(await r.text()).includes('password'));
 }
});
test('wrong request correlation does not return success',async()=>{
 const h=createWorkerHandler({enabled:true,dispatch:async()=>({...response,request_id:'other'})});assert.equal((await h(req())).status,503);
});
test('database parameters are separated and commit failure does not succeed',async()=>{
 const parameters=[];let callbacks=0;
 const tx=async(strings,...params)=>{parameters.push(params);return params.length?[{response}]:[];};tx.json=v=>v;
 const sql={begin:async cb=>{callbacks++;await cb(tx);throw Error('commit failed');}};
 await assert.rejects(createDispatch(sql)('a'.repeat(64),{requestId:id,operation:'claim',args:{}}),/commit failed/);
 assert.equal(callbacks,1);assert.equal(parameters.at(-1)[0],'a'.repeat(64));assert.equal(parameters.at(-1)[1],id);
});
