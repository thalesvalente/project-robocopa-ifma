// REAL HTTPS fixture. Never invoke outside the disposable CI harness.
import postgres from 'npm:postgres@3.4.7';
import {createWorkerHandler} from '../../supabase/functions/worker-control/handler.mjs';
import {createDispatch} from '../../supabase/functions/worker-control/database.mjs';
if(Deno.env.get('GITHUB_ACTIONS')!=='true'||Deno.env.get('RUNNER_ENVIRONMENT')!=='github-hosted'||Deno.build.os!=='linux')throw Error('DISPOSABLE_CI_REQUIRED');
const config=JSON.parse(await Deno.readTextFile(Deno.args[0]));
const sql=postgres({host:config.socket,database:'robocopa_i3_ci',username:'rc_worker_api_ci',password:config.password,ssl:false,prepare:false,max:2,connect_timeout:3,idle_timeout:2,max_lifetime:20,onnotice:()=>{}});
const [who]=await sql`SELECT current_user AS who`;
if(who.who!=='rc_worker_api_ci')throw Error('WRONG_DB_IDENTITY');
const handler=createWorkerHandler({dispatch:createDispatch(sql),enabled:config.enabled===true});
const server=Deno.serve({hostname:'127.0.0.1',port:0,cert:await Deno.readTextFile(config.cert),key:await Deno.readTextFile(config.key),onListen:({port})=>Deno.writeTextFileSync(config.portFile,JSON.stringify({port})),onError:()=>new Response('unavailable',{status:503})},handler);
for(const sig of ['SIGINT','SIGTERM'])Deno.addSignalListener(sig,()=>{server.shutdown().finally(()=>sql.end({timeout:1}));});
await server.finished;
