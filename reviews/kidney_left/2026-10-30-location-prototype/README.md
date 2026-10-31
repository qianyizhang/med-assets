# Retained kidney locator comparisons

Public comparison evidence for [PR #177](https://github.com/qianyizhang/med-assets/pull/177),
published on 2026-10-31 from the original 2026-10-30 Chromium captures of
`158f919e8305a656870f98d24d0eb97d5e47ec21`. These PNGs are copied byte-for-byte;
no recapture, re-encoding or new render was performed. The seven reviewed
prototype files remain unchanged.

All three images use Chromium 154.0.8037.57, a 1100 × 1000 viewport, device scale
1 and the same retained source tiles. The existing
[browser recipe](../../../tests/kidney_left_location/browser_check.py) records
the controls used to reach each captured state.

| Capture | Meaning | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| [Original](original-en.png) | Internal view, outline off; unchanged source pixels | 140016 | `77caf2159bf88c96a03d4e2eb6ba855a1f14c6926717231a6d21fd3ea6156129` |
| [Updated](updated-en.png) | Same internal view with the editorial exterior locator | 149407 | `db0fc6c2dc84717407c9ebc15e0c42cc55dfd378bb64eac284d8f9a0779ee93c` |
| [Simpler paired control](paired-en.png) | Exterior and internal views together at equal scale | 172388 | `fd764bd3456f8bfd481b91941177de67990a4d92d621f81ddc5e9642fff70d50` |

The outline supplies **2D editorial positional context**. It is not an anatomical
boundary, measured depth or a cutaway. The historical contact compositor is
unavailable; alignment was corroborated, not fully replayed. Source-labeled tip
surfaces are not a complete collecting system. PR #7's rejected columns+medulla
mode remains excluded. See the unchanged
[source proof, checks and scope](../../../studies/kidney_left_location/README.md).

Retain these three PNGs (461,811 bytes total) as the canonical repository copies
needed for immutable inline PR evidence. Original local and Space review evidence
remains preserved; no extra crop, alternate encoding, source image or GLB copy is
added here. Existing source/crop, keyboard, language, narrow-layout and failure
recovery results remain applicable because the prototype and source bytes are
unchanged. Publication pointer/offline checks and remote readback are recorded
in PR #177, separately from the original browser checks.

Source credit: Kristen Browne and Heidi Schlehlein (2024), HRA / HuBMAP female left
kidney v1.3, [DOI](https://doi.org/10.48539/HBM449.JPXL.964), CC BY 4.0.
The existing [attribution](../../../models/kidney_left/ATTRIBUTION.md) and source
records are unchanged. No clinical/anatomical approval or endorsement is claimed.
