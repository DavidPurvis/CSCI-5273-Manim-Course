# Current preparation status

Run `./kitchen audit` before rendering. The prepared timelines and caption checks currently pass; current findings are written to `build/audit.json`. Numeric and source checks do not imply perceptual review. Production progress is in `build/production-progress.json`.

# Chef's Sheet

The build is complete and automatically checked; human review still gates release. One command cooks the whole course. You never choose a tool, find a source, or write narration.

Open a terminal in this folder (`source/`) and run:

```bash
./kitchen run
```

It checks the kitchen, cooks whatever changed, tastes each dish, assembles the chapters, and serves the course. Chapters are assembled as soon as their dishes pass the automatic checks. Runtime depends on hardware and changed inputs; completed current receipts are reused. The final media-built message still requires explicit review and `./kitchen verify-release`. The normal command renders from an isolated source snapshot.

Then:

| Command | What it does |
|---|---|
| `./kitchen open` | Starts the study player |
| `./kitchen review` | Shows every cooked dish on one page, changed dishes first, with a box for notes to prep |

## If it stops

`run` names the dish and the problem. Fix it, then run it again. Finished dishes aren't redone.

| You see | You do |
|---|---|
| A label overlaps, sits on a link, or leaves the frame | Correct its layout in the authoritative overrides or authoring, preserving the minimum font size; prepare and check again |
| "animation needs Xs" or "moves overrun" | Correct authored cue order, occurrence or setup time; do not speed up motion to bypass a conflict |
| A mispronounced word or a wrong number | **Stop and report it** in `./kitchen review` |
| "unknown move", missing audio, or a missing trace | **Stop and report it** |
| "only N GiB free" | **Stop and report it** |
| A crash you can't explain | **Stop and report it**, with the printed message |

Layout adjustments belong in `sources/layout-overrides.yaml`, keyed by the full beat ID. Run `./kitchen prepare` after changing them. Do not edit generated recipe cards. The value for each beat uses this structure:

```yaml
1.1.question:
  nudge:
    _q: [0.0, 0.1]

```

To redo one dish by hand: `./kitchen cook 2.3 --final`, then `./kitchen taste 2.3`.

## Where things end up

```
../player/                                 the study player
../video/CSCI-5273-Lectures-06-15.mp4      the full course, with markers and captions
../video/chapters/  ../video/dishes/       one MP4 per chapter and per dish
../captions/  ../transcript/               captions, and the transcript with PDF pages
../README.md  ../final-report.json         viewing guide and final checks
```
