// Saved drafts from standard 1 must remain auditable after the standard changes.
const compatLoadAssets=sgLoadAssets;sgLoadAssets=()=>{};
const oldSavedDraft181=(version=1)=>{
 const a=fresh(),d=qualityDraft(a,true);
 d.visuals.forEach((v,i)=>{const id=String(i+1).padStart(32,'0');Object.assign(v,{assetId:id,file:'images/'+id+'.webp',mime:'image/webp',width:1280,height:853,bytes:1000})});
 d.sourceFingerprint=qeFingerprintForVersion(a,version);
 d.quality.version=version;d.quality.snapshot=qeFingerprintForVersion(sgDraftArticle(a,d),version);
 d.quality.checkedAt='2026-10-27T10:08:00Z';
 return {a,d};
};
await test('Черновик стандарта1 не считается изменённым только из-за обновления программы',()=>{
 const {a,d}=oldSavedDraft181(1),stored=JSON.stringify(d);assert(d.sourceFingerprint!==qeFingerprint(a),'Фикстура не воспроизводит обновление');assert(sgDraftSourceCurrent(a,d),'Заблокирован прежний идентификатор');uiOpenQuality('auto',true);assert(uiQualityContext().draft&&!uiQualityContext().stale,'Сохранённая статья не выбрана');assert(!document.getElementById('qeVersionChoice').textContent.includes('Замена текущей статьи заблокирована'),'Ложное предупреждение');assert(!qeCurrent(uiQualityContext().article),'Старый отчёт засчитан по новому стандарту');assert(JSON.stringify(d)===stored,'Просмотр изменил сохранённые данные');
});
await test('Черновики1.8.0 и новый стабильный идентификатор сохраняют совместимость',()=>{
 const {a,d}=oldSavedDraft181(2);assert(sgDraftSourceCurrent(a,d),'Не принят прежний стандарт2');const modern=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false,audit:true});assert(modern.sourceFingerprint===sgSourceFingerprint(a)&&modern.sourceFingerprint!==qeFingerprintForVersion(a,1)&&modern.sourceFingerprint!==qeFingerprintForVersion(a,2),'Идентификатор по-прежнему зависит от стандарта');modern.quality={version:99};assert(sgDraftSourceCurrent(a,modern),'Версия отчёта меняет исходную статью');
});
await test('Реальные изменения текста и SEO по-прежнему блокируют применение старого черновика',()=>{
 for(const field of ['content','keyword','title']){const {a,d}=oldSavedDraft181(1),original=d.sourceFingerprint;a[field]+=' Новое изменение.';assert(!sgDraftSourceCurrent(a,d),'Не замечена правка '+field);const text=a.content;sgApplyDraft();assert(a.content===text&&d.sourceFingerprint===original,'Старый черновик заменил новый текст')}
});
await test('До новой проверки показывается отсутствие оценки, а не провал22 критериев',()=>{
 const {a}=oldSavedDraft181(1);uiOpenQuality('draft');assert(document.querySelector('.qe-verdict').textContent==='Нужна проверка по новому стандарту','Неясный итог');assert([...document.querySelectorAll('.qe-metric b')].every(n=>n.textContent==='—'),'Показаны фиктивные численные оценки');assert(document.getElementById('qualityRoot').textContent.includes('не оценка качества статьи'),'Не объяснено отсутствие отчёта');
});
await test('Ранее сгенерированная статья проходит весь путь запроса и отображения23 оценок без перегенерации',async()=>{
 const {a,d}=oldSavedDraft181(1);d.html='\n'+d.html+'\n';const original={content:a.content,html:d.html,seo:qeHash(d.seo),visuals:qeHash(d.visuals),source:d.sourceFingerprint};d.autofixPrevious={html:'Сохранённый предыдущий текст'};const backup=JSON.stringify(d.autofixPrevious),requests=[],transport={state:qeHelperState,protocol:qeHelperProtocol,frame:qeHelperFrame};qeHelperState='connected';qeHelperProtocol=10;const peer={postMessage(data){requests.push(data)}};qeHelperFrame={contentWindow:peer};
 try{
  uiOpenQuality('draft',true);qaStart('audit');const j=qeHelperJob;assert(j?.target==='draft'&&j.scope.length===23&&requests.length===1&&requests[0].type==='alfaprom.focused_audit','Запрос23 не отправлен');assert(a.content===original.content&&d.html===original.html,'Проверка изменила текст до ответа');assert(document.getElementById('qaStage').textContent==='Проверяем 23 критерия','Не видно начала проверки');
  const r=qaTestReport(j.article,QA_IDS,[7,22]);for(const id of [14,15,16,17,18])r.criteria.find(c=>c.id===id).status='na';
  await qeHandleHelperMessage({origin:QE_HELPER_ORIGIN,source:peer,data:{type:'alfaprom.focused_audit.result',jobId:j.id,result:r}});
  assert(!qeHelperJob&&requests.length===1,'Оценка запустила исправление или генерацию');const result=uiQualityContext().article;assert(qeCurrent(result)&&result.quality.review.criteria.length===23,'Отчёт не сохранён');assert(qeResults(result).filter(x=>x.status==='problem').length===2&&qeResults(result).filter(x=>x.status==='na').length===5,'Нет правильных результатов');assert(document.querySelectorAll('#qeCriteriaList .qe-row').length===23,'Результаты не появились в интерфейсе');assert(d.html===original.html&&a.content===original.content&&qeHash(d.seo)===original.seo&&qeHash(d.visuals)===original.visuals&&d.sourceFingerprint===original.source,'Проверка переписала статью/изображения');assert(JSON.stringify(d.autofixPrevious)===backup,'Проверка затёрла предыдущую версию');assert(d.quality.checkedAt!=='2026-10-27T10:08:00Z','Время проверки не обновилось');assert(qaPrimaryButton(result).includes('Исправить 2 критерия'),'Нет следующего действия');
 }finally{qeClearHelperJob();qeHelperState=transport.state;qeHelperProtocol=transport.protocol;qeHelperFrame=transport.frame}
});
await test('Даже действительно старый вариант проверяется отдельно, сохраняя новые правки текущей статьи',async()=>{
 const {a,d}=oldSavedDraft181(1);a.content+='<p>Новые правки пользователя после генерации.</p>';const source=a.content,html=d.html,old=d.sourceFingerprint,requests=[],transport={state:qeHelperState,protocol:qeHelperProtocol,frame:qeHelperFrame};qeHelperState='connected';qeHelperProtocol=10;qeHelperFrame={contentWindow:{postMessage(data){requests.push(data)}}};
 try{uiOpenQuality('draft',true);assert(uiQualityContext().stale,'Не воспроизведено изменение исходника');qaStart('audit');const j=qeHelperJob;assert(j?.target==='draft'&&requests[0].type==='alfaprom.focused_audit','Отдельная оценка заблокирована');await qaHandleMessage(j,{type:'alfaprom.focused_audit.result',jobId:j.id,result:qaTestReport(j.article)});assert(!qeHelperJob&&qeCurrent(uiQualityContext().article),'Нет отдельного отчёта');assert(a.content===source&&d.html===html&&d.sourceFingerprint===old,'Новые правки потеряны');sgApplyDraft();assert(a.content===source,'Проверенный старый вариант применился поверх новых правок')}
 finally{qeClearHelperJob();qeHelperState=transport.state;qeHelperProtocol=transport.protocol;qeHelperFrame=transport.frame}
});
await test('Боковая кнопка проверки вызывает тот же новый отчёт и не требует генерацию',()=>{
 const {a,d}=oldSavedDraft181(1),requests=[],transport={state:qeHelperState,protocol:qeHelperProtocol,frame:qeHelperFrame};qeHelperState='connected';qeHelperProtocol=10;qeHelperFrame={contentWindow:{postMessage(data){requests.push(data)}}};
 try{uiOpenQuality('current');sgReviewDraft();assert(qeHelperJob?.target==='draft'&&qeHelperJob.kind==='autofix'&&requests.length===1&&requests[0].type==='alfaprom.focused_audit','Два разных обработчика кнопок')}
 finally{qeClearHelperJob();qeHelperState=transport.state;qeHelperProtocol=transport.protocol;qeHelperFrame=transport.frame}
});
sgLoadAssets=compatLoadAssets;qeClearHelperJob();
