 // Checks the user flows changed by the interface simplification.
 await test('Повторное применение не затирает исходник и подтверждения',()=>{
  const a=fresh(),before=a.content;a.quality=qeNewCheck(a);a.generationDraft=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false});sgApplyDraft();
  const backup=JSON.stringify(a.qualityPreviousVersion);a.quality.approvedAt='editor-approval';const quality=JSON.stringify(a.quality);sgApplyDraft();
  assert(JSON.stringify(a.qualityPreviousVersion)===backup&&a.qualityPreviousVersion.content===before,'Затёрта предыдущая версия');assert(JSON.stringify(a.quality)===quality,'Повторный клик сбросил решения редактора');
  sgRenderGeneration();assert(document.querySelector('#generationBrief button[onclick="sgApplyDraft()"]').disabled,'Повторное применение доступно');
 });
 await test('Добавленные после применения изображения можно применить новой версией',()=>{
  const a=fresh();a.generationDraft=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false});sgApplyDraft();const before=a.content;
  Object.assign(a.generationDraft.visuals[0],{assetId:'a'.repeat(32),file:'images/'+('a'.repeat(32))+'.webp',width:1200,height:514,bytes:100});assert(!sgDraftApplied(a,a.generationDraft),'Новое изображение принято за старый вариант');sgApplyDraft();assert(a.content.includes('<img')&&a.qualityPreviousVersion.content===before,'Изображение не применено отдельной версией');
 });
 await test('Добавление порции фактов сохраняет введённый источник и индексы',()=>{
  const a=fresh();a.quality=qeNewCheck(a);a.quality.addedFacts=Array.from({length:23},(_,i)=>({claim:'Проверяемое утверждение номер '+i+' с достаточным пояснением.',sourceUrl:'',sourceQuote:'',origin:'Тест'}));
  const first=qeFacts(a)[0];a.quality.factDecisions[first.key]={status:'confirmed',sourceUrl:'https://example.org/source',sourceQuote:'Редактор проверил исходные данные и условия.'};renderCriteria();
  assert(document.querySelectorAll('#qeFactRows details.qe-row').length===10,'Нет первой порции');assert(!document.getElementById('qeFactList').open,'Весь список раскрыт');const input=document.getElementById('qe-fact-url-1');input.value='https://example.org/new-unsaved';uiMoreFacts();assert(input.value==='https://example.org/new-unsaved'&&document.querySelectorAll('#qeFactRows details.qe-row').length===20,'Порция затёрла введённые данные');uiMoreFacts();assert(document.querySelectorAll('#qeFactRows details.qe-row').length===23&&document.getElementById('qeMoreFacts').hidden,'Часть фактов недоступна');assert(document.getElementById('qe-fact-url-0').value==='https://example.org/source','Источник потерян при сортировке');
 });
 await test('Фильтр внимания не удаляет пройденные критерии',()=>{
  const a=fresh();complete(a);a.quality.manual[2].status='problem';a.quality.manual[3].status='unverified';qeSetFilter('attention');assert(document.querySelectorAll('[id^="qe-criterion-"]').length===2,'Внимание включает лишние критерии');qeSetFilter('all');assert(document.querySelectorAll('[id^="qe-criterion-"]').length===23,'Не все критерии доступны');qeSetFilter('attention');
 });
 await test('Предпросмотр текущей статьи совпадает с экспортом и не меняет текст',()=>{
  const a=fresh(),before=a.content;uiOpenPreview('current');const frame=document.querySelector('#preview iframe'),doc=new DOMParser().parseFromString(frame.srcdoc,'text/html');assert(frame.hasAttribute('sandbox')&&doc.querySelector('article').innerHTML===new DOMParser().parseFromString(htmlExport(),'text/html').querySelector('article').innerHTML,'Просмотр и экспорт расходятся');assert(a.content===before,'Просмотр изменил статью');
 });
 await test('Предпросмотр нового варианта не заменяет текущую статью',()=>{
  const a=fresh(),before=a.content;a.generationDraft=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false});sgPreviewDraft();assert(document.querySelector('#preview h2').textContent==='Новый вариант','Не указана версия');assert(document.querySelector('#preview iframe').srcdoc.includes(a.generationDraft.seo.h1)&&a.content===before,'Перепутана текущая статья и новый вариант');
 });
 await test('Редактор текста сохраняет позицию ввода при обновлении интерфейса',()=>{
  const a=fresh();uiOpenEditor();const view=document.getElementById('editorTextView');view.focus();view.innerHTML='<p>Начатая правка пользователя.</p>';const text=view.firstChild.firstChild,range=document.createRange();range.setStart(text,7);range.collapse(true);const selection=getSelection();selection.removeAllRanges();selection.addRange(range);view.dispatchEvent(new Event('input'));renderArticle();assert(a.content===view.innerHTML&&selection.anchorNode===text&&selection.anchorOffset===7,'Правка или позиция ввода потеряна');assert(document.getElementById('content').style.display==='none','По умолчанию показан HTML');view.blur();
 });
 await test('Следующее действие генератора учитывает готовность изображений',()=>{
  const a=fresh();assert(sgMainAction(a,null).action==='sgStart()','Нельзя создать статью');const d=sgParseGeneration(sgFixture(a),a,{profile:'short',images:true});a.generationDraft=d;assert(sgMainAction(a,d).action==='sgStart(true)','Нельзя продолжить картинки');d.visuals.forEach((v,i)=>Object.assign(v,{assetId:String(i+1).padStart(32,'0'),file:'images/'+String(i+1).padStart(32,'0')+'.webp',width:100,height:100}));assert(sgMainAction(a,d).action==='sgPreviewDraft()','Нет просмотра готового результата');assert(sgMainAction(a,d,true).action==='void 0','Можно запустить параллельную задачу');
 });
 await test('В прогрессе номер изображения отделён от общего процента',()=>{
  const a=fresh(),d=sgParseGeneration(sgFixture(a),a,{profile:'short',images:true}),job={kind:'generation',operation:'illustrate',options:{profile:'short'},draft:d,started:Date.now(),stage:'generating'};qeHelperJob=job;const root=document.createElement('div');root.innerHTML=sgRenderProgress();assert(root.querySelector('#sgStage').textContent==='Создаём изображение 1 из 3'&&root.querySelector('#sgPercent').textContent.startsWith('Общий прогресс: около '),'Счётчик склеен с процентами');assert(sgProgressView(job,Date.now()+999999).percent<100,'Незавершённая работа показана готовой');qeHelperJob=null;
 });
 await test('Исправление переносов не меняет сохранённое SEO-задание',()=>{
  const a=fresh();a.outline='H2: Первый раздел\\nH2: Второй раздел';const before=a.outline;renderArticle();assert(document.getElementById('outline').value.includes('\n')&&!document.getElementById('outline').value.includes('\\n'),'Переносы не отображаются');assert(sgBuildBrief(a).structure==='H2: Первый раздел\nH2: Второй раздел'&&a.outline===before,'Изменено исходное SEO-задание');
 });
 await test('Ручной возврат HTML и отчёта доступны в одном блоке',()=>{
  const a=fresh();a.quality=qeNewCheck(a);show('quality');const root=document.getElementById('qeManual');assert(root&&!root.open&&root.querySelector('[onclick="qeCopyRevision(true)"]')&&root.querySelector('[onclick="qePrepareReview()"]')&&root.querySelector('#qeRevisionPaste'),'Ручные инструменты потеряны');
 });
 await test('Ошибка записи не выдаётся за успешное автосохранение',()=>{
  fresh();const stored=localStorage.getItem(KEY),setter=Storage.prototype.setItem,savedFlag=uiSaved,errorFlag=uiSaveError;
  try{realSave(true);const saved=localStorage.getItem(KEY);assert(saved&&document.getElementById('studioSaveStatus').textContent==='Сохранено в этом браузере','Успешная запись не подтверждена');get().content+='<p>Новая несохранённая правка.</p>';Storage.prototype.setItem=function(key,value){if(key===KEY)throw new DOMException('Test quota','QuotaExceededError');return setter.call(this,key,value)};rejects(()=>realSave(true));assert(localStorage.getItem(KEY)===saved&&document.getElementById('studioSaveStatus').textContent.startsWith('Не сохранено'),'Ошибка скрыта или данные затёрты')}
  finally{Storage.prototype.setItem=setter;if(stored===null)localStorage.removeItem(KEY);else localStorage.setItem(KEY,stored);uiSaved=savedFlag;uiSaveError=errorFlag}
 });
 await test('Новый отчёт применённого текста обновляется без потери предыдущей версии',()=>{
  const a=fresh();a.quality=qeNewCheck(a);const d=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false}),candidate=sgDraftArticle(a,d);candidate.quality=qeNewCheck(candidate);qeInstallReview(candidate,qeValidateReport(report(candidate),candidate),true);d.quality=candidate.quality;a.generationDraft=d;sgApplyDraft();
  const backup=JSON.stringify(a.qualityPreviousVersion),content=a.content;d.quality=JSON.parse(JSON.stringify(d.quality));d.quality.review.importedAt=new Date(Date.parse(a.quality.review.importedAt)+1000).toISOString();assert(sgDraftReportPending(a,d),'Новый отчёт недоступен');sgApplyDraftReport();assert(a.content===content&&JSON.stringify(a.qualityPreviousVersion)===backup,'Отчёт затёр текст или предыдущую версию');assert(a.quality.review.importedAt===d.quality.review.importedAt&&!sgDraftReportPending(a,d),'Отчёт не обновлён');
 });
 await test('Неизменённый HTML из доработки не затирает предыдущую версию',()=>{
  const a=fresh();a.quality=qeNewCheck(a);a.qualityPreviousVersion={content:'<p>Прежняя версия до доработки.</p>',savedAt:'2026-10-20T10:00:00Z'};const before=JSON.stringify(a.qualityPreviousVersion);qeRevisionCandidate=qeParseRevision('<!-- ALFAPROM_QE_REVISION:'+qeRevisionToken(a)+' -->'+a.content,a);qeApplyRevision();assert(JSON.stringify(a.qualityPreviousVersion)===before,'Неизменённый вариант затёр исходную версию');
 });
 await test('Доработка через помощника доступна и без блокирующих ошибок',()=>{
  const a=fresh();a.quality=qeNewCheck(a);qeInstallReview(a,qeValidateReport(report(a),a),true);show('quality');assert(document.querySelector('#qualityRoot button[onclick="qeStartPlusRevision()"]'),'Повторная доработка недоступна при неподтверждённых критериях');
 });
