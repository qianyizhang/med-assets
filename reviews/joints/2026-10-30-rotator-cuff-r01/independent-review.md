# Independent review — right cuff localization

Reviewed 2026-10-30 by the focused reviewer, separately from the builder.
**V2 visual verdict: pass-with-limitations for static regional localization.**
No remaining necessary visual correction or geometry change was requested.

The reviewer read the repository instructions and review contract, then inspected
both retained accepted shoulder WebPs and all four native preflight images.
The existing ligament/labrum study omits cuff muscles. The new source surfaces
provide a distinct lesson: supraspinatus and infraspinatus around the scapular
spine, teres minor along the lateral region, and subscapularis on the opposing
scapular face. The whole-subset view locates the close views against both bones.
This is added teaching context, not a finding that the accepted study is wrong.

V1 review inspected all four exact-GLB export images, the teaching sheet,
grayscale sheet and matched posterior Source / Export plate. The seven visible
label targets agreed with their named surfaces and recorded ray-hit bindings.
The long posterior S legend crowded the anterior 4 legend; no anatomy repair
was requested. V1 teaching is retained as the failed presentation diagnostic.

V2 shortens that legend to “Scapular spine / 肩胛冈”. The reviewer inspected all
three final presentation images and confirmed that the crowding is resolved.
Measured V1/V2 teaching differences occupy only pixel box (921, 883, 1152, 905).
All three anatomy panels, label bindings and the Source / Export plate are
unchanged. Source / Export shows consistent visible silhouettes and relations.
Grayscale retains numeric identification and outlines, but color is clearer.

- Native source SHA-256, personally checked:
  `9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd`.
- Canonical GLB SHA-256, 703,536 bytes, personally checked against replay:
  `edf5c2fc5322adc1c75703143b3fba5a2be3ecd87d5559bce1441c1977a4eb30`.
- V1 teaching SHA-256: `d5a7dc86c7556029f95b99f924a39fc7a8c2396a59896789f3157030151eeb4b`.
- V2 teaching SHA-256: `addb75923e5b96edfafbc6045a4c1075b8b93889da8863b2ab99440c349eb482`.
- V2 grayscale SHA-256: `7834414cc6606debd8e028db3de2cea962d89573b0feeb874797ef600082a78c`.

The reviewer independently checked all eight retained raw PNG hashes and all
three V2 presentation hashes against their records. Replay/render code and
surface-check records were read; the reviewer did not independently rerun Blender
or the aggregate suite. Code review reported a missing composition-label count
guard to the builder; this is separate from the seven targets actually inspected.

Scope remains source-named surfaces and source `.r` laterality, with illustrative
colors and native relationships. No complete attachment, tendon continuity,
action, watertightness, physical-scale, clinical or browser-runtime approval.
No publication was performed by the reviewer; the accepted study remains separate.
