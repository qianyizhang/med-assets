# Acquired comparisons for the worked visits

[references.json](references.json) pairs each abnormal modeled visit with an acquired image or clip from an independently documented exam. Each record names the source, media URL, credit, license and local file identity. The comparison illustrates one finding from the visit. Its measurements and interpretation belong to the published exam.

The `identity` records keep the published files unchanged. `sourceSha256` identifies the bytes at `sourceMedia` and `sha256` identifies the stored files. The media files are tracked through Git LFS. Noncommercial terms apply where the record's license requires them. The [POCUS Atlas license](https://www.thepocusatlas.com/legal) covers both original clips and the poster adaptations.

## Replay

Fetch a record's `sourceMedia` into a fresh scratch directory. Verify its SHA-256 against `sourceSha256`. For identity records the result also matches the stored file's `sha256`.

The nuchal translucency comparison isolates panel E from a larger figure under CC BY 4.0. Replay the recorded `crop` with FFmpeg 8.1 and compare `sha256`.

```sh
ffmpeg -v error -i original.webp -vf 'crop=394:290:6:298' -frames:v 1 -q:v 2 -threads 1 comparison.jpg
```

For a clip poster, substitute the record's zero-based `posterFrame` for `FRAME` and compare `posterSha256`. The poster retains the clip's attribution and CC BY-NC 4.0 terms.

```sh
ffmpeg -v error -i original.gif -vf 'select=eq(n\,FRAME)' -frames:v 1 -q:v 2 -threads 1 poster.jpg
```
