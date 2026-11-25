"""Render the shared control and section marks for a composed ultrasound tour."""
from html import escape
from urllib.parse import urlencode


def timeline_controls(sections: list[dict]) -> str:
    """Place each section mark at its cumulative frame offset in the tour."""
    final_frame = sum(section['end'] - section['start'] + 1 for section in sections) - 1
    if final_frame < 1 or any(section['start'] < 0 or section['end'] < section['start'] for section in sections):
        raise ValueError('A tour timeline requires ordered frame intervals and at least two frames.')
    marks = []
    offset = 0
    for section in sections:
        key = escape(section['id'], quote=True)
        label = escape(section['label'], quote=True)
        sweep = escape(section['sweep'], quote=True)
        href = escape('?' + urlencode({'chapter': section['id']}), quote=True)
        phase = ' class="phase-start"' if section.get('phaseStart') else ''
        start, end = section['start'], section['end']
        position = 100 * offset / final_frame
        marks.append(f'<a href="{href}" data-chapter="{key}" data-sweep="{sweep}" data-start="{start}" '
                     f'data-end="{end}" data-label="{label}" style="--marker-position:{position:.4f}%"{phase}>'
                     f'<span>{label}</span></a>')
        offset += end - start + 1
    return f'''<div class="tourTimeline">
      <div class="tourTransport">
        <button type="button" id="playTour" disabled>Play tour</button>
        <output id="tourFrameNumber" for="tourPosition" aria-live="off"></output>
      </div>
      <div class="timelineTrack">
        <input id="tourPosition" type="range" min="0" max="{final_frame}" step="1" value="0" aria-label="Tour position" disabled>
        <nav class="chapters" aria-label="Jump to section" style="--section-count:{len(sections)}">{"".join(marks)}</nav>
      </div>
    </div>'''
