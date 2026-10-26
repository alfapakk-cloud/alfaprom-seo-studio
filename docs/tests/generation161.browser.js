 // Opt-out of the post-generation audit and real preview image loading.
 const previewWebp='UklGRkoAAABXRUJQVlA4ID4AAABwAwCdASoUABQAPkkijkUioiEUBAAoBISygDsAfgB+AABEQnAA/uqff//33wy3u3/uv//+5wCpDZ/iQAAAAA==';
 const previewFixture=(a,prefix='d')=>{const d=sgParseGeneration(sgFixture(a),a,{profile:'short',images:true,audit:false});d.visuals.forEach((v,i)=>Object.assign(v,{assetId:(prefix+String(i+1)).padEnd(32,'0'),file:'images/'+(prefix+String(i+1)).padEnd(32,'0')+'.webp',width:20,height:20,bytes:82}));return d};
 await test('Проверка после генерации включена по умолчанию и не меняет стандарт промта',()=>{
  const a=fresh(),fp=qeFingerprint(a);assert(sgOptions(a).audit===true,'Проверка выключена по умолчанию');sgRenderGeneration();assert(document.getElementById('sgAutoAudit').checked,'Галочка не показана');sgSetOption('audit',false);sgRenderGeneration();assert(!sgOptions(a).audit&&!document.getElementById('sgAutoAudit').checked,'Отказ не сохранён');assert(sgBuildBrief(a).qualityRequirements.length===23&&qeFingerprint(a)===fp,'Снят стандарт или сброшена текущая оценка');
 });
 await test('Выключенная проверка не отправляет отдельный запрос оценки',()=>{
  const a=fresh(),d=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false,audit:false}),audit=sgAudit,finish=sgFinish;let audits=0,status='';
  const job={kind:'generation',articleId:a.id,draft:d,options:{profile:'short',images:false,audit:false}};qeHelperJob=job;sgAudit=()=>audits++;sgFinish=(j,s)=>status=s;
  try{sgNextImage(job);assert(audits===0&&status==='ready-unchecked','Отправлен ненужный запрос');job.options.audit=true;sgNextImage(job);assert(audits===1,'Включённая проверка не запущена')}
  finally{sgAudit=audit;sgFinish=finish;qeClearHelperJob()}
 });
 await test('Продолжение очереди учитывает снятую галочку проверки',()=>{
  const a=fresh();a.generationDraft=previewFixture(a,'e');a.generationDraft.status='paused';a.generationOptions={profile:'short',images:true,audit:false};const after=sgAfterGeneration;let option;
  sgAfterGeneration=j=>{option=j.options.audit;qeClearHelperJob()};try{sgStart(true);assert(option===false&&a.generationDraft.autoAudit===false,'Очередь использует старое решение')}
  finally{sgAfterGeneration=after;qeClearHelperJob()}
 });
 await test('Ручная проверка доступна при выключенной автоматической',()=>{
  const a=fresh();a.generationDraft=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false,audit:false});const audit=sgAudit;let ran=false;
  sgAudit=j=>{ran=j.options.audit===true;qeClearHelperJob()};try{sgReviewDraft();assert(ran,'Ручная проверка тоже отключена')}
  finally{sgAudit=audit;qeClearHelperJob()}
 });
 await test('Пропущенная проверка не выдаётся за полученный отчёт',()=>{
  const a=fresh(),d=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false,audit:false});qeHelperJob={kind:'generation',articleId:a.id,draft:d};sgFinish(qeHelperJob,'ready-unchecked');assert(d.status==='ready-unchecked'&&!d.quality?.review,'Возник фиктивный отчёт');assert(sgRenderProgress().includes('не запускалась'),'Пропуск проверки скрыт');sgApplyDraft();assert(!a.quality.review&&!a.quality.approvedAt,'Статья ошибочно утверждена');
 });
 await test('Процент изображений относится к очереди картинок',()=>{
  const a=fresh(),d=sgParseGeneration(sgFixture(a),a,{profile:'short',images:true});d.visuals[0].assetId='f'.repeat(32);const now=Date.now(),job={kind:'generation',operation:'illustrate',options:{profile:'short'},draft:d,started:now,phaseStarted:now,stage:'generating'};
  const first=sgProgressView(job,now);assert(first.progressLabel==='Прогресс изображений:'&&first.displayPercent===45&&first.percent!==first.displayPercent,'Показан общий процент вместо процента изображений');const later=sgProgressView(job,now+60000);assert(later.displayPercent>=first.displayPercent&&later.displayPercent<100,'Неверный прогресс незавершённой очереди');
 });
 await test('Обычный предпросмотр выбирает неприменённый новый вариант',()=>{
  const a=fresh(),before=a.content;a.generationDraft=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false});uiOpenPreview();assert(document.querySelector('#preview h2').textContent==='Новый вариант'&&a.content===before,'Показана другая версия либо изменён текст');uiOpenPreview('current');assert(document.querySelector('#preview h2').textContent==='Текущая статья','Нельзя выбрать текущую версию');
 });
 await test('Предпросмотр загружает настоящие WebP в обложку и заданные разделы',async()=>{
  const a=fresh(),before=a.content,d=previewFixture(a,'a');const raw=Uint8Array.from(atob(previewWebp),c=>c.charCodeAt(0));d.visuals.forEach(v=>sgCacheAsset(v.assetId,new Blob([raw],{type:'image/webp'}),previewWebp));a.generationDraft=d;uiOpenPreview();await uiPreviewDocument.ready;
  const frame=document.getElementById('uiPublicationPreview'),doc=new DOMParser().parseFromString(frame.srcdoc,'text/html'),images=[...doc.querySelectorAll('img')];assert(images.length===3&&images.every(img=>img.src.startsWith('data:image/webp;base64,')),'Файлы не загружены в изолированный просмотр');assert(doc.querySelector('article').children[1].id==='visual-cover'&&doc.getElementById('part1').nextElementSibling.id==='visual-v01'&&doc.getElementById('part2').nextElementSibling.id==='visual-v02','Изображения потеряли места');assert(frame.getAttribute('sandbox')===''&&!JSON.stringify(db).includes('data:image')&&a.content===before,'Просмотр изменил хранилище или изоляцию');
  const image=new Image();await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('WebP не загрузился')),5000);image.onload=()=>{clearTimeout(timer);resolve()};image.onerror=()=>{clearTimeout(timer);reject(Error('WebP повреждён'))};image.src=images[0].src});assert(image.naturalWidth===20&&image.naturalHeight===20,'Файл не декодирован браузером');
 });
 await test('Поздняя загрузка изображений не подменяет выбранную версию',async()=>{
  const a=fresh(),d=previewFixture(a,'b'),request=sgRequestAsset,before=qeHelperState,waiting=[];qeHelperState='connected';sgRequestAsset=(action,data)=>new Promise(resolve=>waiting.push({id:data.assetId,resolve}));a.generationDraft=d;
  try{uiOpenPreview('draft');const ready=uiPreviewDocument.ready;uiOpenPreview('current');waiting.forEach(r=>r.resolve({assetId:r.id,mime:'image/webp',base64:previewWebp}));await ready;assert(document.querySelector('#preview h2').textContent==='Текущая статья'&&!document.getElementById('uiPublicationPreview').srcdoc.includes(d.seo.h1),'Поздний ответ заменил текущую версию')}
  finally{sgRequestAsset=request;qeHelperState=before;sgAssetPromises.clear()}
 });
 await test('Применение из предпросмотра обновляет редактор и экспорт',()=>{
  const a=fresh(),before=a.content;a.generationDraft=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false,audit:false});uiOpenPreview();assert(document.querySelector('#preview button[onclick="sgApplyDraft()"]'),'Нет понятного применения рядом с просмотром');sgApplyDraft();renderAll();assert(document.querySelector('#preview h2').textContent==='Текущая статья'&&a.qualityPreviousVersion.content===before&&document.getElementById('content').value===a.content&&htmlExport().includes(a.generationDraft.seo.h1),'Не обновлены текущая версия, редактор или экспорт');
 });
