# Generation fix 1.7.1

The 1.7.0 server result validator still allowed only legacy visual counts (3/6/11 including the cover). Correct current small and medium generation responses (5/7 including the cover) were rejected after inference. The JSON schema's existing range already permitted those counts; this was a server validation bug, not an instruction to remove images.

The validator now permits the union of current and legacy counts: 3/5/6/7/11. Frontend validation still requires the exact selected count, one leading cover, complete visual metadata and distinct existing HTML anchors. No model response is silently trimmed or padded.

Health protocol increases to 9. New-format generation is blocked locally before sending a model request if a pre-fix helper is running, with a specific 1.7.1 update/restart message. Legacy generation, image queue continuation, audit and revision compatibility are preserved. The response schema, model (gpt-6.1-sol/high), ChatGPT-only authentication, key removal, loopback Host/Origin/session controls and WebP libraries remain unchanged.

Verification:

- Reproduced the reported error before the fix using the actual `execute_task` result handler with a mocked Codex subprocess. New small and medium responses failed; large and legacy responses passed.
- After the fix all 10 Python test cases pass. They exercise all six frontend profile counts through the backend, invalid counts/non-arrays, missing HTML/SEO, unaffected edit/revision/audit operations, and pinned model/reasoning/ChatGPT-only command/environment.
- All 146 isolated browser checks pass, including pre-request rejection with protocol 8, acceptance of all current formats with protocol 9, and continued protocol-8 legacy/image/audit compatibility.
- Tests use fixtures; they do not send live GPT requests, read login files or modify real articles.

Native bundle version: 1.7.1, build 12. The launcher binary and signed WebP libraries are reused from the verified 1.7.0 archive; application resources are updated and the bundle re-signed and verified. Both archives contain only program files, libraries/licenses and documentation. Installation preserves the prior app/source files and user data. A running Python helper must be restarted once to load the fixed backend.
