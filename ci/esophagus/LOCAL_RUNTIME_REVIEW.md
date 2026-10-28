# Local verification boundary — proposed, not enabled

The anchor repair is verified locally with the actual pinned GLTFLoader,
Raycaster, baseline and reconstructed candidate. No GL/browser is required to
reproduce that interaction. The six-case regression uses no synthetic geometry,
no downloads, no npm install and no credential access. It completes in under one
second after its small pinned dependencies are present. The current offline PR
sanity gate stays unchanged; hosted success is not a substitute for this local
behavioral test or for required display checks.

## Missing local display prerequisites

The selected Linux cloud executor runs as non-root uid 1000. Node, Python,
`xauth`, `dpkg-query`, DejaVu and Noto CJK fonts are available. It has no
`firefox`, `/usr/lib/firefox/firefox`, `Xvfb`, `xvfb-run`, or
`/etc/firefox/syspref.js`; no display is active. No browser or privileged package
installation was attempted. The existing probe explicitly requires
`GITHUB_ACTIONS=true`; that guard was neither modified nor spoofed.

Two independent changes require review before a local display run is possible:

1. Provision a Linux cloud image with the reviewed packaged Firefox/Xvfb stack,
   readable package/policy provenance and a functioning unprivileged browser
   sandbox. Preserve the current package-integrity, syspref, non-root and sandbox
   warning checks; never fall back to disabled sandboxing or modified preferences.
2. Approve an explicit local entrypoint/mode. It should accept already-present
   pinned public fixture files in a task-specific directory, verify all sizes and
   SHA-256 values before use, reconstruct only in temporary storage, and call the
   same same-origin server, real WebGL readback, XWD display comparison and bounded
   report verifier. It must not depend on fabricated Actions environment variables.
   Browser environment/profile isolation, CSP/origin checks, host/hash/size and
   time limits, no external GLB dependencies and no security fallback stay intact.

For this repair the appropriate display scope is the 18 esophagus states,
including the real loaded anchors, numbered grayscale, bilingual legends and
hide/restore. The existing 55-state full probe and its lymph negative controls
remain available for changes affecting their shared behavior. A scope selector
must have an explicit expected sequence and cannot turn omitted states into a
full-probe pass. Source/geometry rebuilds unrelated to the change are unnecessary.

No protected runtime code or workflow is changed by this proposal. A future
reviewed local mode must stop on missing prerequisites, obtain no private data or
credentials, and retain failure receipts. Until then, local display/Chinese-glyph
acceptance is blocked. Parent review and an explicitly authorized protected rerun
are separate from this draft repair; a successful CPU raycast test is not a
55-state renderer pass. No additional web-browser workflow is proposed.
