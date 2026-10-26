# Article formats 1.7.0

This release includes the generation audit toggle, image progress, image-aware preview and explained Apply action from the 1.6.1 change, plus the larger article sizes requested next.

Current generation choices:

| Profile | Target visible characters with spaces | Body images | Additional cover | Total images |
| --- | ---: | ---: | ---: | ---: |
| small7000 | 7,000 | 4 | 1 | 5 |
| medium12000 | 12,000 | 6 | 1 | 7 |
| large20000 | 20,000 | 10 | 1 | 11 |

Targets use a 10% tolerance for generated text. HTML, SEO fields, image ALT and captions are excluded from the count. Medium is the default for a new generation. The full standard of 23 criteria remains in every generation prompt; the optional separate post-generation audit is enabled by default.

Legacy short/medium/large profile identifiers retain their existing 2,000/5,000/8,000 character rules and their original image counts. Existing article quality checks, saved generation drafts and paused image queues are not silently migrated to larger formats. Future generation preferences map the old size choice to the corresponding new one; reading those preferences does not change the saved article. Legacy draft cards explain that the larger formats apply to a new generation.

Validation: 143 isolated browser scenarios, including all previous checks and six format/compatibility cases. These cover the targets and body-plus-cover counts in prompts and result validation, the three UI choices and medium default, final quality requirements for new formats, unchanged legacy article fingerprints, applying old drafts and resuming their original queues. No live GPT requests are sent by the harness. See UI_1_6_1_VERIFICATION.md for preview/audit validation.

Backend protocol 8, ChatGPT subscription authentication, GPT-6.1 Sol High, the native launcher implementation and WebP libraries are unchanged. Installation preserves old application/source files and does not move browser data, credentials or article assets. Archives include only application files and documentation.
