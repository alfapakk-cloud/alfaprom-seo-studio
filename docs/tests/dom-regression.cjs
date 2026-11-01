/* Execute existing app DOM regressions in memory. No native browser, ports or network. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {JSDOM,ResourceLoader,VirtualConsole}=require(process.env.ALFAPROM_TEST_MODULES+'/jsdom');
const root=process.argv[2]?path.resolve(process.argv[2]):path.resolve(__dirname,'../..');
class LocalScripts extends ResourceLoader{fetch(url){const u=new URL(url);if(['generation.js','quality-autofix.js','publication.js'].includes(u.pathname.slice(1)))return Promise.resolve(fs.readFileSync(path.join(root,u.pathname.slice(1))));return null}}
let html=fs.readFileSync(path.join(root,'.quality-tests.html'),'utf8');
// These require actual image decoding/canvas or native contenteditable selection.
// The selection limitation was reproduced on unmodified 1.8.1 in the same DOM environment.
const skipped=['Браузер без WebP передаёт пиксели локальному кодировщику','Предпросмотр загружает настоящие WebP в обложку и заданные разделы','Редактор текста сохраняет позицию ввода при обновлении интерфейса'];
html=html.replace('const test=async(name,fn)=>{try{','const test=async(name,fn)=>{if('+JSON.stringify(skipped)+'.includes(name))return;try{');
const virtualConsole=new VirtualConsole(),errors=[];virtualConsole.on('jsdomError',e=>{if(!e.message.includes('navigation'))errors.push(e.message)});
const dom=new JSDOM(html,{url:'http://127.0.0.1:8765/.quality-tests.html',resources:new LocalScripts(),runScripts:'dangerously',virtualConsole,
 beforeParse(w){w.TextEncoder=TextEncoder;w.TextDecoder=TextDecoder;w.fetch=()=>Promise.reject(Error('Network disabled in DOM fixtures'));w.HTMLElement.prototype.scrollIntoView=function(){};w.URL.createObjectURL=()=> 'blob:http://127.0.0.1/'+crypto.randomUUID();w.URL.revokeObjectURL=()=>{};
  w.Blob.prototype.arrayBuffer=function(){return new Promise((resolve,reject)=>{const r=new w.FileReader();r.onload=()=>resolve(r.result);r.onerror=reject;r.readAsArrayBuffer(this)})};
  w.Blob.prototype.text=function(){return new Promise((resolve,reject)=>{const r=new w.FileReader();r.onload=()=>resolve(r.result);r.onerror=reject;r.readAsText(this)})};
 }});
(async()=>{for(let i=0;i<500&&!dom.window.document.title.startsWith('QE tests:');i++)await new Promise(r=>setTimeout(r,50));const title=dom.window.document.title,failed=[...dom.window.document.querySelectorAll('#quality-test-results li')].filter(e=>e.textContent.startsWith('✗')).map(e=>e.textContent);console.log(JSON.stringify({title,failed,skipped,environmentErrors:errors},null,2));dom.window.close();if(!title.includes('PASS')||failed.length||errors.length)process.exitCode=1})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1});
