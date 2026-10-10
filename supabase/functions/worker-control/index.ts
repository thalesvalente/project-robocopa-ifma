// Deployment candidate, OFF by default. Does NOT deploy itself.
import postgres from 'npm:postgres@3.4.7';
import {createDispatch} from './database.mjs';
import {createWorkerHandler} from './handler.mjs';

const enabled=Deno.env.get('RC_WORKER_API_ENABLED')==='true';
let handler: (req: Request)=>Promise<Response>;
if(!enabled){handler=createWorkerHandler({dispatch:async()=>{throw Error('EXECUTION_DISABLED');}});}
else {
  const url=Deno.env.get('RC_WORKER_DATABASE_URL');
  const ca=Deno.env.get('RC_WORKER_DATABASE_CA');
  if(!url||!ca)throw Error('WORKER_API_CONFIG_INVALID');
  const parsed=new URL(url);
  // Never default to platform's all-powerful SUPABASE_DB_URL/service_role.
  if(!['postgres:','postgresql:'].includes(parsed.protocol)||parsed.search||!/^rc_worker_api_login(?:\.[a-z0-9]+)?$/.test(decodeURIComponent(parsed.username)))throw Error('WORKER_API_CONFIG_INVALID');
  const sql=postgres(url,{ssl:{rejectUnauthorized:true,ca},prepare:false,max:1,connect_timeout:3,idle_timeout:10,max_lifetime:60,onnotice:()=>{}});
  handler=createWorkerHandler({dispatch:createDispatch(sql),enabled:true,path:'/functions/v1/worker-control'});
}
Deno.serve(handler);
