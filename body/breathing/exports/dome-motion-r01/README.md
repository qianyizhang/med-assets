# Diaphragm, lungs and liver motion

Open [Breathing_Dome.blend](Breathing_Dome.blend) at frame 1 and compare it with peak inspiration at frame 49. The five lobes, open schematic diaphragm and liver retain their original shapes, editable tracks and source placement. The [full assembly](../../Breathing_Assembly.blend) supplies the other moving organs and the broader respiratory context.

The [matched phase view](../../../../reviews/teaching-assessments/target-risk/views/breath.webp) isolates the dome crest and compares the lung bases and liver. The selected seven meshes retain 93,502 triangles. Position samples of every retained vertex agree with the full assembly in each of its 121 integer frames. The view represents authored gross motion. Projected overlaps and modeled open edges leave attachments and measured physiology outside the exercise.

[Historical review and comparison](../../../../reviews/teaching-assessments/target-risk/README.md) · [Breathing recipe and attribution](../../README.md)

## Rebuild

Use the hydrated full assembly and reviewed scene with Blender 5.2.3 LTS Release Candidate `fab76e95306d`. The replay checks all seven retained meshes against the full assembly and the reviewed scene at all 121 integer frames. Its acceptance is the decoded motion and timeline, with a 0.0001 mm world-position tolerance.

```sh
blender --background --factory-startup --disable-autoexec --threads 6 --python-exit-code 1 \
  --python body/breathing/recipes/dome-motion-r01/build.py -- .artifacts/rebuild-breathing-dome
```
