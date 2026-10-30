"""Compose portable bilingual visibility comparisons from bound native renders."""
import argparse
import base64
import json
from pathlib import Path
import struct
from xml.sax.saxutils import escape, quoteattr

if __package__:
    from .source import CAMERAS, CONTEXT, GLB_SHA, POSTERIOR_BASIS, RESOLUTION, load_inputs, project, require, sha
else:
    from source import CAMERAS, CONTEXT, GLB_SHA, POSTERIOR_BASIS, RESOLUTION, load_inputs, project, require, sha

INK, MUTED, BG = '#f4f2eb', '#bdc7cc', '#101b22'


def validate_record(record, expected_source):
    require(record['source'] == expected_source, 'Render source/context inventory differs')
    require(record['sourceBytesAndGeometryUnchanged'] is True, 'Geometry preservation not verified')
    require([c['name'] for c in record['source']['contexts']] == list(CONTEXT), 'Incomplete same-case context')
    require([(v['view'], v['state']) for v in record['views']] ==
            [(v, s) for v in CAMERAS for s in ('isolated', 'context')], 'Unexpected visibility pairs')
    for row in record['views']:
        config = CAMERAS[row['view']]
        require(row['file'] == row['view'] + '-' + row['state'] + '.png', 'Swapped image role')
        require(row['resolution'] == RESOLUTION, 'Changed view dimensions')
        require(row['contextVisible'] == (row['state'] == 'context'), 'Wrong visibility state')
        require(row['selectedGeometrySha256'] == expected_source['geometrySha256'], 'Selected geometry changed')
        require(abs(row['orthoScaleM'] - config['scale']) < 1e-7, 'Camera scale differs')
        require(all(abs(a-b) < 1e-7 for a,b in zip(row['cameraPosition'], config['position'])), 'Camera position differs')
        matrix = row['cameraWorldMatrix']
        require(all(abs(matrix[r][c] - POSTERIOR_BASIS[r][c]) < 1e-6
                    for r in range(3) for c in range(3)), 'Posterior camera is mirrored or rotated')
        require(all(abs(matrix[r][3] - config['position'][r]) < 1e-7 for r in range(3)), 'Camera matrix translation differs')
    witness = record['orientationWitness']
    for side in ('left', 'right'):
        expected = project(witness[side + 'ContextPointBlenderM'], CAMERAS['overview'])
        require(all(abs(a-b) < .001 for a,b in zip(expected, witness[side + 'PixelOverview'])), 'Orientation projection differs')
    require(witness['leftPixelOverview'][0] < witness['rightPixelOverview'][0], 'Laterality witness is reversed')


def inputs(root, renders):
    expected, *_ = load_inputs(root)
    record = json.loads((renders / 'render.json').read_text())
    validate_record(record, expected)
    images = {}
    for row in record['views']:
        data = (renders / row['file']).read_bytes()
        require(len(data) == row['bytes'] and sha(data) == row['sha256'], 'Render image identity mismatch')
        require(data[:8] == b'\x89PNG\r\n\x1a\n' and list(struct.unpack_from('>II', data, 16)) == RESOLUTION,
                'Render is not the expected PNG size')
        images[row['view'] + '-' + row['state']] = 'data:image/png;base64,' + base64.b64encode(data).decode()
    return record, images


def text(x, y, value, size=25, color=INK, weight=400, anchor='start'):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{escape(value)}</text>')


def crop_box():
    detail = CAMERAS['detail']
    half_w = detail['scale'] / 2
    half_h = half_w * RESOLUTION[1] / RESOLUTION[0]
    x, _, z = detail['position']
    corner = project([x + half_w, 0, z + half_h], CAMERAS['overview'])
    width = detail['scale'] / CAMERAS['overview']['scale'] * RESOLUTION[0]
    height = width * RESOLUTION[1] / RESOLUTION[0]
    return [*corner, width, height]


def panel(view, state, x, y, locator=False):
    key = view + '-' + state
    c = f'<g transform="translate({x} {y})" data-view="{view}" data-state="{state}">'
    c += f'<use xlink:href="#image-{key}"/>'
    c += text(18, 32, 'L / 左', 22, MUTED, 700)
    c += text(882, 32, 'R / 右', 22, MUTED, 700, 'end')
    if locator:
        a,b,w,h = crop_box()
        c += (f'<rect data-editorial="detail-crop" x="{a:.6f}" y="{b:.6f}" width="{w:.6f}" height="{h:.6f}" '
              'fill="none" stroke="#e7e0cd" stroke-width="1.6" stroke-dasharray="8 6"/>')
        c += text(round(a, 2), round(b - 10, 2), 'Detail / 局部', 20, '#e7e0cd')
    return c + '</g>'


def footer(y):
    c = text(40, y, 'Only the largest source-mask component is shown. / 仅显示源掩膜的最大连通组分。', 26, INK, 600)
    c += text(40, y + 42, 'Solid: retained component. Translucent: same-case heart and lungs. / 实色：保留组分；半透明：同例心、肺。', 24, MUTED)
    c += text(40, y + 82, 'Coarse context; original intersections retained. / 背景网格较粗；保留源模型交叠。', 24, MUTED)
    c += text(40, y + 128, 'TotalSegmentator · Wasserthal et al., University Hospital Basel · CC BY 4.0 · Label-source Apache-2.0 notice retained', 19, MUTED)
    return c


def frame(title, content, images, record, height):
    definitions = ''.join(f'<image id="image-{key}" width="900" height="700" xlink:href={quoteattr(value)}/>'
                          for key,value in images.items())
    meta = {'sourceSha256': GLB_SHA, 'sourceCase': 's1233', 'geometryEdited': False,
            'kind': 'same-case visibility/context teaching presentation',
            'contexts': [{k:c[k] for k in ('name','sha256','geometrySha256')} for c in record['source']['contexts']],
            'views': record['views'], 'detailCropInOverviewPixels': crop_box(),
            'orientation': 'Posterior; patient left is screen left',
            'license': 'CC BY 4.0; retained label-source Apache-2.0 notice'}
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1920" height="{height}" viewBox="0 0 1920 {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">The same retained left-sided component, isolated and with native same-case heart/lung context. Matched posterior cameras and scale. No branch reconstruction; only the largest source component is retained.</desc>
<metadata>{escape(json.dumps(meta, ensure_ascii=False, separators=(',', ':')))}</metadata>
<defs>{definitions}</defs><rect width="1920" height="{height}" fill="{BG}"/>
<g font-family="Noto Sans CJK SC, DejaVu Sans, sans-serif">{content}</g></svg>\n'''


def teaching(images, record):
    c = text(40, 44, 'Pulmonary vein: a retained left-sided example', 38, INK, 700)
    c += text(40, 88, '肺静脉：保留的左侧示例', 33, INK, 600)
    c += text(40, 128, 'Posterior view · same native positions · source case s1233 / 后面观 · 原位对照 · 源病例 s1233', 24, MUTED)
    c += text(40, 177, 'Isolated component / 单独显示', 29, INK, 700)
    c += text(980, 177, 'With same-case context / 同例上下文', 29, INK, 700)
    c += text(40, 214, 'Overview / 全貌', 23, MUTED)
    c += panel('overview', 'isolated', 40, 230, True) + panel('overview', 'context', 980, 230, True)
    c += text(40, 974, 'Detail · same posterior direction / 局部 · 同一后方视向', 25, INK, 600)
    c += panel('detail', 'isolated', 40, 995) + panel('detail', 'context', 980, 995)
    c += footer(1750)
    return frame('Pulmonary vein context / 肺静脉原位上下文', c, images, record, 1910)


def comparison(images, record, view):
    title = 'Overview / 全貌' if view == 'overview' else 'Detail / 局部'
    c = text(40, 46, 'MATCHED POSTERIOR COMPARISON / 匹配后面观对照 · ' + title, 27, MUTED, 600)
    c += text(40, 100, 'Original · isolated / 原模型 · 单独显示', 33, INK, 700)
    c += text(980, 100, 'Updated · context / 添加同例上下文', 33, INK, 700)
    c += text(40, 145, 'Same retained surface, camera and scale; new matched renders. / 同一保留表面、视角与比例；新渲染对照。', 24, MUTED)
    c += panel(view, 'isolated', 40, 170, view == 'overview')
    c += panel(view, 'context', 980, 170, view == 'overview')
    c += footer(925)
    return frame('Original / Updated — ' + title, c, {k:v for k,v in images.items() if k.startswith(view + '-')}, record, 1085)


def build(root, renders, output):
    record, images = inputs(root, renders)
    payloads = {'pulmonary-vein-context.svg': teaching(images, record)}
    payloads.update({view + '-comparison.svg': comparison(images, record, view) for view in CAMERAS})
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, content in payloads.items():
        raw = content.encode()
        (output / name).write_bytes(raw)
        rows.append({'file': name, 'sha256': sha(raw), 'bytes': len(raw)})
    result = {'sourceSha256': GLB_SHA, 'renderReceiptSha256': sha((renders / 'render.json').read_bytes()),
              'outputs': rows, 'embeddedImages': {v['file']:v['sha256'] for v in record['views']},
              'matchedCameraAndScale': True, 'geometryEdited': False, 'detailCropInOverviewPixels': crop_box()}
    (output / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--renders', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.root, args.renders, args.output), indent=2))
