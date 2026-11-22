#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { constants } from 'node:fs';
import { link, mkdir, mkdtemp, open, realpath, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { promisify } from 'node:util';
import { brotliDecompress } from 'node:zlib';
import bindings from './projection-bindings.json' with { type: 'json' };

const review = 'reviews/trachea/2026-10-29-open-airway-r06';
const source = path.dirname(fileURLToPath(import.meta.url));
const decompress = promisify(brotliDecompress);
const { files } = bindings;

async function readRegular(file, limit) {
  const handle = await open(file, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
  try {
    const info = await handle.stat();
    if (!info.isFile() || !info.size || info.size > limit) throw Error('Invalid file size or type: ' + file);
    const buffer = Buffer.alloc(info.size + 1);
    const { bytesRead } = await handle.read(buffer);
    if (bytesRead !== info.size) throw Error('File changed during read: ' + file);
    return buffer.subarray(0, bytesRead);
  } finally {
    await handle.close();
  }
}

function check(bytes, entry) {
  if (bytes.length !== entry.bytes || createHash('sha256').update(bytes).digest('hex') !== entry.sha256) {
    throw Error('Projection differs from its reviewed SHA-256 or size: ' + entry.file);
  }
  return bytes;
}

async function unpack(entry) {
  if (await realpath(source) !== source) throw Error('Projection storage traverses a link.');
  const packed = await readRegular(path.join(source, entry.file + '.br'), 1_000_000);
  return check(await decompress(packed, { maxOutputLength: entry.bytes }), entry);
}

export async function readRetainedProjection(relative, asset) {
  const entry = files.find(({ file }) => review + '/' + file === relative);
  if (!entry || entry.bytes !== asset.bytes || entry.sha256 !== asset.sha256) return null;
  // Loopback delivery uses the ordinary unavailable response for malformed or missing storage.
  return unpack(entry).catch(() => null);
}

async function restore(outputRoot) {
  const decoded = await Promise.all(files.map(unpack));
  let directory = await realpath(outputRoot);
  for (const part of review.split('/')) {
    directory = path.join(directory, part);
    await mkdir(directory).catch((error) => {
      if (error.code !== 'EEXIST') throw error;
    });
    if (await realpath(directory) !== directory) throw Error('Restore path traverses a link: ' + directory);
  }

  const missing = [];
  for (const [index, entry] of files.entries()) {
    const target = path.join(directory, entry.file);
    try {
      check(await readRegular(target, entry.bytes), entry);
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
      missing.push({ target, bytes: decoded[index] });
    }
  }

  if (missing.length) {
    const work = await mkdtemp(path.join(directory, '.restore-'));
    try {
      for (const { target, bytes } of missing) {
        const temporary = path.join(work, path.basename(target));
        await writeFile(temporary, bytes, { flag: 'wx' });
        await link(temporary, target);
      }
    } finally {
      await rm(work, { recursive: true, force: true });
    }
  }
  for (const { file } of files) console.log(path.join(directory, file));
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const args = process.argv.slice(2);
  if (args.length !== 2 || args[0] !== '--output') {
    console.error('Usage: node restore-projections.mjs --output EXISTING_ROOT');
    process.exitCode = 1;
  } else {
    try {
      await restore(path.resolve(args[1]));
    } catch (error) {
      console.error('Projection restore refused: ' + error.message);
      process.exitCode = 1;
    }
  }
}
