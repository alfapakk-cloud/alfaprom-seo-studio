# Bundled PDF parser dependencies

Pinned packages from the Python Package Index: pypdf 6.21.4 and typing_extensions 4.16.0 (Python 3.9/3.10 dependency). No system Python packages are changed.

Reproduce in a clean directory with Python 3.9: `python3 -m pip install --no-compile --target helper/vendor -r helper/requirements.txt`.

Original source, metadata and licenses are included unchanged. The helper uses no external PDF service, parser executable, OCR, paid API or dynamic package installation. PDF parsing runs in a child process with 10 MB input, bounded decompression/page/text budgets, 16-second wall timeout, CPU limit and a parent 512 MiB RSS monitor (macOS does not implement RLIMIT_AS). Scans/encrypted/unreadable documents remain unverified. Their absence is not a positive assessment.
