// Run with Node 18+: node tests/test_frontend.mjs
// Exercises actual application functions with a small DOM stub, not a browser.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';
import {Blob} from 'node:buffer';
import {URL} from 'node:url';
import {serialize,deserialize} from 'node:v8';

const source=await fs.readFile(new URL('../static/app.js',import.meta.url),'utf8');
const nodes=new Map();
function node(selector){
  if(!nodes.has(selector))nodes.set(selector,{value:'',checked:false,files:[],disabled:false,textContent:'',
    addEventListener(){},setAttribute(){},replaceChildren(){},append(){}});
  return nodes.get(selector);
}
const context=vm.createContext({document:{querySelector:node,querySelectorAll:()=>[]},
  Blob,URL,structuredClone:value=>deserialize(serialize(value)),Date,console,setInterval(){},setTimeout(){},clearTimeout(){},
  Node:class{},window:{},confirm:()=>true});
vm.runInContext(source.replace(/\ninit\(\);\s*$/,'\n'),context,{filename:'app.js'});
const app=vm.runInContext('({caseSnapshot,validateCase,reportBody,setVersion,run,saveHibpKey,saveOathnetKey,importCase,clearCurrentCase})',context);
let count=0;
function check(name,fn){fn();count++;console.log('PASS:',name);}

check('server version is reused in HTML reports',()=>{
  app.setVersion('1.0.0');
  assert.match(app.reportBody(),/M-OSINT v1\.0\.0/);
  assert.throws(()=>app.setVersion('<bad>'));
});
const entry={feature_id:27,name:'Large comments',status:'functional',scope:'Test scope',
  timestamp:'2026-11-04T00:00:00+00:00',result:{text:'\\"'.repeat(150000)}};
check('large escaped result can be exported and imported again',()=>{
  const snapshot=app.caseSnapshot(entry);
  const serialized=JSON.stringify({schema:'mosint.case.v1',name:'Test',entries:[snapshot]});
  app.validateCase(JSON.parse(serialized));
  assert.ok(JSON.stringify(snapshot.result,null,2).length<=250000);
  assert.equal(entry.result.text.length,300000);
});
check('file bytes are excluded from saved case snapshots',()=>{
  const snapshot=app.caseSnapshot({...entry,result:{download:{name:'clean.png',base64:'test-file-bytes'}}});
  assert.equal(snapshot.result.download.base64,undefined);
});
check('cases containing new tool #110 can be reopened',()=>{
  const value={schema:'mosint.case.v1',name:'New tools',entries:[{...entry,feature_id:110,result:{unified_diff:'-old\n+new'}}]};
  app.validateCase(value);
});
check('reports include the exact creator name',()=>{
  assert.match(app.reportBody(),/TarikPro43391/);
});

vm.runInContext(`
  replace=()=>{};el=()=>({});toast=()=>{};
  retain=()=>{};outputResult=()=>{};renderHistory=()=>{};saveLocal=()=>{};
  addHistory=()=>({state:'Çalışıyor'});
  activeTool={id:65,name:'File hash',kind:'file',network:false};
  globalThis.fileReads=0;globalThis.apiCalls=0;
  globalThis.fileReady=new Promise(resolve=>globalThis.finishRead=resolve);
  readFile=async()=>{globalThis.fileReads++;return await globalThis.fileReady;};
  api=async()=>{globalThis.apiCalls++;return {feature_id:65};};
`,context);
node('#toolFile').files=[{size:3}];
const event={preventDefault(){}};
const first=app.run(event);
const second=app.run(event);
assert.equal(context.fileReads,1);
assert.equal(node('#runTool').disabled,true);
context.finishRead('YWJj');
await Promise.all([first,second]);
check('double submit while file loads makes one request',()=>{
  assert.equal(context.apiCalls,1);
  assert.equal(node('#runTool').disabled,false);
});
vm.runInContext(`readFile=async()=>{throw Error('unreadable file');};`,context);
await app.run(event);
check('file read failure releases the run lock',()=>{
  assert.equal(vm.runInContext('running',context),false);
  assert.equal(node('#runTool').disabled,false);
  assert.equal(context.apiCalls,1);
});
vm.runInContext(`renderDashboard=()=>{};api=async(path,payload)=>{globalThis.lastSettings={path,payload};return {saved:Boolean(payload.hibp)};};`,context);
context.fetch=async()=>({ok:true,json:async()=>({features:Array.from({length:111},(_,i)=>({id:i+1}))})});
node('#hibpKey').value='a'.repeat(32);
await app.saveHibpKey(false);
check('HIBP settings send only that provider key and clear the input',()=>{
  assert.equal(context.lastSettings.path,'/api/settings');
  assert.equal(context.lastSettings.payload.hibp,'a'.repeat(32));
  assert.equal(context.lastSettings.payload.ipinfo,undefined);
  assert.equal(node('#hibpKey').value,'');
});
await app.saveHibpKey(true);
check('HIBP removal does not submit an IP provider change',()=>{
  assert.equal(context.lastSettings.payload.hibp,'');
  assert.equal(context.lastSettings.payload.ipinfo,undefined);
});
node('#oathnetKey').value='test-oathnet-key';
await app.saveOathnetKey(false);
check('OathNet settings do not submit HIBP or IPinfo changes',()=>{
  assert.equal(context.lastSettings.payload.oathnet,'test-oathnet-key');
  assert.equal(context.lastSettings.payload.hibp,undefined);
  assert.equal(context.lastSettings.payload.ipinfo,undefined);
  assert.equal(node('#oathnetKey').value,'');
});
await app.saveOathnetKey(true);
check('OathNet key removal is independent',()=>{
  assert.equal(context.lastSettings.payload.oathnet,'');
  assert.equal(context.lastSettings.payload.hibp,undefined);
});
check('new OathNet result can be reimported into a case',()=>{
  app.validateCase({schema:'mosint.case.v1',name:'OathNet',entries:[{...entry,feature_id:111,result:{found:false}}]});
});
vm.runInContext(`
  globalThis.settingsCalls=0;
  globalThis.keyReady=new Promise(resolve=>globalThis.finishKey=resolve);
  api=async()=>{globalThis.settingsCalls++;return await globalThis.keyReady;};
`,context);
node('#hibpKey').value='a'.repeat(32);
node('#oathnetKey').value='second-key';
const firstKey=app.saveHibpKey(false);
await app.saveOathnetKey(false);
check('rapid provider updates cannot race each other',()=>{
  assert.equal(context.settingsCalls,1);
  assert.equal(node('#saveOathnetKey').disabled,true);
});
context.finishKey({saved:true});
await firstKey;
check('settings controls are unlocked after completion',()=>{
  assert.equal(vm.runInContext('settingsBusy',context),false);
  assert.equal(node('#saveOathnetKey').disabled,false);
});
vm.runInContext(`api=async()=>({saved:true});`,context);
context.fetch=async()=>({ok:false});
node('#hibpKey').value='a'.repeat(32);
await app.saveHibpKey(false);
check('saved key plus catalog failure explains the partial outcome',()=>{
  assert.match(node('#hibpKeyState').textContent,/uygulandı.*yenilenemedi/);
  assert.equal(vm.runInContext('settingsBusy',context),false);
});
vm.runInContext(`api=async()=>{throw Error('request rejected');};`,context);
node('#hibpKey').value='a'.repeat(32);
await app.saveHibpKey(false);
check('settings request failure preserves the input and releases controls',()=>{
  assert.equal(node('#hibpKey').value,'a'.repeat(32));
  assert.equal(node('#saveHibpKey').disabled,false);
});

context.savedEntry={...entry,result:{note:'keep current case'}};
vm.runInContext(`entries=[savedEntry];caseTitle='Case A';running=true;`,context);
let importReads=0;
await app.importCase({size:10,text:async()=>{importReads++;return '{}';}});
check('case import cannot replace a case during an analysis',()=>{
  assert.equal(importReads,0);
  assert.equal(vm.runInContext('caseTitle',context),'Case A');
});
app.clearCurrentCase();
check('case clearing cannot drop the target of an active result',()=>{
  assert.equal(vm.runInContext('entries.length',context),1);
});
vm.runInContext('running=false',context);
let finishImport;
const importPending=app.importCase({size:20,text:()=>new Promise(resolve=>finishImport=resolve)});
vm.runInContext('running=true',context);
finishImport(JSON.stringify({schema:'mosint.case.v1',name:'Case B',entries:[]}));
await importPending;
check('case import rechecks active analysis after asynchronous file reading',()=>{
  assert.equal(vm.runInContext('caseTitle',context),'Case A');
  assert.equal(vm.runInContext('entries.length',context),1);
});
console.log(`${count} frontend regression checks passed.`);
