"""Deterministic presentation-only derivative of the retained source diagnostic."""
import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path

BASELINE_SHA = '206915ffa0b6b625ca17e32f35b893e1d1a103f25bce59f41e02d657ab9e7fd5'
SOURCE_SHA = '9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'
NAMES = ['Ulnar nerve.r', 'Humerus.r', 'Ulna.r', 'Radius.r']

def read_glb(path):
    data = Path(path).read_bytes()
    if len(data) < 20 or struct.unpack_from('<4sII', data) != (b'glTF', 2, len(data)):
        raise ValueError('Invalid GLB header')
    size, kind = struct.unpack_from('<II', data, 12)
    if kind != 0x4e4f534a or 20 + size > len(data):
        raise ValueError('Invalid GLB JSON chunk')
    return json.loads(data[20:20+size]), data[20+size:]

def build(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError('Output must be new')
    if hashlib.sha256(source.read_bytes()).hexdigest() != BASELINE_SHA:
        raise ValueError('Exact retained source diagnostic required')
    original, rest = read_glb(source)
    result = copy.deepcopy(original)
    if [n['extras']['source_object'] for n in result['nodes']] != NAMES:
        raise ValueError('Unexpected source selection')
    for material in result['materials']:
        nerve = material['name'].startswith('Ulnar nerve.r')
        material['name'] = ('Ulnar nerve — illustrative ochre' if nerve else
                            material['name'].split(' illustrative')[0] + ' — illustrative slate')
        material['pbrMetallicRoughness']['baseColorFactor'] = ([.22,.075,.008,1] if nerve else [.075,.09,.105,1])
    for node in result['nodes']:
        name = node['extras']['source_object']
        node['name'] = name
        node['extras'] = {'source_object':name, 'role':'nerve' if name == NAMES[0] else 'native bone context',
                          'scope':'Source-native gross elbow relationship; unaltered evaluated source surface'}
    result['scenes'][0]['name'] = 'Right ulnar nerve and elbow bones — regional teaching supplement'
    result['scenes'][0]['extras'] = {
        'assetId':'peripheral_nerves_ulnar_elbow_z', 'variantId':'native-ulnar-elbow-r01-v2',
        'relatedHistoricalAssetId':'draft_peripheral_nerves', 'sourceBlendSha256':SOURCE_SHA,
        'license':'CC BY-SA 4.0',
        'attribution':'Z-Anatomy — The libre 3D atlas of anatomy — CC BY-SA 4.0; BodyParts3D — The Database Center for Life Science — CC BY-SA 2.1 Japan (historical attribution)',
        'sourceAuthors':'Kousaku Okubo (BodyParts3D); Gauthier Kervyn (Z-Anatomy design, 3D, anatomy); Marcin Zielinski (Blender add-on)',
        'scope':'Right ulnar nerve relative to three native elbow bones; illustrative colors, static source pose.',
        'limitations':'Exposed source nerve endpoints; coarse source bone form and retained source topology defects. No skin, muscle, retinaculum or modeled cubital tunnel. No complete nerve route, physical-scale validation, patient registration, motion, clinical or runtime approval. Separate supplement, not an old-scaffold replacement.'}
    encoded = json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(struct.pack('<4sII', b'glTF', 2, 20+len(encoded)+len(rest)) +
                       struct.pack('<II', len(encoded), 0x4e4f534a) + encoded + rest)
    return {'inputSha256':BASELINE_SHA, 'outputSha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'bytes':output.stat().st_size, 'preservedBinarySha256':hashlib.sha256(rest).hexdigest()}

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--input', required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(build(a.input,a.output),indent=2))
