#!/usr/bin/env bash
# Optional geometry-only reconstruction; NOT a recorded full-pipeline replay receipt.
set -euo pipefail
if [[ "$#" -ne 2 ]]; then
  echo "Usage: bash scripts/rebuild_optional.sh RAW_HRA_GLB NEW_RUN_DIRECTORY" >&2
  echo "Requires Python3.12 + NumPy2.3.5 + SciPy1.17.0 + Matplotlib; no network or Blender renders." >&2
  exit 2
fi
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
RAW="$($PY -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$1")"
RUN="$($PY -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$2")"
[[ -f "$RAW" ]] || { echo "Raw source not found: $RAW" >&2; exit 2; }
[[ ! -e "$RUN" ]] || { echo "Refusing to overwrite existing run directory: $RUN" >&2; exit 2; }
mkdir -p "$RUN/scripts" "$RUN/source" "$RUN/reviews" "$RUN/models"
for s in extract_hra_tongue.py inspect_source.py analyze_upper_patch.py select_exterior_p07.py excluded_components_p07.py restore_enclosed_source_p07.py trim_upper_join_p07.py export_prototype_p08.py refine_tip_p11.py verify_candidate_p11.py; do
  cp "$HERE/$s" "$RUN/scripts/$s"
done
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-2}"
export MPLCONFIGDIR="${TMPDIR:-/tmp}/matplotlib-tongue-recipe"
export XDG_CACHE_HOME="${TMPDIR:-/tmp}"
"$PY" "$RUN/scripts/extract_hra_tongue.py" --raw "$RAW" --output "$RUN/source/tongue-surfaces-hra-female-r02.glb" --receipt "$RUN/reviews/raw-extraction.json"
for s in inspect_source.py analyze_upper_patch.py select_exterior_p07.py excluded_components_p07.py restore_enclosed_source_p07.py trim_upper_join_p07.py export_prototype_p08.py refine_tip_p11.py verify_candidate_p11.py; do
  "$PY" "$RUN/scripts/$s" > "$RUN/reviews/replay-${s%.py}.log"
done
"$PY" - "$RUN/models/tongue-authored-hra-hybrid-p11.glb" <<'PY'
import hashlib,pathlib,sys
p=pathlib.Path(sys.argv[1]);r=p.read_bytes();h=hashlib.sha256(r).hexdigest()
expected='efabd58b235b72682f067113cf079e3f70fbaceac47062f2b937f09540c1ee1a'
print(f'{h}  {p} ({len(r)} bytes)')
if h!=expected or len(r)!=4983044:raise SystemExit('Digest mismatch: stop; this output is NOT the frozen reviewed candidate.')
print('This invocation reproduced candidate bytes. It does not rerun anatomy/static visual/runtime review.')
PY
