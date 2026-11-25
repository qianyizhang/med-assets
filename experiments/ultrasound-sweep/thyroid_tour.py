"""Compose a bilateral orientation tour from the two s1127 thyroid sweeps."""
from html import escape
from urllib.parse import urlencode

from tour_timeline import timeline_controls


def write_thyroid_tour(destination, tours):
    lobes = {tour['id']: tour for tour in tours if tour['id'] in ('thyroid-right', 'thyroid-left')}
    route = destination / 'tours/thyroid-orientation/index.html'
    if len(lobes) != 2:
        if route.exists():
            route.write_text('<!doctype html><html lang="en"><title>Bilateral thyroid orientation</title>'
                             '<h1>Bilateral thyroid orientation</h1><p>The thyroid sweeps are unavailable in this build.</p>'
                             '<a href="../index.html">Browse tours</a></html>\n')
        return False

    sections = []
    notes = []
    for side in ('right', 'left'):
        sweep_id = 'thyroid-' + side
        sweep = lobes[sweep_id]
        isthmus, transverse, longitudinal = sweep['keyframes']
        poses = [
            ('transverse', f'Slide {side}', isthmus['frame'], transverse['frame'], [isthmus, transverse],
             ('Start at the isthmus' if side == 'right' else 'Return to the midline') +
             f' and follow the probe toward the {side} lobe. In transverse section, find the trachea medially and the common carotid artery laterally.'),
            ('longitudinal', f'Rotate {side}', transverse['frame'] + 1, longitudinal['frame'], [longitudinal],
             f'Stay on the {side} lobe as the probe rotates. Follow the gland along its long axis and compare its shape with the transverse view.'),
        ]
        for plane, label, start, end, stops, cue in poses:
            section_id = side + '-' + plane
            sections.append(dict(id=section_id, label=label, sweep=sweep_id, start=start, end=end))
            links = []
            for stop in stops:
                query = urlencode({'chapter': section_id, 'frame': stop['frame']})
                links.append(f'<a href="?{escape(query)}">{escape(stop["label"])} view</a>')
            notes.append(f'<section class="chapter" id="{section_id}" hidden>'
                         f'<div><h2>{side.capitalize()} lobe · {plane}</h2><p>{escape(cue)}</p></div>'
                         f'<div class="evidence">{" ".join(links)}</div></section>')

    route.parent.mkdir(parents=True, exist_ok=True)
    route.write_text(f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Bilateral thyroid orientation · Ultrasound Anatomy</title>
  <link rel="stylesheet" href="../../study.css"><link rel="stylesheet" href="../../composed-tour/tour.css">
  <script defer src="../../composed-tour/tour.js"></script>
</head>
<body>
  <header class="mast"><div class="bar"><nav aria-label="Ultrasound studies">
    <a class="caseLink" href="../../index.html">All sweeps</a><a class="caseLink" href="../index.html">Tours</a>
  </nav></div></header>
  <main>
    <div class="introduction"><h1>Bilateral thyroid orientation</h1>
      <p>Start at the isthmus, slide to each lobe and rotate into its long axis. The left-side sequence starts back at the same midline window.</p>
    </div>
    {timeline_controls(sections)}
    <p id="tourProgress" class="sr" role="status"></p>
    {''.join(notes)}
    <div id="player" data-sweep-url="../../index.html"></div>
    <noscript><p>Enable JavaScript to play the tour.</p></noscript>
    <p class="standaloneLink"><a id="openSweep">Open standalone sweep</a></p>
    <aside class="reading"><h2>Compare the two lobes</h2>
      <p>The neck, thyroid and vessels share one s1127 CT. Turn on the anatomy overlay to follow the gland around the trachea.
      The acquired images show the corresponding views in other subjects and retain their own scale.</p>
    </aside>
  </main>
</body>
</html>
''', encoding='utf-8')
    return True
