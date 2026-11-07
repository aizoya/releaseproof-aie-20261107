// Exercise the actual UI handlers with delayed HTTP responses. Candidate strings
// remain data; this harness evaluates only our trusted application JavaScript.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

async function setup() {
  const nodes = new Map();
  function element() {
    return {value:'', hidden:true, disabled:false, textContent:'', handlers:{},
      addEventListener(event, handler){this.handlers[event]=handler;},
      replaceChildren(){}, append(){}, scrollIntoView(){}};
  }
  const get = id => {
    if(!nodes.has(id)) nodes.set(id,element());
    return nodes.get(id);
  };
  let resolve, reject;
  const pending = new Promise((yes,no)=>{resolve=yes;reject=no;});
  const examples={baseline:'original',correct:'correct',hardcoded:'hardcoded'};
  const fetch = async url => {
    if(url==='/api/verify') return pending;
    return {ok:true,json:async()=>url==='/api/config'?{acceptance_enabled:true}:examples};
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8'),{
    document:{getElementById:get,createElement:element},fetch,
  });
  await new Promise(setImmediate);
  const report={status:'pass',gate:'eligible',reason:'Passed',checks:[],checks_run:0,
    duration_ms:1,provider_calls:0};
  return {get,resolve:()=>resolve({ok:true,json:async()=>report}),reject};
}

for(const action of ['edit','switch','edit-and-restore']) {
  test(`discard late passing verdict after ${action}`,async()=>{
    const ui=await setup();
    const request=ui.get('verify').handlers.click();
    if(action==='switch') {
      ui.get('example').value='correct'; ui.get('example').handlers.change();
    } else {
      ui.get('source').value='changed'; ui.get('source').handlers.input();
      if(action==='edit-and-restore') {
        ui.get('source').value='original'; ui.get('source').handlers.input();
      }
    }
    ui.resolve(); await request;
    for(const id of ['result','accept','download']) assert.equal(ui.get(id).hidden,true,id);
    assert.equal(ui.get('verify').disabled,false);
  });
}
test('discard late network failure after edit',async()=>{
  const ui=await setup(); const request=ui.get('verify').handlers.click();
  ui.get('source').value='changed'; ui.get('source').handlers.input();
  ui.reject(new Error('late failure')); await request;
  assert.equal(ui.get('result').hidden,true);
  assert.equal(ui.get('verify').disabled,false);
});
test('unchanged candidate still receives its passing result',async()=>{
  const ui=await setup(); const request=ui.get('verify').handlers.click();
  ui.resolve(); await request;
  assert.equal(ui.get('result').hidden,false);
  assert.equal(ui.get('verdict').textContent,'Checks passed');
  assert.equal(ui.get('download').hidden,false);
  assert.equal(ui.get('accept').hidden,false);
});
