"""Read the abdominal sweep catalogue."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read_tracks():
    catalogue = json.loads((HERE / 'abdomen-tracks.json').read_text())
    structures = catalogue['structures']
    tracks = []
    for row in catalogue['sweeps']:
        track = {**catalogue.get('common', {}), **row}
        styles = track.pop('partStyles', {})
        track['parts'] = [{'id': key, **structures[key], **styles.get(key, {})} for key in row['parts']]
        tracks.append(track)
    return tracks
