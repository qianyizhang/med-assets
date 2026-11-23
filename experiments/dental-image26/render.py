"""Rebuild dental films offline from retained native GIFs and frozen narration."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import re

from PIL import Image, ImageDraw, ImageFont

from generate import ROOT, specification, validate_gif

FONTS = ROOT.parents[1] / 'sources/fonts/dejavu'
BG = '#102333'
WHITE = '#F4F0E8'
TEAL = '#78D6C0'
MUTED = '#B0C2CD'
GOLD = '#F2C97D'
INTRO = 'Five dental conditions. Five treatment stories. These are simplified illustrations; treatment depends on assessment.'
OUTRO = 'These stories omit many clinical steps. A dental professional assesses the condition and discusses suitable options.'


def run(args):
    subprocess.run([str(arg) for arg in args], check=True, capture_output=True)


def duration(path):
    result = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                                      'format=duration', '-of', 'json', str(path)])
    value = json.loads(result)['format'].get('duration')
    if value is None or float(value) <= 0:
        raise ValueError(f'No decodable duration: {path.name}')
    return float(value)


def font(size, bold=False):
    return ImageFont.truetype(str(FONTS / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')), size)


def text(draw, words, xy, width, size=28, color=WHITE, bold=False, spacing=12):
    face = font(size, bold)
    lines = []
    line = ''
    for word in words.split():
        candidate = (line + ' ' + word).strip()
        if draw.textlength(candidate, font=face) > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    lines.append(line)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=face, fill=color)
        y += size + spacing
    return y


def plate(path, story=None, shot=None, index=0, total=0, heading=None, body=None, label=None):
    image = Image.new('RGB', (1280, 720), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((48, 48, 90, 53), fill=TEAL)
    draw.text((106, 36), 'DENTAL STORIES', font=font(20, True), fill=TEAL)
    draw.text((850, 36), 'IMAGE 2.6 / EXPERIMENT', font=font(18), fill=MUTED)
    if shot:
        draw.rounded_rectangle((48, 104, 608, 664), radius=12, fill='#EDEBE7')
        draw.text((660, 109), f"{story['title'].upper()}  /  {index:02d} OF {total:02d}",
                  font=font(18, True), fill=TEAL)
        y = text(draw, shot['title'], (660, 155), 560, 39, WHITE, True, 10)
        y += 22
        y = text(draw, shot['caption'], (660, y), 550, 18, GOLD, True, 8)
        draw.line((660, y + 22, 1218, y + 22), fill='#365265', width=2)
        text(draw, shot['narration'], (660, y + 48), 548, 26, WHITE, spacing=12)
        draw.text((660, 617), 'Simplified illustration / treatment varies', font=font(17), fill=MUTED)
    else:
        draw.text((80, 130), label or 'FIVE CONDITIONS → FIVE TREATMENT STORIES',
                  font=font(22, True), fill=GOLD)
        y = text(draw, heading, (80, 205), 1110, 65, WHITE, True, 14)
        text(draw, body, (84, y + 36), 1080, 30, MUTED, spacing=14)
        draw.text((84, 630), 'Original AI-generated illustrations • educational experiment',
                  font=font(18), fill=TEAL)
    image.save(path)


def encode(name, narration, work, frames, gif=None, story=None, shot=None, index=0, total=0,
           heading=None, body=None, label=None):
    background = work / f'{name}.png'
    plate(background, story, shot, index, total, heading, body, label)
    seconds = frames / 30
    target = work / f'{name}.mp4'
    args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-loop', '1', '-i', background]
    if gif:
        args += ['-ignore_loop', '1', '-i', gif,
                 '-filter_complex',
                 f'[1:v]fps=30,scale=552:552,tpad=stop_mode=clone:stop_duration={seconds}[g];'
                 '[0:v][g]overlay=52:108:shortest=1,format=yuv420p[v]',
                 '-map', '[v]']
    else:
        args += ['-map', '0:v']
    args += ['-an', '-frames:v', str(frames), '-r', '30', '-c:v', 'libx264', '-preset', 'fast',
             '-crf', '19', '-pix_fmt', 'yuv420p',
             '-video_track_timescale', '15360', '-movflags', '+faststart', target]
    run(args)
    return target, seconds, narration


def concatenate(parts, target, work, name, audio_start=0):
    listing = work / f'{name}-concat.txt'
    # All segment names are controlled identifiers; no user text enters concat syntax.
    listing.write_text(''.join(f"file '{part[0].resolve()}'\n" for part in parts))
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0',
         '-i', listing, '-ss', str(audio_start), '-i', ROOT / 'audio/narration.flac',
         '-map', '0:v', '-map', '1:a', '-t', str(sum(part[1] for part in parts)),
         '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000', '-ac', '2',
         '-movflags', '+faststart', target])


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    sec, milliseconds = divmod(milliseconds, 1000)
    return f'{hours:02}:{minutes:02}:{sec:02},{milliseconds:03}'


def retained_timings(spec):
    """Bind retained speech/cut timings to the current narrated scene order."""
    expected = [('intro', INTRO)]
    for story in spec['stories']:
        expected.append((story['id'] + '-title', story['title'] + '.'))
        expected.extend((shot['id'], shot['narration']) for shot in story['shots'])
        expected.append((story['id'] + '-takeaway', story['takeaway']))
    expected.append(('outro', OUTRO))
    blocks = (ROOT / 'audio/narration.srt').read_text().strip().split('\n\n')
    if len(blocks) != len(expected):
        raise ValueError('Narration cue count differs from the current script')

    def seconds(value):
        if not re.fullmatch(r'\d{2}:\d{2}:\d{2},\d{3}', value):
            raise ValueError('Invalid narration timestamp')
        h, m, s, ms = map(int, re.split('[:,]', value))
        if m > 59 or s > 59:
            raise ValueError('Invalid narration timestamp')
        return h * 3600 + m * 60 + s + ms / 1000

    timings = {}
    previous_end = 0
    for number, ((name, narration), block) in enumerate(zip(expected, blocks), 1):
        lines = block.splitlines()
        if len(lines) < 3 or lines[0] != str(number) or ' '.join(lines[2:]) != narration:
            raise ValueError(f'Narration transcript differs from script: {name}')
        start, end = map(seconds, lines[1].split(' --> '))
        # The original edit places speech 300 ms into a scene and ends each cue
        # 200 ms before its cut. Round millisecond SRT precision onto 30 fps cuts.
        first_frame = round((start - 0.3) * 30)
        final_frame = round((end + 0.2) * 30)
        if first_frame != previous_end or final_frame <= first_frame:
            raise ValueError(f'Noncontiguous or invalid scene timing: {name}')
        timings[name] = final_frame - first_frame
        previous_end = final_frame
    return timings


def subtitles(parts, path):
    clock = 0
    lines = []
    for index, (_, seconds, words) in enumerate(parts, 1):
        lines += [str(index), f'{timestamp(clock + 0.3)} --> {timestamp(clock + seconds - 0.2)}',
                  '\n'.join(textwrap.wrap(words, 56)), '']
        clock += seconds
    path.write_text('\n'.join(lines))


def contact_sheet(spec, output):
    shots = [shot for story in spec['stories'] for shot in story['shots']]
    canvas = Image.new('RGB', (1440, len(shots) * 190 + 90), BG)
    draw = ImageDraw.Draw(canvas)
    draw.text((24, 20), 'NATIVE GIF SHOTS / frames 1, 5, 10, 16 / chronological',
              font=font(26, True), fill=WHITE)
    for row, shot in enumerate(shots):
        y = 90 + row * 190
        text(draw, shot['id'], (18, y + 15), 250, 20, TEAL, True)
        with Image.open(ROOT / 'gifs' / f"{shot['id']}.gif") as animation:
            for column, index in enumerate([0, 4, 9, 15]):
                animation.seek(index)
                frame = animation.convert('RGB')
                frame.thumbnail((170, 170))
                canvas.paste(frame, (310 + column * 275, y))
    canvas.save(output / 'shot-review.jpg', quality=90)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results')
    args = parser.parse_args()
    output = args.output.resolve()
    spec = specification()
    timings = retained_timings(spec)
    audio_seconds = duration(ROOT / 'audio/narration.flac')
    if abs(audio_seconds - sum(timings.values()) / 30) > 0.1:
        raise ValueError('Frozen narration duration differs from the retained edit')
    for story in spec['stories']:
        for shot in story['shots']:
            validate_gif((ROOT / 'gifs' / f"{shot['id']}.gif").read_bytes(), spec['request'])
    for binary in ['ffmpeg', 'ffprobe']:
        if not shutil.which(binary):
            raise RuntimeError(f'Missing executable: {binary}')
    scratch = ROOT.parents[1] / '.artifacts' / 'dental-image26-2026-11-06'
    scratch.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='edit-', dir=scratch))
    films = output / 'films'
    films.mkdir(parents=True, exist_ok=True)
    intro = encode('intro', INTRO, work, frames=timings['intro'], heading='From condition\nto treatment',
                   body='Five short stories about what changes, what is repaired, and what takes time.')
    all_parts = [intro]
    clock = intro[1]
    summaries = []
    for story in spec['stories']:
        parts = [encode(story['id'] + '-title', story['title'] + '.', work,
                        frames=timings[story['id'] + '-title'],
                        heading=story['title'], body=story['condition'] + ' → ' + story['procedure'],
                        label=f"{len(story['shots'])} SHOTS / ONE TREATMENT STORY")]
        for index, shot in enumerate(story['shots'], 1):
            print('Rendering', shot['id'], flush=True)
            parts.append(encode(shot['id'], shot['narration'], work,
                                frames=timings[shot['id']],
                                gif=ROOT / 'gifs' / f"{shot['id']}.gif", story=story,
                                shot=shot, index=index, total=len(story['shots'])))
        parts.append(encode(story['id'] + '-takeaway', story['takeaway'], work,
                            frames=timings[story['id'] + '-takeaway'],
                            heading='Remember', body=story['takeaway'], label=story['title'].upper()))
        target = films / f"{story['id']}.mp4"
        concatenate(parts, target, work, story['id'], audio_start=clock)
        clock += sum(part[1] for part in parts)
        subtitles(parts, target.with_suffix('.srt'))
        all_parts += parts
        summaries.append(f"- `{target.name}`: {duration(target):.2f} seconds; {len(story['shots'])} shots.")
    all_parts.append(encode('outro', OUTRO, work, frames=timings['outro'], heading='The next step is assessment',
                            body='Original AI-generated illustrations. No clinical or anatomical approval.\nSources: NIDCR / AAE / FDA.',
                            label='EXPERIMENT / NOT A PROCEDURAL TRAINING GUIDE'))
    master = output / 'dental-condition-to-treatment.mp4'
    concatenate(all_parts, master, work, 'master')
    subtitles(all_parts, master.with_suffix('.srt'))
    contact_sheet(spec, output)
    (output / 'README.md').write_text(
        '# Dental Image 2.6 — local film bundle\n\n'
        'Original generated illustrations; separate from maintained anatomical assets.\n\n'
        f'- Combined explainer: `dental-condition-to-treatment.mp4`, {duration(master):.2f} seconds.\n'
        '- Five individual films in `films/`; retained native animations in `../gifs/`.\n'
        '- Frozen English Samantha narration from `../audio/narration.flac`; no speech synthesis during rebuild.\n'
        '- Captions are burned in, with companion SRT files. No third-party music.\n'
        '- Each GIF plays once in the edit, followed by a final-frame hold; no reversed treatment.\n'
        '- Sources and exact prompts: `../stories.json` and `../SCRIPTS.md`.\n'
        '- Review frames: `shot-review.jpg`. Shared DejaVu fonts retain the sibling experiment license.\n\n'
        + '\n'.join(summaries) + '\n\n'
        '## Review\n\nSee `../README.md` for retained verification and review limits.\n\n'
        '## Retention\n\nRetain this requested bundle while reviewed or used. Review temporary edit files by 2026-12-06. '
        'No publication, asset admission or clinical approval is implied.\n')
    print('Master:', master, f'{duration(master):.2f} seconds', flush=True)


if __name__ == '__main__':
    main()
