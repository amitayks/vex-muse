import puppeteer from 'puppeteer-core'; import {resolve} from 'node:path'; import {pathToFileURL} from 'node:url';
const b = await puppeteer.launch({executablePath:process.env.CHROME_PATH, headless:true, args:['--no-sandbox','--allow-file-access-from-files','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p = await b.newPage();
p.on('console', m=>console.log('[c]',m.type(),m.text().slice(0,200))); p.on('pageerror',e=>console.log('[err]',e.message));
p.on('requestfailed', r=>console.log('[fail]',r.url().slice(0,100),r.failure()?.errorText));
const t0=Date.now();
await p.goto(pathToFileURL(resolve('studio.html')).href+'?render',{waitUntil:'load',timeout:60000}).catch(e=>console.log('goto',e.message));
console.log('loaded',Date.now()-t0);
for(let i=0;i<30;i++){ const r=await p.evaluate(()=>window.ready); if(r){console.log('ready',Date.now()-t0);break;} await new Promise(r=>setTimeout(r,2000)); }
const t1=Date.now(); const url=await p.evaluate(()=>window.renderAt(1,'image/jpeg',.8)).catch(e=>'E:'+e.message); console.log('frame ms',Date.now()-t1, String(url).slice(0,40));
await b.close();
