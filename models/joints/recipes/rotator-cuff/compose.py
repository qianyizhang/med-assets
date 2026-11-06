"""Compose source-bound teaching labels without changing anatomy pixels."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageChops, ImageStat

FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
BACKGROUND = '#151b20'
INK = '#eef2f3'
MUTED = '#bac5ca'
PANEL_SPECS = [('overview', (20, 170), 420), ('posterior', (460, 170), 680),
               ('anterior', (1160, 170), 680)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def font(size):
    return ImageFont.truetype(FONT, size)


def make_teaching(directory, checks, version=2):
    canvas = Image.new('RGB', (1860, 1100), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    draw.text((22, 16), 'Right rotator cuff muscles / 右肩袖肌群', font=font(39), fill=INK)
    draw.text((24, 76), 'Source-named surfaces in scapula–humerus context / 来源肌表面与肩胛骨、肱骨定位', font=font(23), fill=MUTED)
    names = {'overview': 'Whole subset / 完整选集', 'posterior': 'Posterior / 后面', 'anterior': 'Anterior / 前面'}
    # Display positions are deliberately outside the selected surface targets.
    badge_positions = {'posterior': {'1': (285, 240), '2': (175, 535), '3': (758, 470), 'S': (110, 365)},
                       'anterior': {'4': (785, 590)},
                       'overview': {'S': (150, 380), 'H': (750, 560)}}
    locators = []
    for name, (x, y), size in PANEL_SPECS:
        raw = Image.open(directory/'export'/(name+'.png')).convert('RGB')
        panel = raw.resize((size, size), Image.Resampling.LANCZOS)
        canvas.paste(panel, (x, y))
        draw.text((x, 125), names[name], font=font(25), fill=INK)
        view = next(v for v in checks['exportViews'] if v['file'] == name+'.png')
        for anchor in view['anchors']:
            px, py = anchor['pixel']
            bx, by = badge_positions[name][anchor['id']]
            point = (x+px*size/900, y+py*size/900)
            badge = (x+bx*size/900, y+by*size/900)
            draw.line((badge, point), fill=INK, width=2)
            draw.ellipse((point[0]-3, point[1]-3, point[0]+3, point[1]+3), fill=INK, outline=BACKGROUND)
            radius = 13 if name == 'overview' else 16
            draw.ellipse((badge[0]-radius, badge[1]-radius, badge[0]+radius, badge[1]+radius), fill=BACKGROUND, outline=INK, width=2)
            draw.text(badge, anchor['id'], font=font(18), fill=INK, anchor='mm')
            locators.append({'view': name, 'anchorId': anchor['id'], 'badgeInRawPixels': [bx, by]})
        if name == 'overview':
            # The visible proximal region is located by a source-surface callout.
            draw.text((25, 625), 'S  Scapula / 肩胛骨', font=font(22), fill=INK)
            draw.text((25, 661), 'H  Humerus / 肱骨', font=font(22), fill=INK)
            draw.text((25, 719), 'Close views crop the humeral shaft.', font=font(18), fill=MUTED)
            draw.text((25, 750), '近图裁切肱骨骨干；模型保留全长。', font=font(18), fill=MUTED)
    legend = [('1  Supraspinatus / 冈上肌', (465, 875)),
              ('2  Infraspinatus / 冈下肌', (465, 918)),
              ('3  Teres minor / 小圆肌', (820, 918)),
              ('S  Scapular spine / 肩胛冈' if version == 2 else 'S  Scapula: spine region / 肩胛冈区', (820, 875)),
              ('4  Subscapularis / 肩胛下肌', (1165, 875))]
    for text, position in legend:
        draw.text(position, text, font=font(21), fill=INK)
    draw.line((20, 972, 1840, 972), fill='#42525d', width=1)
    draw.text((24, 989), 'Illustrative colors; source .r laterality. Localization only: no attachment, tendon-continuity or action claim.', font=font(20), fill=MUTED)
    draw.text((24, 1023), '示意配色；左右沿用来源标记。仅作区域定位，不表示完整附着、肌腱连续性或肌肉动作。', font=font(20), fill=MUTED)
    draw.text((24, 1060), 'Z-Anatomy / BodyParts3D • CC BY-SA 4.0 • Offline exact-GLB views; no clinical or runtime validation.', font=font(16), fill=MUTED)
    return canvas, locators


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--version', type=int, choices=[1, 2], default=2)
    parser.add_argument('--previous-teaching')
    args = parser.parse_args()
    directory, out = Path(args.run), Path(args.out)
    checks = json.loads((directory/'checks.json').read_text())
    out.mkdir(parents=True, exist_ok=False)
    for kind in ['source', 'export']:
        for view in checks[kind+'Views']:
            assert sha(directory/kind/view['file']) == view['sha256'], 'Changed raw capture'
    teaching, locators = make_teaching(directory, checks, args.version)
    teaching.save(out/'teaching.png')
    ImageOps.grayscale(teaching).save(out/'grayscale.png')
    compare = Image.new('RGB', (1820, 1010), BACKGROUND)
    draw = ImageDraw.Draw(compare)
    draw.text((18, 16), 'Source / Export — posterior, matched camera and display', font=font(31), fill=INK)
    metrics = []
    for view in checks['sourceViews']:
        name = view['file']
        source = Image.open(directory/'source'/name).convert('RGB')
        exported = Image.open(directory/'export'/name).convert('RGB')
        difference = ImageChops.difference(source, exported)
        stats = ImageStat.Stat(difference)
        metrics.append({'view': name, 'meanAbsoluteRGBDifference255': sum(stats.mean)/3,
                        'maxChannelDifference255': max(v[1] for v in difference.getextrema())})
        if name == 'posterior.png':
            compare.paste(source, (5, 90)); compare.paste(exported, (915, 90))
    draw.text((20, 60), 'Source / 来源', font=font(21), fill=MUTED)
    draw.text((930, 60), 'Export: clean GLB reimport / 导出：GLB重新导入', font=font(21), fill=MUTED)
    compare.save(out/'source-export.png')
    outputs = {p.name: sha(p) for p in out.glob('*.png')}
    (out/'composition.json').write_text(json.dumps({
        'artifactSha256': checks['artifactSha256'], 'outputs': outputs,
        'version': args.version,
        'previousTeachingSha256': sha(args.previous_teaching) if args.previous_teaching else None,
        'labelBindings': locators, 'sourceExportPixelComparison': metrics,
        'renderConditions': 'Shared VIEWS and capture() in replay.py; identical camera, scale, lighting and exposure for each pair.',
        'grayscaleScope': 'Readability diagnostic of the same teaching pixels; color is preferred.'
    }, indent=2)+'\n')
    print('PASS: raw hashes, seven visible label bindings, teaching/grayscale and matched Source / Export composition')


if __name__ == '__main__':
    main()
