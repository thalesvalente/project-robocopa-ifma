'use strict';
const $ = id => document.getElementById(id);
const code = $('codigo');
let config, frames = [], position = 0, timer = null, loading = false;
const key = 'robocopa-lab-draft-v1';
function message(text, error = false) { $('status').textContent = text; $('status').classList.toggle('error', error); }
function store() { try { localStorage.setItem(key, code.value); return true; } catch { return false; } }
async function api(path, source) {
  const response = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json','X-Robocopa-CSRF':config.csrf}, body:JSON.stringify({source})});
  const data = await response.json();
  if (!response.ok) { const e = new Error(data.error || 'Falha na requisição.'); e.line=data.line; throw e; }
  return data;
}
function highlight(line) {
  if (!line) return;
  const parts = code.value.split('\n'), start = parts.slice(0, line-1).join('\n').length + (line>1 ? 1 : 0);
  code.focus(); code.setSelectionRange(start, start + (parts[line-1] || '').length);
}
function busy(value) { loading=value; for (const id of ['train','validate','sentinela','explorador']) $(id).disabled=value; }
function stop() { clearInterval(timer); timer=null; $('play').textContent='Reproduzir replay'; }
function draw(frame) {
  const canvas=$('arena'), ctx=canvas.getContext('2d');
  ctx.fillStyle='#07101b';ctx.fillRect(0,0,800,600);
  ctx.strokeStyle='#162d3d';ctx.lineWidth=1;
  for(let x=0;x<=800;x+=50){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,600);ctx.stroke();}
  for(let y=0;y<=600;y+=50){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(800,y);ctx.stroke();}
  if(!frame)return;
  for(const bot of frame.bots){
    ctx.save();ctx.translate(bot.x,600-bot.y);ctx.rotate(-bot.direction*Math.PI/180);
    ctx.fillStyle=bot.name==='Aprendiz'?'#a6efad':'#f8d37b';ctx.fillRect(-13,-10,26,20);ctx.fillRect(0,-3,23,6);ctx.restore();
    ctx.fillStyle='#f2f6f8';ctx.font='13px system-ui';ctx.fillText(bot.name,Math.max(4,Math.min(720,bot.x-20)),Math.max(14,600-bot.y-20));
  }
  $('frame-label').textContent=`Round ${frame.round} · turno ${frame.turn} · amostra ${position+1}/${frames.length}`;
}
function result(data) {
  stop(); frames=data.replay.frames; position=0; $('empty').hidden=true; $('empty').style.display='none';
  $('play').disabled=!frames.length;draw(frames[0]);
  const out=$('result');out.replaceChildren();const heading=document.createElement('h3');heading.textContent='Resultado do motor · 3 rounds';out.append(heading);
  for(const row of data.results.results){const div=document.createElement('div');div.className='score';const name=document.createElement('span');name.textContent=`${row.rank}º · ${row.name}`;const score=document.createElement('strong');score.textContent=`${row.totalScore} pontos`;div.append(name,score);out.append(div);}
  const metric=document.createElement('p');metric.className='metric';metric.textContent=`Aprendiz: velocidade média absoluta ${data.replay.mean_abs_speed.toFixed(2)} · em movimento em ${(100*data.replay.moving_tick_fraction).toFixed(1)}% dos turnos observados.`;out.append(metric);
  const fingerprint=document.createElement('p');fingerprint.className='hash';fingerprint.textContent=`Versão do programa: ${data.results.program_sha256.slice(0,12)} · execução ${data.run_id}`;out.append(fingerprint);
}
$('save').addEventListener('click',()=>{const saved=store();message(saved?'Rascunho salvo neste navegador. Não é uma inscrição em competição.':'O navegador não permitiu salvar. Copie o código antes de fechar.', !saved);});
code.addEventListener('input',()=>{store();message('Rascunho alterado. Verifique e teste a nova versão.');});
for(const button of document.querySelectorAll('[data-insert]'))button.addEventListener('click',()=>{const snippet=button.dataset.insert.replaceAll('\\n','\n');code.setRangeText(snippet,code.selectionStart,code.selectionEnd,'end');code.focus();store();message('Instrução inserida. Confira o bloco e verifique o código.');});
for(const name of ['sentinela','explorador'])$(name).addEventListener('click',()=>{
  if(code.value.trim() && !Object.values(config.examples).includes(code.value) && !confirm('Substituir o rascunho atual pelo exemplo?'))return;
  code.value=config.examples[name];store();message(`Exemplo ${name} carregado. Você pode editar qualquer instrução.`);
});
$('validate').addEventListener('click',async()=>{busy(true);try{const data=await api('/api/validate',code.value);message(`Código válido: ${data.instructions} instruções/condições · versão ${data.program_sha256.slice(0,12)}.`);}catch(e){message(e.message,true);highlight(e.line);}finally{busy(false);}});
$('train').addEventListener('click',async()=>{
  const source=code.value;store();busy(true);message('Executando uma batalha real no servidor local. O código continua salvo.');
  try{const data=await api('/api/train',source);result(data);message(code.value===source?'Batalha concluída. Compare o replay e altere sua estratégia.':'Batalha concluída para a versão anterior. Suas novas edições não foram perdidas.');}
  catch(e){message(e.message,true);highlight(e.line);}finally{busy(false);}
});
$('play').addEventListener('click',()=>{if(timer){stop();return;}if(position>=frames.length-1)position=0;$('play').textContent='Pausar replay';timer=setInterval(()=>{draw(frames[position]);if(position>=frames.length-1)stop();else position++;},75);});
(async()=>{busy(true);try{const response=await fetch('/api/config');if(!response.ok)throw new Error('Falha ao conectar.');config=await response.json();let draft;try{draft=localStorage.getItem(key);}catch{}code.value=draft && draft.length<=8192?draft:config.examples.explorador;message('Laboratório pronto. Escolha um exemplo ou edite a estratégia.');busy(false);draw();}catch{message('Não foi possível conectar ao laboratório. Inicie o servidor Python e recarregue.',true);}})();
