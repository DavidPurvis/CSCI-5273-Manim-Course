# Study player design system

Source of truth: `course/player/tokens.css` (values), `course/player/style.css` (components), `course/player/player.js` (markup and behaviour), `course/tests/test_player_design.py` (guards). The palette mirrors `course/stage/theme.py`.

Revamped 2026-11-01. The audit and the before-and-after numbers are at the end.

## Principles

1. **Tokens before values.** Components read roles such as `--color-action`, never palette names or raw numbers.
2. **Variants are classes; state is semantic.** `.btn--primary` is a variant. `aria-pressed`, `aria-current`, `aria-selected`, `aria-invalid`, `data-state`, `data-result` and `data-level` carry state, so the CSS and the screen reader read the same thing.
3. **One palette, shared with the videos.** The nine mirrored colours are the course palette. Changing one changes `theme.py`, which changes the videos too.
4. **Touch first.** Controls and list rows are 44px on touch screens. Inline text links keep the 24px WCAG minimum.
5. **Document what exists.** A component that is not in this file is not part of the system.

## Tokens

### Palette (mirrors `course/stage/theme.py`)

| Token | Value | Role | Mirrors |
|---|---|---|---|
| `--blue` | #4A9EFF | links, focus | `LAYER["ip"]` |
| `--orange` | #FF8A3D | primary action, current selection | `STATE["now"]` |
| `--green` | #4CD07D | success | `STATE["done"]` |
| `--red` | #FF5A5A | danger | `STATE["error"]` |
| `--grey` | #6B7588 | control borders | `STATE["idle"]` |
| `--ink` | #F2F4F8 | primary text | `INK` |
| `--ink-muted` | #A9B3C4 | secondary text | `MUTED` |
| `--page` | #11141B | page background | `BG` |
| `--card` | #1B2029 | card surface | `PANEL` |

UI-only neutrals, not in `theme.py` because the videos never draw them: `--raised`, `--divider`, `--track`, `--black`, `--paper`, `--scrim`.

`LAYER["eth"]` (yellow) is deliberately unused. In the videos it names the Ethernet layer, and a UI warning colour would borrow that meaning.

### Roles

`--color-page`, `--color-surface`, `--color-surface-raised`, `--color-divider`, `--color-track`, `--color-border`, `--color-text`, `--color-text-muted`, `--color-text-on-action`, `--color-link`, `--color-focus`, `--color-action`, `--color-success`, `--color-danger`, `--color-video`, `--color-slide`, `--color-scrim`.

### Scales

- **Type:** 13 / 14 / 16 / 19 / 22 / 26 px (`--text-xs` to `--text-2xl`). Body 16px at 1.5 line height.
- **Space:** 4 / 8 / 12 / 16 / 20 / 24 / 32 / 48 px (`--space-1` to `--space-12`).
- **Radius:** 4 / 6 / 8 / 12 px, plus pill (`--radius-sm` to `--radius-pill`).
- **Control height:** 40px, or 44px on touch screens (`--control-height`, `--target-min`).
- **Layout:** measure 760px for reading, 1320px for wide views. Top bar 56px, or 100px on phones (`--topbar-height`).
- **Motion:** 120ms fast, 200ms base, one standard easing. Off under `prefers-reduced-motion`.

## Components

### Button: `.btn`

- **Use:** every clickable action. Works on `<button>` and `<a>`.
- **Variants:** default (secondary); `.btn--primary` (one per view); `.btn--success` (confirm a right answer); `.btn--danger` (destructive, or a wrong answer); `.btn--ghost` (inline text action).
- **States:** hover (border to ink; primary and success brighten); focus-visible (2px blue ring); active (1px press); disabled (`disabled` or `aria-disabled="true"`, 45% opacity, no pointer); pressed (`aria-pressed="true"`, orange border and text).
- **Accessibility:** native `<button>`; toggles announce through `aria-pressed`.

```html
<button type="button" class="btn btn--primary">Start</button>
<button type="button" class="btn" aria-pressed="true">Full route</button>
```

### Segmented control: `.segmented`

- **Use:** choosing one of a few options: route, playback speed, Slide/Transcript tabs.
- **Markup:** buttons with `.btn`. A toggle group uses `aria-pressed`. Tabs use `role="tab"` and `aria-selected` inside `role="tablist"`.

### Card: `.card`

- **Variants:** `.card--feature` (the one next thing, orange border); `.card--link` (the whole card is a link, with a hover lift).
- **Surface:** card colour, 12px radius, 20px padding.

### Notice: `.notice`

- **Use:** a statement that frames the view, such as a disclaimer or a countdown. Blue edge by default.
- **Variant:** `.notice--danger` for errors. Add `role="alert"` only for errors that appear after an action.

### Fields: `input`, `select`, `textarea`, `.field`, `.form-grid`

- **Use:** labels sit above controls in `.field`. Borders use `--color-border`, which is 3:1 against the page and the raised surface.
- **Feedback:** `data-result="right"` or `"wrong"` on the control, plus `aria-invalid="true"` when wrong.
- **Compact:** `.select--compact` for inline selects.

### Checkbox: `.check`

- **Use:** a label that wraps a native checkbox. The 20px box has a green accent, and the whole label is the target.

### Tag: `.tag`

- **Use:** a short label, or an inline link.
- **Variants:** `.tag--success`, `.tag--danger`. Minimum height 24px.

### Progress: `.progress` and `.progress__fill`

- **Markup:** `role="progressbar"` with `aria-valuenow` and `aria-valuemax`. The fill width comes from the `--value` custom property.
- **Rule:** the bar is decorative beside its number. The number carries the value.

### Task row: `.task-list` > `.task`

- **Lessons** (dish boxes) are links with a tick mark.
- **Tasks** (on paper, stop check, midterm, readiness) are checkboxes, so they can be ticked in any order.
- **State:** `data-state="done"` or `"todo"`. Both kinds share one left edge.

### Transcript line: `.line`

- **Markup:** one `<button>` per line, so it is keyboard reachable.
- **State:** `aria-current="true"` on the line being spoken.

### Timer: `.timer`

- **Markup:** tabular numerals. `data-level="low"` turns it danger-red in the last five minutes.

### Dialog: `dialog.dialog`

- **Use:** any choice that discards or locks work.
- **Build:** `confirmFirst()` in `player.js`. Title, one sentence of consequence, Cancel, and an action whose tone matches the risk.
- **Behaviour:** native `<dialog>`, so focus stays inside and Escape closes it.
- **Rule:** no `alert()` or `confirm()`. Import errors and load errors use a notice.

### Top bar: `.topbar`, `.topbar__nav`

- **Contents:** brand, section links (`aria-current="page"` on the current one), and the score.
- **Phones:** brand and score share row one. Sections scroll sideways on row two.

### Prompt: `.prompt`

- **Use:** the pause-and-predict overlay inside the video frame.
- **Style:** scrim colour, 22px text, one button.

### Empty and error states: `.empty-state`, `.notice--danger`

- **Empty:** centred muted text, for "nothing here yet" or "nothing matches".
- **Error:** a danger notice.

### Question, answer, feedback: `.question`, `.answer`, `.feedback`

- **Question:** 19px text.
- **Answer:** block with a green edge.
- **Feedback:** coloured by `data-result`.

## Patterns

- **Home:** midterm notice, then route (segmented control plus one line saying what it covers), then the next-up card, then one progress bar with one line of counts, then the schedule (day groups of task rows), then export and import.
- **Test out:** one card, two actions. Try two questions is primary; Just watch is secondary.
- **Watch:** page head with one primary action (Finish and check me), the video with a speed group and captions, and a side panel with Slide and Transcript tabs.
- **Drills:** link cards with a solved-count tag. Fields in a grid, a feedback line, and steps revealed on demand.
- **Midterm:** a notice on the start screen, then a sticky toolbar with the timer and Finish. Finish and Start over both go through the dialog.
- **Readiness:** a card per criterion. The checkbox comes first, and the links sit indented under it.

## Accessibility rules

- Every view has one `h1`, which takes focus on navigation.
- The current section is announced through `aria-current`.
- Text contrast is at least 4.5:1. Control borders and focus rings are at least 3:1. Tests enforce both.
- No state is carried by colour alone: states have text, such as "Right." or "Not yet.", or an ARIA attribute.
- Touch targets are 44px on touch screens. Inline text links are at least 24px.

## Naming rules

- **Block, element, modifier:** `.card`, `.task__label`, `.btn--primary`.
- **Layout helpers:** `.cluster` (wrapping row), `.spread`, `.stack` (vertical rhythm), `.measure` (line length).
- **Text:** `.text-muted`, `.text-sm`.
- **Inline styles:** none, except dynamic values such as the progress width.

## Migration from the previous system

| Before | After |
|---|---|
| `.top`, `.top nav` | `.topbar`, `.topbar__nav` |
| `.row` | `.cluster` |
| `.narrow` | `.measure` |
| `.muted`, `.small` | `.text-muted`, `.text-sm` |
| `button.primary`, `.good`, `.bad`, `.link` | `.btn--primary`, `.btn--success`, `.btn--danger`, `.btn--ghost` |
| `.on` on buttons, nav and transcript | `aria-pressed`, `aria-current`, `aria-selected` |
| `.card.next` | `.card--feature` |
| `.boxes` | `.task-list` |
| `.stats`, `.stat` | `.progress-summary`, `.stat-row` |
| `.bar` | `.progress` |
| `.stagebox`, `.missing` | `.video-frame`, `.empty-state` |
| `.overlay` | `.prompt` |
| `.side`, `.tabs` | `.side-panel`, `.segmented` |
| `.transcript p` | `.transcript .line` (a button) |
| `.hit` | `.result` |
| `.fields` | `.form-grid` |
| `.ready` | `.check` inside `.card` |
| `.right`, `.wrong` | `data-result`, `aria-invalid` |
| `.tag.good`, `.tag.bad` | `.tag--success`, `.tag--danger` |
| `.timer.low` | `.timer[data-level="low"]` |

Progress data is unchanged. The localStorage key is still `csci5273-player-v1`, so existing progress carries over.

## Governance

- **Palette change:** change `course/stage/theme.py` first, which also changes the videos and means re-rendering them. Then change the matching value in `tokens.css`. `test_player_design.py` fails until both agree.
- **Player-only colour:** change `tokens.css` only.
- **New component:** add a section here with its variants, states, accessibility and a markup example. Add a contrast pair to the tests if it introduces colour.
- **Served copy:** the server runs from a copy of `course/player`. After editing, run `python -m course.tools.player_build` from `source/` (with `.venv`). Reload the page.

## Not in this revamp

- **Video palette and stage components** (`course/stage/`): unchanged. The rendered videos depend on them.
- **Design tool:** no design file is connected, so this system lives in code and this document.

## Audit, 2026-11-01

| Measure | Before | After |
|---|---|---|
| Raw colours in component CSS | 7 (`#2B3240` ×3, `#11141B` ×2, `#000`, `#fff`, one `rgba`) | 0 (test) |
| Colour tokens | 11, one unused (`--eth`) | 9 mirrored, 17 roles, UI neutrals; `--eth` reserved |
| Font sizes | 6 values, unnamed | 6 named steps |
| Inline styles in `player.js` | 16 | 1 (dynamic progress width) |
| Native dialogs | 3 (`alert` ×1, `confirm` ×2) | 0 (test) |
| ARIA state attributes | 5 (`aria-label` ×4, `aria-live` ×1) | 14 uses of `aria-pressed`, `aria-current`, `aria-selected`, `aria-invalid` |
| Click handler on a non-focusable element | 1 (transcript `<p>`) | 0 |
| Text pairs below 4.5:1 | 0 of 13 | 0 (test) |
| Control-border pairs below 3:1 | 1 (button border, 2.52:1) | 0 (test) |
| Sticky offset | hard-coded `top: 52px` | `var(--topbar-height)` |
| Phone touch targets | 24 to 32px | 44px |
| Phone top bar | nav wraps to three rows | two rows, nav scrolls |
| Component documentation | none | this file |
