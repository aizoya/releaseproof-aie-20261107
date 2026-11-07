'use strict';
const $ = id => document.getElementById(id);
let examples = {}, current = null;
let revision = 0;
let capabilities = {acceptance_enabled:false};
const money = cents => typeof cents === 'number' ? '$' + (cents / 100).toFixed(2) : String(cents);
function invalidate() { revision++; current = null; $('accept').hidden = true; $('download').hidden=true; $('result').hidden=true; $('accepted').textContent = ''; }
async function post(path, body) {
  const response = await fetch(path, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed.');
  return data;
}
$('source').addEventListener('input', invalidate);
$('example').addEventListener('change', () => { $('source').value = examples[$('example').value]; invalidate(); $('result').hidden=true; });
$('verify').addEventListener('click', async () => {
  invalidate(); $('verify').disabled=true;
  const source = $('source').value;
  const requestRevision = revision;
  try {
    const data = await post('/api/verify', {source});
    if (revision !== requestRevision || $('source').value !== source) return;
    current = data;
    $('result').hidden=false;
    $('verdict').textContent = {pass:'Checks passed',fail:'Repair blocked',inconclusive:'Verification inconclusive'}[data.status];
    $('verdict').className=data.status;
    $('gate').textContent=data.gate.toUpperCase();
    $('reason').textContent=data.reason;
    $('summary').textContent=`${data.checks.filter(x=>x.passed).length}/${data.checks_run} checks passed · ${data.duration_ms} ms · ${data.provider_calls} model calls`;
    $('checks').replaceChildren();
    for (const check of data.checks.slice(0,8)) {
      const row=document.createElement('div'); row.className='check';
      const icon=document.createElement('span'); icon.textContent=check.passed?'✓':'×'; icon.className=check.passed?'pass':'fail';
      const text=document.createElement('div'); text.textContent=check.name;
      const detail=document.createElement('small');
      detail.textContent=`Expected ${money(check.expected_cents)} · quote ${money(check.quote_cents)} · receipt ${money(check.receipt_cents)}`;
      text.append(detail); row.append(icon,text); $('checks').append(row);
    }
    if(data.checks.length>8){
      const extra=document.createElement('p');
      extra.className='muted';
      extra.textContent=`${data.checks.slice(8).filter(c=>c.passed).length}/32 fresh challenge cases passed. All inputs and outputs are in the evidence below.`;
      $('checks').append(extra);
    }
    $('evidence').textContent=JSON.stringify(data,null,2);
    $('accept').hidden=data.status!=='pass'||!current||capabilities.acceptance_enabled!==true||data.acceptance_enabled===false;
    $('download').hidden=!current;
    $('result').scrollIntoView({behavior:'smooth',block:'start'});
  } catch(error) { if (revision !== requestRevision || $('source').value !== source) return; $('result').hidden=false; $('verdict').textContent='Verification unavailable'; $('gate').textContent='BLOCKED'; $('reason').textContent=error.message; $('checks').replaceChildren(); $('summary').textContent=''; $('evidence').textContent='No new evidence produced.'; }
  finally { $('verify').disabled=false; }
});
$('accept').addEventListener('click', async () => {
  if(!current||capabilities.acceptance_enabled!==true)return;
  const evidence = current;
  const source = $('source').value;
  const requestRevision = revision;
  $('accept').disabled=true;
  try {
    await post('/api/accept',{run_id:evidence.run_id,candidate_sha256:evidence.candidate_sha256});
    if (revision !== requestRevision || current !== evidence || $('source').value !== source) return;
    $('accepted').textContent='Accepted locally after fresh verification. No merge or deployment.';
    $('accept').hidden=true;
  }
  catch(error){
    if (revision !== requestRevision || current !== evidence || $('source').value !== source) return;
    $('accepted').textContent=error.message;
  }
  finally{$('accept').disabled=false;}
});
$('download').addEventListener('click',()=>{
  if(!current)return;
  const form=document.createElement('form');form.method='POST';form.action='/api/report';form.hidden=true;
  for(const [name,value] of Object.entries({source:$('source').value,challenge_seed:current.challenge_seed})){
    const input=document.createElement('input');input.type='hidden';input.name=name;input.value=value;form.append(input);
  }
  document.body.append(form);form.submit();form.remove();
});
async function readJson(path){const r=await fetch(path);if(!r.ok)throw new Error('Could not load verification configuration.');return r.json();}
Promise.all([readJson('/api/config'),readJson('/api/examples')]).then(([config,data])=>{
  capabilities=config;examples=data;$('source').value=data.baseline;$('verify').disabled=false;
  if(config.mode==='hosted-preview'){
    $('mode-tag').textContent='VERIFICATION PREVIEW';
    $('mode-note').hidden=false;
    $('mode-note').textContent=config.persistence_configured
      ? 'Development storage configured. Each verification must save and read back evidence or return BLOCKED. Hosted acceptance remains disabled.'
      : 'Verification only. Evidence is not stored on the server. Download your report; acceptance stays disabled until durable storage is connected.';
  }
}).catch(error=>{$('verify').disabled=true;$('source').value=error.message;});
