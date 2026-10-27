 // Version-aware Quality Engine uses the saved report, without applying or re-auditing it.
 const qualityDraft=(a,checked=true)=>{
  uiQualitySelection={};const d=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false,audit:checked});a.generationDraft=d;
  if(checked){const candidate=sgDraftArticle(a,d);candidate.quality=qeNewCheck(candidate);const r=report(candidate);r.criteria.forEach(c=>c.reason='Основание критерия '+c.id+': проверен именно новый вариант статьи, без подтверждения отсутствующих данных.');qeInstallReview(candidate,qeValidateReport(r,candidate),true);d.quality=candidate.quality;d.status='ready'}
  return d;
 };
 await test('После генерации раздел качества автоматически показывает отчёт нового варианта',()=>{
  const a=fresh(),d=qualityDraft(a),before=JSON.stringify(a);uiOpenQuality('auto',true);
  assert(uiQualityContext().draft&&document.querySelectorAll('#qeCriteriaList .qe-row').length===23,'Нет всех 23 критериев');
  assert(document.querySelector('#qeVersionChoice h3').textContent==='Новый вариант'&&document.querySelector('#qe-criterion-1').textContent.includes('Основание критерия 1:'),'Показан чужой отчёт');assert(JSON.stringify(a)===before,'Просмотр изменил статью или отчёт');
 });
 await test('Сводка в Структуре не повторяет полный отчёт и открывает тот же набор критериев',()=>{
  const a=fresh(),d=qualityDraft(a),root=document.createElement('div');root.innerHTML=sgRenderDraft(a,d);const text=root.querySelector('#sgQualitySummary').textContent,state=qeTextState({...sgDraftArticle(a,d),quality:d.quality});
  assert(text.includes('проблемы: '+state.bad.length)&&text.includes('нужны данные: '+state.unknown.length),'Счётчики различаются');assert(!root.textContent.includes('Основание критерия')&&!root.textContent.includes('Quality Engine нового варианта'),'Полный отчёт дублируется');assert(root.querySelector('button[onclick="uiOpenQuality(\'draft\',true)"]'),'Нет перехода к отчёту');
 });
 await test('Переключение версий не переносит оценки и решения между статьёй и черновиком',()=>{
  const a=fresh();complete(a);const d=qualityDraft(a),before=JSON.stringify(a);uiOpenQuality('draft',true);assert(document.querySelector('#qe-criterion-1').textContent.includes('Основание критерия 1:'),'Нет нового отчёта');uiOpenQuality('current',true);assert(document.querySelector('#qe-criterion-1').textContent.includes('Редактор проверил'),'Нет текущего отчёта');assert(JSON.stringify(a)===before,'Версии смешались');
 });
 await test('Непроверенный новый вариант не получает оценки текущей статьи',()=>{
  const a=fresh();complete(a);const d=qualityDraft(a,false);uiOpenQuality('auto',true);assert(uiQualityContext().draft&&!uiQualityContext().article.quality,'Подставлен отчёт другой версии');assert(qeResults(uiQualityContext().article).filter(r=>r.status==='unverified').length===22,'Есть ложные оценки');assert(document.querySelector('button[onclick="sgReviewDraft()"]')&&!d.quality,'Нет возможности запуска проверки');
 });
 await test('Применение переносит готовый отчёт без нового запроса и сохраняет исходник',()=>{
  const a=fresh();complete(a);const original=JSON.stringify(a.quality),content=a.content,d=qualityDraft(a),review=JSON.stringify(d.quality.review);uiOpenQuality('draft',true);sgApplyDraft();
  assert(!uiQualityContext().draft&&qeCurrent(a)&&JSON.stringify(a.quality.review)===review,'Отчёт сброшен');assert(a.qualityPreviousVersion.content===content&&JSON.stringify(a.qualityPreviousVersion.quality)===original,'Не сохранён исходник');assert(!qeHelperJob&&!a.quality.approvedAt&&!a.quality.final,'Запущена лишняя оценка или публикация утверждена');
 });
 await test('Шесть критериев с подтверждениями не закрываются автоматически при применении',()=>{
  const a=fresh();qualityDraft(a);sgApplyDraft();assert(qeManualOnly.every(id=>qeResults(a)[id-1].status==='unverified'),'Недоказанные критерии приняты');assert(qeResults(a)[8].status==='stage','Изображения ошибочно утверждены');
 });
 await test('После применения остаётся один отчёт, сводка использует новые решения редактора',()=>{
  const a=fresh(),d=qualityDraft(a);sgApplyDraft();a.quality.manual[1]={status:'pass',reason:'Редактор проверил частотность, регион, дату и источник спроса.'};uiOpenQuality('auto',true);const state=qeTextState(a),summary=sgQualitySummary(a,d);assert(!document.querySelector('#qeVersionChoice button[onclick="uiOpenQuality(\'draft\')"]'),'Дубликат текущей версии');assert(summary.includes('нужны данные: '+state.unknown.length),'Сводка использует устаревший отчёт черновика');
 });
 await test('В просмотре неприменённого отчёта нет действий, меняющих текущую статью',()=>{
  const a=fresh();qualityDraft(a);uiOpenQuality('draft',true);const root=document.getElementById('qualityRoot');assert(!root.querySelector('[onclick^="qeSaveCriterion"],[onclick^="qeStartQualityCycle"],[onclick^="qeStartPlusRevision"],[onclick^="qeApproveText"],[onclick^="qeRunFinal"]'),'Кнопка меняет другую версию');assert(!root.querySelector('#qe-status-1')&&root.querySelector('button[onclick="sgApplyDraft()"]'),'Нет безопасного перехода к применению');assert(root.querySelector('button[onclick="qeSetTab(\'final\')"]').disabled,'Черновик допускает публикацию');
 });
 await test('Факты нового варианта раскрываются порциями без редактирования чужих решений',()=>{
  const a=fresh(),d=qualityDraft(a);d.quality.review.facts=Array.from({length:24},(_,i)=>({claim:'Тестовое проверяемое утверждение номер '+i,sourceUrl:'https://example.org/'+i,sourceQuote:'Основание из тестового документа '+i}));const before=JSON.stringify(a);uiOpenQuality('draft',true);const rows=document.getElementById('qeFactRows');assert(rows.children.length===10,'Нет ограничения порции');uiMoreFacts();assert(rows.children.length===20&&rows.textContent.includes('документа 19'),'Не та версия фактов');assert(!rows.querySelector('input,textarea,[onclick^="qeSaveFact"]')&&JSON.stringify(a)===before,'Затронуты текущие данные');
 });
 await test('Устаревший черновик не выбирается автоматически и не допускает применения',()=>{
  const a=fresh();qualityDraft(a);a.content+='<p>Новая ручная правка исходной статьи.</p>';uiOpenQuality('auto');assert(!uiQualityContext().draft,'Выбран устаревший черновик');uiOpenQuality('draft');assert(uiQualityContext().stale&&document.querySelector('#qeVersionChoice').textContent.includes('Исходная статья изменилась'),'Нет предупреждения');assert(document.querySelectorAll('#qualityRoot button[onclick="sgReviewDraft()"]:not([disabled]),#qualityRoot button[onclick="sgApplyDraft()"]:not([disabled])').length===0,'Доступна опасная запись');
 });
 await test('Выбранная текущая версия сохраняется при обновлении, новый черновик выбирается отдельно',()=>{
  const a=fresh();qualityDraft(a);uiOpenQuality('current');renderCriteria();assert(!uiQualityContext().draft,'Выбор сброшен');qualityDraft(a);show('quality');assert(uiQualityContext().draft,'Новый черновик не выбран');
 });
 await test('Завершение генерации обновляет уже открытый раздел качества',()=>{
  const a=fresh(),d=qualityDraft(a),job={kind:'generation',articleId:a.id,draft:d};uiOpenQuality('draft',true);qeHelperJob=job;renderCriteria();assert(document.querySelector('#qualityRoot button[onclick="sgApplyDraft()"]').disabled,'Запись доступна во время задачи');sgFinish(job,'ready');assert(!document.querySelector('#qualityRoot button[onclick="sgApplyDraft()"]').disabled,'Завершённый отчёт не обновился');
 });
 await test('Готовый отчёт применяется и при ранее пустом исследовании',()=>{
  const a=fresh();delete a.generationBrief;const d=qualityDraft(a),candidate={...sgDraftArticle(a,d),quality:d.quality};assert(qeCurrent(candidate),'Кандидат потерял исследование');sgApplyDraft();assert(qeCurrent(a)&&a.quality.review?.criteria.length===23,'При применении отчёт потерян');
 });
