"""Compose bilingual native teaching/evidence sheets without altering source renders."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BASELINE_SHA = '7451f9806e64fa9c04f55d97dd0f35f61bc09b56ce737f160809d8ea71e61143'
BG = '#10191e'
FG = '#edf1f2'
MUTED = '#bcc9cf'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


class Sheet:
    def __init__(self, size):
        self.image = Image.new('RGB', size, BG)
        self.overlay = Image.new('RGBA', size)
        self.draw = ImageDraw.Draw(self.overlay)
        self.bindings = []
        self.texts = []

    def text(self, xy, value, size=30, fill=FG):
        font = ImageFont.truetype(str(FONT), size)
        box = self.draw.textbbox(xy, value, font=font, anchor='lt')
        require(box[0] >= 0 and box[1] >= 0 and box[2] <= self.image.width and box[3] <= self.image.height,
                'Text extends beyond sheet: ' + value)
        self.draw.text(xy, value, font=font, fill=fill, anchor='lt')
        self.texts.append({'text': value, 'box': list(box)})

    def panel(self, path, xy, crop=None):
        source = Image.open(path).convert('RGB')
        crop = crop or (0, 0, *source.size)
        panel = source.crop(crop)
        require(xy[0] >= 0 and xy[1] >= 0 and xy[0]+panel.width <= self.image.width and
                xy[1]+panel.height <= self.image.height, 'Panel extends beyond sheet')
        self.image.paste(panel, xy)
        self.bindings.append({'file': path.name, 'sha256': digest(path), 'crop': list(crop),
                              'position': list(xy), 'size': list(panel.size), 'resampling': False})

    def leader(self, number, start, end):
        self.draw.line([start, end], fill=FG, width=2)
        x, y = end
        self.draw.ellipse((x-4, y-4, x+4, y+4), fill=FG)
        x, y = start
        self.draw.ellipse((x-21, y-21, x+21, y+21), fill=FG)
        self.draw.text((x, y-1), str(number), font=ImageFont.truetype(str(FONT), 28), fill=BG, anchor='mm')

    def save(self, path, inputs):
        final = Image.alpha_composite(self.image.convert('RGBA'), self.overlay).convert('RGB')
        final.save(path)
        # Every panel pixel outside the explicit editorial overlay must be exact.
        protected = 0
        for binding in self.bindings:
            original = Image.open(inputs[binding['file']]).convert('RGB').crop(binding['crop'])
            x, y = binding['position']; w, h = binding['size']
            actual = final.crop((x, y, x+w, y+h))
            alpha = self.overlay.getchannel('A').crop((x, y, x+w, y+h))
            difference = ImageChops.difference(actual, original)
            difference.paste((0, 0, 0), mask=alpha.point(lambda value: 255 if value else 0))
            require(difference.getbbox() is None, 'Source pixels changed outside editorial overlay')
            protected += sum(count for count, value in alpha.getcolors(w*h) if value == 0)
        return {'file': path.name, 'bytes': path.stat().st_size, 'sha256': digest(path),
                'size': list(final.size), 'panels': self.bindings, 'texts': self.texts,
                'unalteredPanelPixelsOutsideEditorialOverlay': protected}


def run(renders, baseline, output):
    require(not output.exists(), 'Output already exists')
    require(digest(baseline) == BASELINE_SHA, 'Original schematic image identity differs')
    receipt = json.loads((renders/'reimport-render.json').read_text())
    inputs = {row['file']: renders/row['file'] for row in receipt['views']}
    inputs[baseline.name] = baseline
    for row in receipt['views']:
        require(digest(inputs[row['file']]) == row['sha256'], 'Render identity differs')
    matched = []
    for view in ('overview', 'detail-R', 'detail-L'):
        source = Image.open(renders/('source-'+view+'.png')).convert('RGB')
        export = Image.open(renders/('export-'+view+'.png')).convert('RGB')
        require(source.size == export.size and ImageChops.difference(source, export).getbbox() is None,
                'Source/export matched pixels differ')
        matched.append({'view': view, 'identicalRGB': True, 'size': list(source.size)})
    output.mkdir(parents=True)
    records = []
    sheet = Sheet((1940, 1930))
    sheet.text((40, 30), 'Ovary + tubal-end context / 卵巢与输卵管末端', 48)
    sheet.text((40, 102), 'Native source relationships / 来源模型原生相对位置', 29, MUTED)
    sheet.text((490, 155), 'Source R / 来源右', 30)
    sheet.text((1320, 155), 'Source L / 来源左', 30)
    sheet.panel(renders/'export-overview.png', (370, 200), (0, 150, 1200, 650))
    sheet.text((40, 732), '1  Ovary / 卵巢       2  Fimbrial end / 伞端', 36)
    sheet.text((40, 790), 'Source R / 来源右', 30)
    sheet.text((1000, 790), 'Source L / 来源左', 30)
    leader_bindings = []
    for side, x in [('R', 40), ('L', 1000)]:
        sheet.panel(renders/('export-detail-'+side+'.png'), (x, 830))
        view = next(row for row in receipt['views'] if row['variant'] == 'export' and row['view'] == 'detail-'+side)
        for number, role in [(1, 'ovary'), (2, 'fimbria')]:
            anchor = view['anchors'][role]
            require(anchor['sourceNode'] == anchor['rayHitNode'], 'Leader is not on the named visible surface')
            endpoint = [x+anchor['pixel'][0], 830+anchor['pixel'][1]]
            start = [x+(530 if side == 'R' else 350), endpoint[1]]
            sheet.leader(number, start, endpoint)
            leader_bindings.append({'side': side, 'number': number, 'role': role,
                                    'sourceNode': anchor['sourceNode'], 'start': start, 'endpoint': endpoint})
    sheet.text((40, 1760), 'Coarse exterior context; follicles, ligaments and uterus are not included. / 粗略外形与位置；不含卵泡、韧带和子宫。', 26)
    sheet.text((40, 1804), 'Source gaps/cut ends remain; proximity is not an attachment claim. / 保留源间隙与截断端；相邻不代表附着。', 26)
    sheet.text((40, 1848), 'Source L/R labels · native +Z view / 来源左右标注 · 原生 +Z 视角', 26, MUTED)
    sheet.text((40, 1890), 'Browne & Schlehlein · HuBMAP / HRA · CC BY 4.0 · Ovary v1.3 + Fallopian tube v1.2', 22, MUTED)
    records.append(sheet.save(output/'teaching.png', inputs))
    gray = ImageOps.grayscale(Image.open(output/'teaching.png'))
    gray.save(output/'teaching-grayscale.png')

    comparison = Sheet((1600, 1600))
    comparison.text((32, 26), 'Original schematic / 原示意模型  →  Updated source subset / 更新来源子集', 35)
    comparison.text((32, 82), 'Different models, independent views and scales / 不同模型，视角和比例独立', 28, MUTED)
    comparison.panel(baseline, (32, 140))
    comparison.text((32, 772), 'Original: schematic exterior retained separately / 原模型：示意外形，独立保留', 29)
    comparison.text((32, 850), 'Updated: both ovaries with native tubal-end context / 更新：双侧卵巢及原生输卵管末端', 31)
    comparison.panel(renders/'export-overview.png', (200, 920), (0, 150, 1200, 650))
    comparison.text((32, 1460), 'All 10 acquired meshes; source geometry, gaps and cut ends retained. / 保留全部10个来源网格、间隙与截断端。', 25)
    comparison.text((32, 1505), 'Source L/R labels; no follicle or attachment reconstruction. / 沿用来源左右标注；未重建卵泡或附着。', 25, MUTED)
    comparison.text((32, 1550), 'Updated source: Browne & Schlehlein · HuBMAP / HRA · CC BY 4.0', 23, MUTED)
    records.append(comparison.save(output/'original-updated.png', inputs))

    for view in ('overview', 'detail-R', 'detail-L'):
        w, h = Image.open(renders/('source-'+view+'.png')).size
        pair = Sheet((w*2+120, h+230))
        pair.text((40, 20), 'Clean reimport: four sources / combined GLB  |  原始文件 / 合并导出', 32)
        pair.text((40, 77), 'Original source files / 原始来源文件', 28)
        pair.text((w+80, 77), 'Updated combined GLB / 合并导出', 28)
        pair.panel(renders/('source-'+view+'.png'), (40, 130))
        pair.panel(renders/('export-'+view+'.png'), (w+80, 130))
        pair.text((40, h+165), 'Matched camera, scale and lighting; identical RGB pixels. / 同视角、比例与光照；RGB像素一致。', 26, MUTED)
        records.append(pair.save(output/('matched-'+view+'.png'), inputs))
    result = {'candidateSha256': receipt['candidateSha256'], 'font': {'file': FONT.name, 'sha256': digest(FONT)},
              'baselineImageSha256': BASELINE_SHA, 'originalComparison': 'Different models, independent views/scales, no registration claim.',
              'matchedSourceExport': matched, 'leaders': leader_bindings, 'sheets': records,
              'grayscale': {'file': 'teaching-grayscale.png', 'bytes': (output/'teaching-grayscale.png').stat().st_size,
                            'sha256': digest(output/'teaching-grayscale.png')},
              'scope': 'Native static display only; clinical/anatomy approval and browser runtime unverified.'}
    (output/'composition.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({'sheets': len(records), 'matchedViews': matched, 'leaders': len(leader_bindings),
                      'protectedPixels': sum(row['unalteredPanelPixelsOutsideEditorialOverlay'] for row in records)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renders', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.renders, args.baseline, args.output)
