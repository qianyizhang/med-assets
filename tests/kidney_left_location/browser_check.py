"""Local 2D browser journeys and screenshots. Requires Playwright, Chromium, Pillow.

Start the repository-root HTTP server first; this does not access remote services.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

from verify_source import DISPLAY, require

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8765/studies/kidney_left_location/')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
source = Image.open(DISPLAY / 'contact.webp').convert('RGB')
checks = []


def image_error(a, b):
    require(a.size == b.size, 'Image dimensions differ')
    return sum(ImageStat.Stat(ImageChops.difference(a.convert('RGB'), b.convert('RGB'))).mean) / 3


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True)
    page = browser.new_page(viewport={'width': 1100, 'height': 1000}, device_scale_factor=1)
    errors, requests = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: requests.append(r.url))

    def visit(query=''):
        page.goto(args.url + query)
        page.wait_for_selector('#views:visible')
        page.wait_for_function("[...document.querySelectorAll('svg image')].every(x => x.getAttribute('href')?.startsWith('blob:'))")
        page.evaluate('document.fonts.ready')

    visit('?view=internal&outline=0')
    page.screenshot(path=str(args.output / 'original-en.png'), full_page=True)
    original_box = page.locator('#internal-panel svg').bounding_box()
    # Explicit clip keeps 420x420; locator screenshots expand fractional page bounds.
    page.screenshot(path=str(args.output / 'internal-crop.png'), clip=original_box)
    internal = Image.open(args.output / 'internal-crop.png').convert('RGB')
    err = image_error(internal, source.crop((0, 1016, 420, 1436)))
    require(err < 1, f'Internal crop differs: {err}')

    # Real keyboard switching: native radio group, same-position source tiles.
    page.locator('input[value="internal"]').focus()
    page.keyboard.press('ArrowLeft')
    require(page.locator('input[value="exterior"]').is_checked(), 'Keyboard exterior selection')
    require(page.locator('#exterior-panel svg').bounding_box() == original_box, 'Position/scale changed')
    require(page.locator('#locator').is_disabled(), 'Exterior locator should be unavailable')
    page.screenshot(path=str(args.output / 'exterior-crop.png'), clip=original_box)
    exterior_error = image_error(Image.open(args.output / 'exterior-crop.png'), source.crop((0, 112, 420, 532)))
    require(exterior_error < 1, f'Exterior crop differs: {exterior_error}')
    page.keyboard.press('ArrowRight')
    require(page.locator('input[value="internal"]').is_checked(), 'Keyboard return')
    page.locator('#locator').focus()
    page.keyboard.press('Space')
    require(page.locator('#locator').is_checked() and page.locator('#outline').is_visible(), 'Keyboard locator')
    require(page.locator('#internal-panel svg').bounding_box() == original_box, 'Locator moved the crop')
    require(page.locator('#locator').evaluate("el => getComputedStyle(el).outlineStyle") != 'none', 'Keyboard focus indicator')
    # Move focus off the control for a matched, neutral comparison capture.
    page.locator('#locator').blur()
    page.screenshot(path=str(args.output / 'updated-en.png'), full_page=True)
    page.screenshot(path=str(args.output / 'updated-crop.png'), clip=original_box)
    updated = Image.open(args.output / 'updated-crop.png').convert('RGB')
    changed = tissue_changed = 0
    baseline_bytes, updated_bytes = internal.tobytes(), updated.tobytes()
    for offset in range(0, len(baseline_bytes), 3):
        before, after = baseline_bytes[offset:offset + 3], updated_bytes[offset:offset + 3]
        if before != after:
            changed += 1
            if before[0] - before[1] > 12 and before[0] > 65:
                tissue_changed += 1
    require(changed > 500 and tissue_changed == 0, f'Locator obscures source shapes: {tissue_changed}')
    checks.append({'cropMeanAbsRGB': {'internal': err, 'exterior': exterior_error},
                   'keyboard': 'radio arrows, checkbox Space, visible focus, fixed tile position',
                   'outlineChangedPixels': changed, 'internalForegroundPixelsChanged': tissue_changed})

    visit('?view=paired&outline=0')
    require(page.locator('#exterior-panel').is_visible() and page.locator('#internal-panel').is_visible(), 'Paired control')
    require(page.locator('#outline').is_hidden(), 'Comparator has unexpected outline')
    for panel in ['exterior', 'internal']:
        box = page.locator('#' + panel + '-panel svg').bounding_box()
        require(box['width'] == box['height'] == 420, 'Comparator uses unequal scale')
    page.screenshot(path=str(args.output / 'paired-en.png'), full_page=True)

    visit('?view=internal&outline=1&lang=zh')
    page.screenshot(path=str(args.output / 'updated-zh.png'), full_page=True)
    require(page.locator('html').get_attribute('lang') == 'zh-CN', 'Document language')
    require('二维' in page.locator('#internal-title').text_content(), 'Chinese accessible image description')
    require(page.locator('[data-copy="original"]').text_content() == '原始审阅拼图', 'Corrected Chinese link')
    page.select_option('#language', 'en')
    require(page.locator('#locator').is_checked() and page.locator('input[value="internal"]').is_checked(), 'Language lost state')
    page.select_option('#language', 'zh')
    for width in [320, 375]:
        page.set_viewport_size({'width': width, 'height': 900})
        for language in ['en', 'zh']:
            page.select_option('#language', language)
            for view in ['exterior', 'internal', 'paired']:
                page.locator('input[value="' + view + '"]').check()
                require(page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Horizontal overflow: {width}/{language}/{view}')
                for caption in page.locator('figure:visible figcaption').all():
                    require(caption.evaluate('el => el.scrollHeight <= el.clientHeight'), f'Caption overflow: {width}/{language}/{view}')
                require(all(page.locator(el).text_content().strip() for el in ['h1', '#view-note', '#internal-title']), 'Missing localized text')
                if width == 320 and language == 'en' and view == 'internal':
                    page.screenshot(path=str(args.output / 'updated-en-narrow.png'), full_page=True)
    page.set_viewport_size({'width': 320, 'height': 900})
    page.select_option('#language', 'zh')
    page.locator('input[value="internal"]').check()
    page.screenshot(path=str(args.output / 'updated-zh-narrow.png'), full_page=True)
    page.locator('input[value="paired"]').check()
    page.locator('#locator').uncheck()
    page.screenshot(path=str(args.output / 'paired-zh-narrow.png'), full_page=True)
    checks.append({'languages': ['en', 'zh-CN'], 'narrowWidths': [320, 375], 'viewStates': 3, 'overflow': 'none'})

    page.set_viewport_size({'width': 1100, 'height': 1000})
    visit('?view=internal&outline=1')
    page.locator('#internal-panel svg').evaluate("el => el.style.filter = 'grayscale(1)'")
    page.locator('#internal-panel').screenshot(path=str(args.output / 'updated-grayscale.png'))
    # Failed/mismatched source must hide the entire figure; restoring bytes recovers.
    for status, body in [(404, b'missing'), (200, b'version https://git-lfs.github.com/spec/v1\n')]:
        page.route('**/display/contact.webp', lambda route, request, s=status, b=body: route.fulfill(status=s, body=b))
        page.goto(args.url)
        page.wait_for_function("document.querySelector('#status').textContent.includes('could not be verified')")
        require(page.locator('#views').is_hidden(), 'Failed source displayed an image')
        page.unroute('**/display/contact.webp')
    visit('?view=bad&lang=bad')
    require(page.locator('input[value="internal"]').is_checked(), 'Invalid state fallback')
    require(page.locator('html').get_attribute('lang') == 'en', 'Invalid language fallback')
    require(not errors, 'Browser errors: ' + repr(errors))
    require(all(url.startswith(('http://127.0.0.1:', 'blob:http://127.0.0.1:')) for url in requests), 'Unexpected remote request')
    checks.append({'sourceFailure': '404 and unresolved/mismatched bytes rejected; restored source recovered',
                   'consoleErrors': errors, 'network': 'local only', 'browser': browser.version})
    browser.close()

receipts = {path.name: {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(args.output.glob('*.png'))}
(args.output / 'checks.json').write_text(json.dumps({'checks': checks, 'images': receipts}, indent=2) + '\n')
print(json.dumps({'status': 'passed', 'checks': checks, 'imageCount': len(receipts)}, indent=2))
