// Attach the source view to an opaque WebP produced by this renderer's canvas.
export async function identifyPoster(blob, width, height, source, renderer) {
  const encoder = new TextEncoder();
  const xml = (value) =>
    value
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('"', '&quot;')
      .replaceAll('>', '&gt;');
  const xmp = encoder.encode(
    '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:xmp="http://ns.adobe.com/xap/1.0/" dc:source="' +
      xml(source) +
      '" xmp:CreatorTool="' +
      xml(renderer) +
      '"/></rdf:RDF></x:xmpmeta>',
  );
  const bytes = new Uint8Array(await blob.arrayBuffer());
  const tag = (offset) => String.fromCharCode(...bytes.subarray(offset, offset + 4));
  if (tag(0) !== 'RIFF' || tag(8) !== 'WEBP') throw Error('Unexpected poster format.');
  const extended = tag(12) === 'VP8X';
  const extra = extended ? 0 : 18;
  const output = new Uint8Array(bytes.length + extra + 8 + xmp.length + (xmp.length % 2));
  const view = new DataView(output.buffer);
  output.set(bytes.subarray(0, 12));
  output.set(bytes.subarray(12), 12 + extra);
  if (!extended) {
    output.set(encoder.encode('VP8X'), 12);
    view.setUint32(16, 10, true);
    for (let i = 0; i < 3; i++) {
      output[24 + i] = (width - 1) >>> (8 * i);
      output[27 + i] = (height - 1) >>> (8 * i);
    }
  }
  output[20] |= 4;
  const pos = bytes.length + extra;
  output.set(encoder.encode('XMP '), pos);
  view.setUint32(pos + 4, xmp.length, true);
  output.set(xmp, pos + 8);
  view.setUint32(4, output.length - 8, true);
  return new Blob([output], { type: 'image/webp' });
}
