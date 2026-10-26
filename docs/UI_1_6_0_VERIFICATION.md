# Interface simplification 1.6.0

Scope: approved changes 1–5 and 7–12. SEO-plan and strategy (item 6) are retained.

- Removed demo-fill and redundant prompt preparation controls; displayed literal line breaks as real newlines without migrating or rewriting saved SEO data.
- The generation toolbar follows the saved draft state. Restart is secondary. Image count and estimated overall progress have separate labels and layouts.
- Current article and new variant are explicitly identified. Repeated Apply cannot replace the previous version. A fresh report for an already applied article can be installed without replacing its text or backup.
- Helper connection status and startup settings are centralized in the header. Existing transfer and restore actions remain available.
- Quality review has one current-article outcome and an explicit next action. All 23 criteria remain available; attention is the default filter. Facts are collapsed and loaded in batches of ten, retaining stable evidence indexes and unsaved inputs while expanding.
- Manual ChatGPT handoff, JSON reports, TXT and HTML return are grouped. Quick HTML checking remains available under technical tools.
- The rich text editor is the default; the header reports successful browser saves and storage failures. Image metadata is collapsed; approval remains explicit.
- Preview and export share the same HTML document builder. Draft/current selection is explicit. Diff viewing remains separate. Primary exports are article plus images and project JSON; JSON does not embed image binaries.
- Navigation labels are clearer and use a compact two-row menu below 900px.

Validation: 126 isolated browser scenarios passed, including existing generation/audit/revision/recovery flows, failed-save handling, previous-version preservation, report-only updates, factual evidence pagination, matching preview/export, and rich-text caret preservation. JavaScript syntax checks passed. Four exact source-region comparisons confirmed that plan rendering, duplicate checking, imports, SEO auto-fill, article operations and the strategy form are unchanged.

The browser regression harness uses a separate storage key and simulated model responses. It does not submit live GPT requests or approve publication. GPT-6.1 Sol High, ChatGPT subscription authentication, helper protocol 8, backend code and WebP libraries are unchanged from 1.5.2. The native launcher source is unchanged; its existing compiled implementation is repackaged and signed for the new resources.

Saved article format, browser storage key and origin remain unchanged. Files in Application Support, browser profiles, credentials and user articles are not part of this release. Installation must preserve existing application and source files as rollback copies.
