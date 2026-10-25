# Quality Engine — обновление 25.10.2026

## Запуск помощника из студии — 25.10.2026

Коммит: `19913f3919426847a1cd35a8b97b40a2bd1fc905`. [Сборка GitHub Pages 40181941194](https://github.com/alfapakk-cloud/alfaprom-seo-studio/actions/runs/40181941194) завершена успешно, кнопка проверена на опубликованном сайте. Системный поиск обработчика через NSWorkspace вернул установленный ALFAPROM Helper.app. Сам переход по ссылке автоматически не выполнен из-за политики инструмента.

Добавлена кнопка «Запустить помощника» с системной ссылкой `alfaprom-seo://start`. Для текущего пользователя Mac установлен и зарегистрирован ALFAPROM Helper.app. Приложение работает в фоне с меню α SEO; окно Terminal не требуется. Веб-ссылка разрешает только запуск, без передачи команд, файлов и данных аккаунта.

Приложение содержит собственные копии сервера и панели, проверяет `/health` перед запуском второго процесса и останавливает активную генерацию при завершении. Сохранён прежний сценарий доработки и возврата статьи. Реальный запуск системной ссылки инструмент браузерной автоматизации заблокировал: этот шаг оставлен для ручной проверки пользователем, без заявления об успешном end-to-end тесте.

Проверено: 58 браузерных сценариев, 8 тестов Python, 13 случаев разбора системной ссылки; приложение собрано и его подпись проверена. Файлы и инструкция: `helper/macos/`, `helper/README.md`.


## Доработка 25.10.2026 — замкнутый цикл

Текущий релиз: `bca936f3dee7915175e817a4d94d8e55c860bdcc`. [Сборка GitHub Pages 40175325293](https://github.com/alfapakk-cloud/alfaprom-seo-studio/actions/runs/40175325293) завершена успешно; новый блок проверен на опубликованном сайте. После анализа автоматически формируется полное задание на исправление статьи с замечаниями, критериями, фактами и исходным HTML. Важность/фильтры интерфейса не скрывают замечания из задания. Непроверенные пункты отделены от доказанных ошибок.

Два сценария: «Доработать через Plus» с [локальным помощником](../helper/README.md) либо «Скопировать и открыть ChatGPT» с возвратом HTML-файла/вставкой HTML. До замены доступен изолированный предпросмотр. Есть метка принадлежности статьи/версии/анализа; устаревший ответ отклоняется, файл без метки требует явного подтверждения принадлежности. При применении сохраняется предыдущая версия, выполняется новая быстрая проверка, прежнее одобрение нового текста не переносится.

Локальный помощник вызывает уже установленный официальный Codex с ChatGPT-аутентификацией, не запрашивая отдельный API-ключ. Установленный клиент сообщил «Logged in using ChatGPT»; реальный запрос успешно вернул HTML, проверены возврат, предпросмотр, применение, повторный анализ и откат через интерфейс. Название тарифа и остаток лимита отдельным запросом не проверялись. Обработка идёт в пределах доступности/лимитов аккаунта, без автоматического подключения API-оплаты.

Проверка: 56 сценариев браузерной регрессии и 6 тестов помощника прошли. Предыдущий релиз ниже сохранён как история.


Опубликованный коммит: `5f9564b34890a09effce9bda5432978c6ab36d9a`.
GitHub Pages: [сборка 40171655445](https://github.com/alfapakk-cloud/alfaprom-seo-studio/actions/runs/40171655445) завершена успешно; опубликованный экран проверен в браузере, ошибок JavaScript не обнаружено.

Исходная версия для отката: `99d87fb37b7e3fc3b8b0277f82a3e18db7a9436e`.
Изменён только раздел Quality Engine в `index.html`: его разметка, стили и функции. Остальной интерфейс и ключ localStorage сохранены.

## Работа с текстом

1. Открыть статью → Quality Engine → «Быстрая проверка».
2. Исправить конкретные ошибки HTML, SEO-полей, заголовков, ссылок и служебных маркеров.
3. «Задание для AI» → скопировать или скачать TXT → передать в ChatGPT → получить `quality-report.json`.
4. Загрузить JSON через системный выбор файла. Отчёт должен содержать все 23 критерия, реальные цитаты, адресные замечания и факты. Отчёт другой версии не принимается.
5. Прочитать выводы и принять редакционную оценку. Спрос, факты, источники, оригинальность, каннибализация и доверие требуют отдельного решения редактора с основанием.
6. Подтвердить факты по первоисточникам: URL и цитата/пояснение. Добавить пропущенные утверждения вручную. AI не подтверждает свои факты автоматически.
7. Закрыть 22 критерия текста и утвердить текст. Критерий 9 проверяется на следующем этапе. Для критериев 14–18 допустима обоснованная неприменимость.

Статусы: пройдено / проблема / не проверено / не применимо. У каждого критерия указаны метод и основание. Условные баллы SEO, уникальности и достоверности удалены из интерфейса. Старые галочки не засчитываются как доказательства.

Версия привязана к содержимому, SEO-задаче, исходным исследовательским данным, базе блога и другим темам плана. При изменении этих данных предыдущие решения перестают подтверждать текущую версию; нужна новая проверка. Добавление визуалов не сбрасывает принятие неизменённого текста.

## Перед публикацией

Проверяется актуальное утверждение текста, SEO-разметка, наличие минимум четырёх разных файлов изображений в самом HTML, соответствие утверждённым карточкам и ALT. Метаданные карточки без тега img не считаются готовым визуалом. Редактор отдельно подтверждает доступность ссылок, загрузку/достоверность изображений и просмотр итогового HTML. Есть изолированный предпросмотр именно содержимого article.html.

Это решение о готовности внутри QE. Существующие кнопки экспорта в другом разделе сохранены. Генерация/загрузка изображений, их автоматическая вставка и полный пакет публикации относятся к следующим работам.

## Практические пределы

Автоматические правила проверяют формальные признаки и находят часть существенных утверждений. Они не доказывают поисковый спрос, смысловую оригинальность, полноту фактчека, качество источника или отсутствие каннибализации. Отчёт ChatGPT является редакционной помощью. Решения человека явно отделены от автоматических результатов. Внешних AI API и новых платных вызовов нет.

## Проверка релиза

- JavaScript прошёл `node --check`.
- 40 регрессионных сценариев в браузере: `tests/quality-engine.browser.js`.
- Проверены: устаревшие/неполные/противоречивые отчёты; выдуманные цитаты; импорт не подтверждает факты; HTML-ошибку нельзя перекрыть галочкой; старые баллы не засчитываются; правки отменяют одобрение; карточки без файлов не дают финальную готовность; ALT и дубли изображений; экранирование текста отчёта; пустое состояние самого QE.
- Через интерфейс проверены импорт HTML-файла, подготовка задания, загрузка JSON-файла, принятие редакционной оценки, запрет подтверждения факта без источника, сохранение неприменимости с основанием, сохранение после перезагрузки, финальные ограничения и экспортный предпросмотр.
- Полноценная редакционная оценка реальной пользовательской статьи и полный выпуск материала с изображениями этим релизным тестом не выполнялись.

Для повторного запуска регрессии создать временную копию `index.html`, добавив после документа `<script src="docs/tests/quality-engine.browser.js"></script>`, и открыть её на локальном HTTP-сервере. Тесты используют собственную демонстрационную очередь в памяти и отключают запись состояния. Временную страницу не публиковать.


## Revision UI 1.2 (2026-10-25)

Published commit: bbeef25006ee3dc81862701735e50ed729d3ac74. Added estimated progress, elapsed/remaining time, an authenticated loopback iframe bridge instead of a persistent popup, cancellation and word/block comparisons with deleted fragments. Highlights are preview-only and never enter article content or export; the previous version remains available after applying a revision.

Validation: 72 browser regressions and 12 Python tests. Mock end-to-end revision completed without calling GPT. Native app 1.2 installed and signed; the already running backend still reported protocol 2 and requires a manual menu stop/start to load protocol 3. Live Pages and actual native authentication still require verification before claiming full completion.

Published reconnect follow-up: 75b76d7d999610455053472ce4a0eb016e273b5b. Live tab verified the 1.2 UI. Mock cancellation returns to idle with the original article unchanged. Native backend still protocol 2; user asked to restart manually. The browser security block on automatic native launch remains in effect; do not substitute another launch method.


## Local Studio connection repair (2026-10-25)

Native app 1.3 / protocol 4 was installed and restarted by the user. Its authenticated account diagnostic returned ChatGPT state with exit code 0. Public HTTPS-to-loopback iframe did not deliver a ready message despite a healthy service. A local Studio deployment and explicit same-tab project transfer were implemented, retaining origin/host checks and nonce authentication for generation.

First live HTTPS form transfer was rejected because the default referrer policy sends Origin null for HTTPS-to-HTTP navigation. The explicit transfer now applies the origin-only referrer policy before form submission; the server still refuses untrusted/null origins. Published commits f5d979139fa68183aec61db47003e01d946762b8 and 4f9253a50efabd719873ba4438f58ec83a151c63.

Tests: 74 browser regressions, 14 Python tests, full mock same-tab transfer and revision, native local GET /studio and connected status. Live site transfer and native inference verification remain in progress. Website/local browser stores are independent; no automatic synchronization is claimed.


## Verified final result (2026-10-25)

Final release d631cf7718edf9af3866e122cdd9e88932a53ed9, helper 1.3.1 / protocol 5. Live HTTPS project transfer into the same tab at http://127.0.0.1:8766/studio succeeded. Queue, article, fingerprint and prior quality report survived the transfer. The native helper returned connected status.

The first live revision exposed a false-negative login preflight: login status was failing on GUI configuration, even though ChatGPT authentication was present. The generation runner now relies on its directly enforced forced_login_method=chatgpt and ignores user config, with API keys stripped. The user restarted the final backend. A complete real revision then finished in 2:23, returned 1552 words from a 106-word source, passed the version marker/import validation and displayed 100 percent. Added/rewritten text was highlighted; removed fragments were listed separately. The original article was not replaced. The result remains open in deliverable IAB tab 4. A clean local copy derived from the reviewed HTML is saved in article-improved-2026-10-25.html, with its original revision marker, no preview highlight markup.

Screenshots: quality-engine-real-complete-2026-10-25.png and quality-engine-real-diff-2026-10-25.png. This is a verified model request, not a mocked result. Tests remain 74 browser regressions and 14 Python checks. Public website and local Studio storage remain independent; use local Studio after transfer and export JSON backups.


## 1.4 — оценка, доработка и повторная оценка

Причина повторных 22 «не проверено»: повторная кнопка выполняла только локальный анализ HTML, а применение новой статьи сбрасывало редакционный JSON. Устранено отдельной автоматической оценкой всех 23 критериев и циклом audit → edit → audit, максимум две попытки исправлений. Исправленная версия остаётся черновиком для просмотра и возвращается с собственным проверенным fingerprint и отчётом. Применение сохраняет отчёт, а не сбрасывает его в 22 неизвестных статуса.

Часть критериев требует внешних доказательств: 1, 3, 4, 8, 12, 22. Они не становятся зелёными только из-за ответа модели. В интерфейсе эти пункты после оценки обозначены «Нужны данные», с основанием и задачей для редактора. №9 остаётся этапом визуалов. Самостоятельное утверждение готовности к публикации запрещено.

SEO-поля возвращаются вместе с HTML, отдельно показываются при просмотре и восстанавливаются с предыдущей версией. Исходная статья не меняется до применения; проверяются исходная версия, решения редактора, окно/Origin, идентификатор каждого этапа. Поздние ответы и неполные отчёты отклоняются. При ошибке после доработки промежуточный безопасный HTML сохраняется для просмотра и нового анализа.

Регрессии: 90 браузерных, 17 Python. HTTP-макет проверил полный цикл и применение вместе с отчётом; GPT для макета не запускался.
