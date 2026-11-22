"""Select the context that One Breath renders beside its separately loaded trachea."""

from tools.glb import decode, encode
from tools.glb_selection import select


def build_companion(raw, asset):
    doc, _ = decode(raw)
    nodes = [node for node in doc['nodes'] if 'mesh' in node]
    retained = [node['name'] for node in nodes if node['extras']['lessonRegion'] != 'V7']
    if not retained or len(retained) == len(nodes):
        raise ValueError('Expected both the airway context and its embedded V7 cutaway')

    result, _ = select(raw, {
        'source': asset['source'],
        'sha256': asset['sourceSha256'],
        'file': asset['file'],
        'title': 'One Breath airway context',
        'scope': 'Nasal passage, larynx, route guides, left lobar branch and enlarged terminal inset.',
        'retain': retained,
    })
    output, binary = decode(result)
    # The older portable export carries scene extras inherited from its source imports.
    output['scenes'][0]['extras'] = {
        'coordinates': 'glTF metres, +X patient left, +Y superior, +Z anterior.',
        'scope': 'Authored airway context in the original display frame. Terminal inset enlarged.',
    }
    return encode(output, binary)
