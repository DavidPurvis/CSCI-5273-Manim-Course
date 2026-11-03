# Rebuild the supplied source

Run these commands from the unpacked `source/` directory. The environment is deliberately excluded from the source archive.

```bash
uv venv --python 3.12 .venv
uv pip sync requirements.lock --python .venv/bin/python
./kitchen audit
./kitchen check
```

Manim is pinned to Community 0.22.1 and uses Cairo. On macOS, the official installation guide calls for Cairo and pkg-config; install only missing prerequisites. This course also uses the existing FFmpeg, Poppler and LaTeX/dvisvgm tools. Cached narration is supplied; generating new narration uses the Mac's Samantha voice.

```bash
brew install cairo pkg-config ffmpeg poppler
```

If LaTeX is absent, follow the MacTeX installation path in the [official Manim installation guide](https://docs.manim.community/en/stable/installation/uv.html). The guide lists packages for a smaller TeX installation as well. This course requires formula rendering, so LaTeX/dvisvgm must be available.

Render one segment at 720p/30 fps, then at 1080p/30 fps:

```bash
./kitchen cook 1.1 --preview
./kitchen taste 1.1
./kitchen cook 1.1 --final
./kitchen taste 1.1
```

Render and assemble the full course sequentially:

```bash
./kitchen run
./kitchen open
```

The default `run` checks inputs and works from a source snapshot. It reuses current successful render receipts and assembles each chapter when its dishes pass. A stage or narration change requires affected scenes to render again. Export-only changes require assembly again.

Render just the Foundations chapter from the packaged source (its two dishes), with final settings:

```bash
(
  set -e
  for dish in 1.1 1.2; do
    ./kitchen cook "$dish" --final
    ./kitchen taste "$dish"
  done
  ./kitchen plate 1
)
```

For another chapter, use its exact dish IDs from docs/04-SCENE-RECIPES.md. For a quick visual preview, use `--preview` for those dishes; chapter assembly requires their final renders.

For a chapter whose dishes have already rendered:

```bash
./kitchen plate 1
```

For an independent reproduction using the supplied narration assets:

```bash
uv venv --python 3.12 build/reproduction/.venv
uv pip sync requirements.lock --python build/reproduction/.venv/bin/python
.venv/bin/python -m course.tools.reproduction
```

This copies source into an isolated directory, runs tests in the second environment, and renders 1.1 and 3.4 sequentially. Results go to `build/reproduction/report.json`.

Use `./kitchen prepare --vault /path/to/vault` only when intentionally taking a new source snapshot. Normal renders and the study player use packaged sources. Change authoring YAML, curated teaching bindings, pronunciation or layout overrides; prepare generates recipes and narration Markdown. Audits and checks do not rewrite authoritative inputs.

After production, `./kitchen review` records explicit content, visual, audio and caption reviews. `./kitchen verify-release` checks current media and evidence. A successful render or a saved note does not pass those reviews.

## Updating narration and timing

Unchanged course assets need no speech model. The package includes raw cached transcription evidence bound to the supplied WAV hashes, so existing alignments can be rebuilt with the main environment:

```bash
.venv/bin/python -m course.tools.ears
```

To synthesize changed narration with Samantha:

```bash
.venv/bin/python -m course.tools.tts
```

New audio needs a new transcription. On the Apple Silicon authoring Mac, create the separate optional speech environment:

```bash
uv venv --python 3.12 .venv-speech
uv pip sync requirements-speech.lock --python .venv-speech/bin/python
.venv-speech/bin/python -m course.tools.ears
./kitchen prepare
./kitchen audit
```

The first uncached transcription downloads the configured `mlx-community/whisper-small.en-mlx` model. Cached evidence is accepted only for matching audio bytes and aligner identity. ASR differences remain review findings; agreement does not pass perceptual audio review.

## Words used in this kitchen

- **Dish:** one lesson segment, such as 1.1.
- **Cook:** render a dish. `--preview` makes a quick 720p check; `--final` makes the 1080p file.
- **Taste:** check a rendered dish with the automatic checks.
- **Plate:** assemble a chapter from its finished dishes.

## Hand off the deliverables

After `./kitchen run` and the media audit and reproduction, refresh the shared status, write the source ZIP, record the test and release evidence, then intentionally build the handoff folder. `verify-release` exits non-zero while reviews are pending; it still writes the evidence the next step needs:

```bash
.venv/bin/python -c "from course.tools.release_status import refresh; refresh()"
.venv/bin/python -m course.tools.package
.venv/bin/python -m pytest course/tests -q | tee ../verification/tests.log
./kitchen verify-release
.venv/bin/python -m course.tools.deliverables
.venv/bin/python -m course.tools.handoff
```

The handoff folder is written next to the course folder as `CSCI-5273-Manim-Course-handoff`. It holds the videos, captions, transcript, study player, README, final report, evidence and the source ZIP. It leaves out the virtual environments, `build/` and the working `source/` tree.

## Standalone playback (delivered handoff)

The delivered folder needs Python 3.10 or later and a web browser. Playback uses
only the Python standard library. On macOS, double-click `Play Course.command`,
or run these commands from the delivered folder:

```bash
python3 play.py --check
python3 play.py
```

`play.py`, `local_server.py`, `player/`, `video/`, `captions/`, `notes/`, and
`decks/` travel together. Notes, figures, and instructor PDFs are bundled from
the frozen snapshot. Non-vault provenance records such as `review.txt` and
`vault-source-manifest.json` remain preserved in the source ZIP. Vault records
are hash-validated as bundled notes; all explicitly required PDFs, including
`lec02-layering.pdf`, are copied to `decks/`. The launcher validates referenced assets and the recorded
SHA-256 hashes before opening the player; validation can take time for large
videos. It listens on `127.0.0.1` only. If port 5273 is busy, it chooses a free
port and prints the actual URL. Keep the Terminal window open during playback;
Control-C stops the server. Optional arguments: `--no-browser`, `--port 0`
(always choose a free port), and `--root /path/to/delivered-folder`.

`setup.sh` installs the rendering environment; it is unnecessary for playback.
To validate an already delivered folder from the authoring source, run
`python3 -m course.tools.playback --root /path/to/delivered-folder --check`.

Handoff consumes the shared status written by `course.tools.release_status.refresh()`.
The source status, verification status, final report's `release_status`, and the
status inside the source ZIP must agree, including their revision. Refresh the
status and regenerate the source ZIP before intentionally creating a handoff.
Handoff preserves pending review findings; packaging does not grant release approval.

Handoff construction uses a temporary sibling directory. It copies deliverables,
installs the launcher and resources, records their hashes in `playback-assets.json`
and `verification/deliverables-manifest.json`, validates assets and ZIP integrity,
and only then promotes the staged folder. An existing destination is retained as
`<destination>.previous-<unique-id>`; failed promotion restores it. Each rename is
atomic, but replacement takes two renames and the destination may briefly be
absent. Copy or validation failure leaves the previous destination untouched and
removes the incomplete staging folder. Existing previous folders remain available
for manual recovery.
