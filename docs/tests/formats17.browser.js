 // New format defaults must not reinterpret saved 1.x articles and drafts.
 await test('Новые форматы задают 7000/12000/20000 символов и 4/6/10 фото плюс обложку',()=>{
  const expected=[['small7000',7000,4],['medium12000',12000,6],['large20000',20000,10]];
  assert(JSON.stringify(SG_CURRENT_PROFILE_KEYS)===JSON.stringify(expected.map(x=>x[0])),'Другие варианты в выборе');
  for(const [key,target,images]of expected){const a=fresh(),brief=sgBuildBrief(a,{profile:key,images:true,audit:true});assert(brief.characters.target===target&&brief.visuals.body===images&&brief.visuals.cover===1&&brief.visuals.total===images+1,'Обложка посчитана внутри фото');assert(brief.qualityRequirements.length===23,'Стандарт потерян')}
 });
 await test('Новый генератор принимает статьи и якоря всех трёх больших форматов',()=>{
  for(const key of SG_CURRENT_PROFILE_KEYS){const a=fresh(),d=sgParseGeneration(sgFixture(a,key),a,{profile:key,images:true,audit:false}),p=SG_PROFILES[key];assert(d.chars>=p.min&&d.chars<=p.max&&d.visuals.length===p.images+1&&sgValidDraft(d),'Новый формат отклонён');const article=sgDraftArticle(a,d);assert(sgVisualCount(article)===p.images+1&&!qeAnalyze(article).issues.some(x=>x.title==='Объём не соответствует выбранному формату'),'Финальная проверка использует старый объём')}
 });
 await test('В интерфейсе только три новых размера, средний выбран по умолчанию',()=>{
  const a=fresh();sgRenderGeneration();const buttons=[...document.querySelectorAll('.sg-profile')];assert(buttons.length===3&&buttons.filter(b=>b.getAttribute('aria-pressed')==='true').length===1,'Лишние или невыбранные форматы');assert(sgOptions(a).profile==='medium12000'&&buttons[0].textContent.includes('Маленькая')&&buttons[0].textContent.includes('4 изображения'),'Новые размеры не отображаются');
 });
 await test('Старый формат статьи не меняется от новых настроек генерации',()=>{
  const a=fresh();a.contentProfile='medium';a.generationOptions={profile:'medium',images:true,audit:false};const before=JSON.stringify(a),fp=qeFingerprint(a);const options=sgOptions(a);assert(options.profile==='medium12000'&&!options.audit&&sgProfile(a).target===5000&&sgVisualCount(a)===6,'Старый материал принят за новый формат');assert(JSON.stringify(a)===before&&qeFingerprint(a)===fp,'Изменены сохранённая статья или её версия');
 });
 await test('Старый короткий черновик можно применить после перехода на новые размеры',()=>{
  const a=fresh(),before=a.content;a.generationDraft=sgParseGeneration(sgFixture(a),a,{profile:'short',images:false,audit:false});a.generationOptions={profile:'small7000',images:true,audit:true};sgApplyDraft();assert(a.contentProfile==='short'&&a.qualityPreviousVersion.content===before&&sgProfile(a).max===2000,'Старый черновик заблокирован или переосмыслен');
 });
 await test('Продолжение старой очереди не переводит её на 7000 символов и пять файлов',()=>{
  const a=fresh();a.generationDraft=sgParseGeneration(sgFixture(a),a,{profile:'short',images:true,audit:false});a.generationOptions={profile:'small7000',images:true,audit:false};const operation=sgOperation;let profile,total;sgOperation=j=>{profile=j.options.profile;total=j.draft.visuals.length};try{sgStart(true);assert(profile==='short'&&total===3,'Старая очередь получила новые требования')}
  finally{sgOperation=operation;qeClearHelperJob()}
 });
await test('Новые размеры не отправляются старому помощнику до обновления',()=>{
 const old={protocol:sgProtocol,state:qeHelperState,frame:qeHelperFrame,job:qeHelperJob,fail:sgFail,update:sgUpdateUI};let sent=0,error='';
 try{qeHelperState='connected';sgProtocol=8;qeHelperFrame={contentWindow:{postMessage(){sent++}}};sgFail=m=>{error=m;qeHelperJob=null};sgUpdateUI=()=>{};
  for(const profile of SG_CURRENT_PROFILE_KEYS){qeHelperJob={kind:'generation',operation:'generate',options:{profile},sent:false};sgSendJob();assert(!qeHelperJob&&error.includes('1.7.1')&&error.includes('ещё не отправлен'),'Нет понятной ранней ошибки')}
  assert(sent===0,'Запрос потратил лимит на несовместимом помощнике');
 }finally{sgProtocol=old.protocol;qeHelperState=old.state;qeHelperFrame=old.frame;qeHelperJob=old.job;sgFail=old.fail;sgUpdateUI=old.update}
});
await test('Помощнику протокола 9 доступны все новые форматы',()=>{
 const old={protocol:sgProtocol,state:qeHelperState,frame:qeHelperFrame,job:qeHelperJob,update:sgUpdateUI};let sent=0;
 try{qeHelperState='connected';sgProtocol=9;qeHelperFrame={contentWindow:{postMessage(data){assert(data.type==='alfaprom.generate','Другая операция');sent++}}};sgUpdateUI=()=>{};
  for(const profile of SG_CURRENT_PROFILE_KEYS){qeHelperJob={kind:'generation',operation:'generate',options:{profile},sent:false};sgSendJob();assert(qeHelperJob.sent,'Новый формат заблокирован')}
  assert(sent===3,'Не все форматы отправлены');
 }finally{sgProtocol=old.protocol;qeHelperState=old.state;qeHelperFrame=old.frame;qeHelperJob=old.job;sgUpdateUI=old.update}
});
await test('Старые форматы и продолжение изображений работают с протоколом 8',()=>{
 const old={protocol:sgProtocol,state:qeHelperState,frame:qeHelperFrame,job:qeHelperJob,update:sgUpdateUI};let sent=0;
 try{qeHelperState='connected';sgProtocol=8;qeHelperFrame={contentWindow:{postMessage(){sent++}}};sgUpdateUI=()=>{};
  for(const [operation,profile]of [['generate','short'],['generate','medium'],['generate','large'],['illustrate','medium12000'],['audit','medium12000']]){qeHelperJob={kind:'generation',operation,options:{profile},sent:false};sgSendJob();assert(qeHelperJob.sent,'Совместимая операция заблокирована')}
  assert(sent===5,'Операции потеряны');
 }finally{sgProtocol=old.protocol;qeHelperState=old.state;qeHelperFrame=old.frame;qeHelperJob=old.job;sgUpdateUI=old.update}
});
