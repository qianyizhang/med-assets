# Incorporated viewer context-loss recovery

The repair for [#192](https://github.com/qianyizhang/med-assets/issues/192) is
incorporated in the retained Site v50 viewer. Context loss permanently fails the
interactive view for that document: callbacks stop, resources are disposed and
bilingual unavailable text offers explicit Reload. Verified downloads and static
evidence remain usable until ordinary unload. Cached return and context-restored
events do not silently start another viewer.

The historical lifecycle-first applicator and composition ordering are retired.
[`tests/viewer/source.json`](../../../tests/viewer/source.json) binds the actual
current candidate and helpers. Run `python3 tests/viewer/run.py --suite context`
or `python3 tools/verify.py offline`.

All 14 context cases execute the current module, including loss during parse or
first frame, late success/failure, failed fetch, missing static evidence, locale
changes, stale actions, cached return, teardown and detached Reload controls.
The lifecycle suite independently preserves fallback/resource behavior. Runs have
private temporary staging; browser, renderer and transport are doubles.

Historical canonical and lifecycle-only sources reproduced 12 and 10 failures,
respectively, out of the original 14 cases. Those witnesses are not reconstructed
on every current test run. Actual browser context loss/restoration, import-map
resolution, WebGL/device integration and anatomy remain unverified. This repository
does not deploy the Site.
