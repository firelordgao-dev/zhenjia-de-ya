# Source checkpoint — 2026-09-30

This draft saves the local mini-program and web-prototype work for review.

- Source branch: `codex/duck-source-checkpoint-20260930`
- GitHub base: `ffc56e7a46dd2176e2f030203b63daf64fec20fd`
- Complete local checkpoint: `codex/checkpoint-duck-local-20260930` at `1bdb32c23c893f684b30ec4442eaf540fe1dc574`
- Original local master remains at `243ffd79ec2c07044f9dec2432f87c7666818424`, with its original 15 unpublished commits unchanged.
- The three new local commits preserve all 28 previously dirty/untracked files.

The source PR contains the code, tests, documentation and all referenced mini-program/web runtime images. It excludes the generated `output/` delivery packages, exploratory image boards, and developer-local project configuration. These files remain in the original project and full checkpoint. The largest local archive is 1,257,223,867 bytes; its history is intentionally not an ancestor of this source branch.

The local historical note `修改汇总.md` describes an earlier troubleshooting state. It is preserved as history, not a current deployment or authentication acceptance claim.

Existing offline checks cover syntax, routes, activity logic, image flow, layouts, visual assets, and mocked provider routing. Real WeChat/cloud deployment and live provider authentication still require acceptance. The current automatic image-analysis path passes only the first image to OCR even though the input page permits multiple images; this known unfinished behavior is preserved for subsequent review rather than declared complete.
