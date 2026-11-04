> Scope: these are the prior generic storytelling experiments, not the actual-asset treatment-procedure prototype. Retention and reproducibility decisions are in README.md and results/manifest.json.

# One script, three creative treatments

Three actual 48-second narrated films, not just style descriptions. Each uses exactly the same frozen narration/music master and the same six clinical beats. All three exports are 1280×720, 30 fps, and 1,440 frames. Illustrations and scene code were independently authored for these prototypes.

## How to watch

Watch the individual films first. The synchronized three-panel overview is useful for comparing shot choices and pacing, but its reduced panels are not suitable for judging small text. The aligned storyboard samples each treatment at the same times.

1. **HyperFrames / Before the hole**: stronger visual hook and contrast between macro scenes and light explanatory scenes. A dimensional tooth leads into a plaque factory, mineral exchange, cavity threshold, assessment and prevention. Especially useful for an engaging short motion-graphics explainer.
2. **Remotion / The Decay File**: warm editorial dioramas, clear cause-and-effect chain, treatment decision map, full narration captions and a compact prevention recap. Especially useful for a repeatable patient-education series with editable components.
3. **Original 3b1b ManimGL / The Mineral Ledger**: a continuous spatial journey built from native geometry. Repeated mineral tiles and particles make loss, recovery and surface breakdown explicit. Especially useful when the central goal is explaining a mechanism, rather than decorative cinematic detail.

These are observations about these authored versions. They do not establish that one engine inherently tells better stories, or that installing a skill alone improves a film. The creative brief, narration, illustration decisions and revision passes all matter.

## What is controlled

- Same six beats: 0–6, 6–14, 14–23, 23–31, 31–40, 40–48 seconds.
- Same exact source WAV, SHA-256 `e3b3c974ccdf5ceaf2e2ae72f71a6981e84dbe592cd3735014a9ccc659a4e6c4`.
- Same resolution, frame rate and core educational claims.
- Different shot design, graphics, transitions, typography and caption strategy by intent.

The voice is local Kokoro-82M v1.0 `af_heart` synthesis, not a cloned person or a clinician recording. The score was procedurally composed for this project without third-party music samples. No paid service was used. Timing/encoding/loudness were checked programmatically; direct listening review remains outstanding.

## Actual tools and skills

- HyperFrames 0.9.8 + GSAP 3.14.2, native HTML/SVG timeline. Official skill references: https://github.com/heygen-com/hyperframes/tree/main/skills
- Remotion 4.0.540 + React 19.1.0, frame-driven React/SVG composition. Official skills: https://www.remotion.dev/docs/ai/skills
- ManimGL 1.7.2, the original 3b1b project, not Manim Community Edition. Native geometry/text rendered through ModernGL EGL. Official engine: https://github.com/3b1b/manim . A community skill was read for narration-first workflow and engine distinctions: https://github.com/do-gongil/manimgl-skill/blob/main/skills/manimgl-video/SKILL.md . No unreviewed helper scripts from that skill were run.

The design-style repository was a visual reference only. No videos, cover art, style assets or code were copied. Its gallery code license should not be mistaken for blanket rights to its media: https://github.com/guanmo-ai/design-style

## Workflow friction and limits

- HyperFrames rendered successfully with its managed browser and software GPU. The workspace's system browser had local-socket restrictions. Lint recommended separating the six-shot composition into smaller subcompositions. Those maintainability warnings are not a failed render. Final text/contrast/leader-line fixes were verified in decoded frames, not falsely reported as a new zero-warning lint run.
- Remotion needed a process-local loopback adapter because this container blocks network-interface enumeration. It does not alter system networking or security settings. Its renderer itself is unchanged.
- ManimGL required native Cairo/Pango and a working EGL backend. Native fill-opacity behavior and one label placement were corrected after rendered-frame review. The last nine-second label correction was rendered natively, joined to unchanged native footage, then re-encoded. The included final scene code can render the complete corrected film directly.
- Technical checks do not establish clinical accuracy. These are schematic 2D/2.5D illustrations, not validated tooth anatomy, a molecular simulation or a procedure guide. A dental reviewer and a human listening pass are needed before patient-facing publication.
- Remotion licensing depends on organization/use. Review https://www.remotion.dev/docs/license/pricing . Dependencies retain their own licenses. HyperFrames and Kokoro source/model references are in the individual READMEs; bundled font notices are preserved.

## Clinical sources

Original paraphrase based on NIDCR:
- https://www.nidcr.nih.gov/health-info/tooth-decay
- https://www.nidcr.nih.gov/health-info/tooth-decay/more-info/tooth-decay-process

The story separates early mineral loss from a formed cavity. It shows assessment before treatment and identifies a filling as one common option, not the required treatment for every lesion. There is no operative instruction or promise of success.

## Useful judging questions

- Which opening makes you want to keep watching?
- Which version makes the loss-versus-repair idea easiest to understand?
- Do the props clarify the story, or compete with the voice?
- Which visual language should become a reusable system for future topics?
