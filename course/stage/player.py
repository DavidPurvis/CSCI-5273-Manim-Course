"""Plays one recipe card, beat by beat. Set KITCHEN_DISH to the dish id."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
from manim import AnimationGroup, FadeOut, LEFT, RIGHT, Scene, Succession, VGroup, linear

from course.stage.card import beat_times, load_card, load_manifest, load_timing, narration_text, phrase_time, timed_cues, word_times
from course.stage.context import last_sentence, lesson_question, step_name
from course.stage.moves import REGISTRY, Stage, resolve
from course.stage.parts import Net, T
from course.stage.signal import FLASH, find as find_signals, flash, spoken_words
from course.stage.theme import BG, FRAME_X, FRAME_Y, FULL_HEIGHT_LESSONS, MIN_FONT, MUTED, STATE, ZONES, use_full_height

# A narrated frame may sit unchanged this long. Prediction and reading holds use idle(), not this splitter.
IDLE_LIMIT = 20.0


def idle_slices(seconds, limit=IDLE_LIMIT, pulse=FLASH):
    """Break a long idle into waits no longer than limit, with a pulse between them."""
    return [("wait", seconds)] if seconds > 0 else []


def keep_live(mobjects, live):
    """Drop what the stage no longer owns. A temporary animation group is dropped but what's inside it stays, in place."""
    out, seen = [], set()

    def visit(mob):
        if id(mob) in live:
            if id(mob) not in seen:
                seen.add(id(mob))
                out.append(mob)
            return
        for part in mob.submobjects:
            visit(part)
    for mob in mobjects:
        visit(mob)
    return out


class Dish(Scene):
    def construct(self):
        self.camera.background_color = BG
        dish = os.environ["KITCHEN_DISH"]
        self.snap_dir = os.environ.get("KITCHEN_SNAP")
        self.fps = 30
        card = load_card(dish)
        self.card_pad = card.get("pad", 2.2)
        manifest = load_manifest()
        self.timing = load_timing()
        texts = narration_text()
        from course.stage.timeline import compile_dish
        compile_dish(card,manifest,self.timing,texts,{k:v['t'] for k,v in REGISTRY.items()})
        times, total = beat_times(card, manifest)
        self.stage_ = Stage(self)
        self.card_ = card
        self.strip_on = dish not in FULL_HEIGHT_LESSONS
        if not self.strip_on:
            use_full_height()
        problems = []
        self.moving = []
        for beat, slot in zip(card["beats"], times):
            self.beat_start = slot["start"]
            problems += self.play_beat(beat, slot, manifest, texts)
            problems += self.lint(beat["id"])
            if self.snap_dir:
                self.snapshot(beat["id"])
        if hasattr(self.renderer, "file_writer") and getattr(self.renderer.file_writer, "includes_sound", False):
            from pydub import AudioSegment
            self.renderer.file_writer.add_audio_segment(AudioSegment.silent(50), time=max(0, total - 0.05))
        out = Path(os.environ.get("KITCHEN_BUILD", ROOT / "build")) / "lint"
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{dish}.json").write_text(json.dumps({"dish": dish, "problems": problems, "duration": total, "moving": self.moving}))

    # Frame-exact durations keep audio aligned however many animations a dish has.
    def anim_time(self, t):
        return (max(1, round(t * self.fps)) - 0.01) / self.fps

    def wait_time(self, t):
        return (round(t * self.fps) + 0.01) / self.fps

    def idle(self, t):
        if round(t * self.fps) >= 1:
            self.wait(self.wait_time(t))

    def idle_keep(self, t, now):
        """Break a long idle with a corner-tag pulse so narration is not left on a frozen frame."""
        self.idle(t)
        return now + t

    def idle_at(self, now, t):
        """Wait t seconds from time now in the beat, lighting up whatever the narration names meanwhile."""
        if not self.words or round(t * self.fps) < round(FLASH * self.fps):
            self.idle_keep(t, now)
            return
        total, pos = round(t * self.fps), 0
        need = round(FLASH * self.fps)
        for at, mob in find_signals(self.words, now, now + t, self.stage_, self.signalled):
            start = round((at - now) * self.fps)
            if start < pos or start + need > total:
                continue
            self.idle_keep((start - pos) / self.fps, now + pos / self.fps)
            self.play(flash(mob, self.stage_), run_time=self.anim_time(need / self.fps))
            self.prune()
            self.moving.append((self.beat_start + now + start / self.fps, self.beat_start + now + (start + need) / self.fps))
            pos = start + need
        self.idle_keep((total - pos) / self.fps, now + pos / self.fps)

    def set_tag(self, beat):
        """A small corner tag names the instructor slide behind this beat."""
        deck, *pages = beat["pdf"]
        x0, y0, x1, y1 = ZONES["title"]
        tag = T(f"Lecture {int(deck[3:5])} · p. {pages[0]}", 24, MUTED)
        tag.set_y((y0 + y1) / 2)
        tag.align_to(np.array([x1 - 0.2, 0, 0]), RIGHT)
        old = self.stage_.objs.get("_tag")
        if old is not None:
            self.remove(old)
        self.stage_.objs["_tag"] = tag
        self.stage_.zone_of["_tag"] = None
        self.add(tag)

    def set_context(self, beat):
        """The strip under the title says which question this lesson is answering and which step this beat is."""
        x0, y0, x1, y1 = ZONES["context"]
        step = T(step_name(beat["stage"]), 24, STATE["now"])
        step.set_y((y0 + y1) / 2)
        step.align_to(np.array([x1 - 0.2, 0, 0]), RIGHT)
        strip = VGroup(step)
        question = lesson_question(self.card_)
        # While the question beat is asking it on the big stage, the strip doesn't repeat it.
        if question and beat["stage"] != "question":
            room = step.get_left()[0] - 0.3 - (x0 + 0.2)
            for form in (question, last_sentence(question)):
                text = T(form, 24, MUTED)
                if text.width <= room:
                    text.set_y((y0 + y1) / 2)
                    text.align_to(np.array([x0 + 0.2, 0, 0]), LEFT)
                    strip.add(text)
                    break
        old = self.stage_.objs.get("_context")
        if old is not None:
            self.remove(old)
        self.stage_.objs["_context"] = strip
        self.stage_.zone_of["_context"] = None
        self.add(strip)

    def play_beat(self, beat, slot, manifest, texts):
        problems = []
        self.set_tag(beat)
        if self.strip_on:
            self.set_context(beat)
        adj = beat.get("adjust") or {}
        self.stage_.adjust = adj
        pace = adj.get("pace", 1.0)
        speech, total = slot["speech"], slot["total"]
        entry = manifest.get(beat["id"])
        measured = word_times(beat["id"], manifest, self.timing)
        self.words = spoken_words(texts.get(beat["id"], ""), measured) if measured else []
        self.signalled = {}
        if beat["stage"] == "prediction" or beat.get("reading_hold"):
            self.words = []
        from course.stage.timeline import compile_beat
        schedule = compile_beat(beat, entry, measured, texts.get(beat["id"], ""), self.card_pad,
                                defaults={k:v['t'] for k,v in REGISTRY.items()})
        self.words = [(word, at + schedule.speech[0]/30, sentence_start) for word, at, sentence_start in self.words]
        if entry:
            self.add_sound(str(ROOT / entry["wav"]), time_offset=schedule.speech[0]/30)
            for cue in schedule.captions:
                self.add_subcaption(cue['text'], duration=(cue['end']-cue['start'])/30, offset=cue['start']/30)
        moves = []
        for raw in beat.get("moves") or []:
            name = next(k for k in raw if k not in ("when", "t", "event_id"))
            args = dict(raw[name] or {})
            for extra in ("when", "t"):
                if extra in raw:
                    args[extra] = raw[extra]
            if name not in REGISTRY:
                problems.append(f"{beat['id']}: unknown move {name}")
                continue
            when = args.pop("when", None)
            args.pop("occurrence", None)
            args.pop("t", None)
            run = schedule.moves[len(moves)]["frames"] / self.fps
            moves.append((name, args, when, run))
        busy = sum(m[3] for m in moves)
        budget = total - slot["hold"]
        if busy > budget + 1e-3:
            problems.append(f"{beat['id']}: animation needs {busy:.1f}s but narration allows {budget:.1f}s; lower pace or add hold")
        spoken = texts.get(beat["id"], "")
        targets = [m["start"] / 30 for m in schedule.moves]
        now = 0.0
        for i, (name, args, when, run) in enumerate(moves):
            wait = max(0, schedule.moves[i]['start'] / 30 - now)
            targets[i] = schedule.moves[i]['start'] / 30
            # Wait first: a move changes the stage as soon as it's called, so calling it early would show its result early.
            if targets[i] is not None and wait:
                self.idle_at(now, wait)
                now += round(wait * self.fps) / self.fps
            self.stage_.move_run = run
            try:
                anims = REGISTRY[name]["fn"](self.stage_, **resolve(args))
            except Exception as exc:
                problems.append(f"{beat['id']}: {name} failed: {exc}")
                raise
            if anims:
                fades = [a for a in anims if isinstance(a, FadeOut)]
                rest = [a for a in anims if not isinstance(a, FadeOut)]
                if fades and rest:
                    # Old leaves before new arrives, so text never sits on top of text. Total time is unchanged.
                    out = min(0.4, run / 2)
                    anims = [Succession(AnimationGroup(*fades, run_time=out), AnimationGroup(*rest, run_time=run - out))]
                self.play(*anims, run_time=self.anim_time(run))
                self.moving.append((self.beat_start + now, self.beat_start + now + run))
                now += round(run * self.fps) / self.fps
                self.prune()
                problems += self.lint(beat["id"] + ":" + schedule.moves[i]["event_id"])
                from course.stage.moves import observe_stage, check_stage
                assertions = [a for a in beat.get('assertions', []) if a.get('after') == schedule.moves[i]['event_id']]
                problems += [f.message for f in check_stage(observe_stage(self.stage_), assertions)]
            if targets[i] is None and wait:
                self.idle_at(now, wait)
                now += round(wait * self.fps) / self.fps
        fade_room = 0.2 if slot["hold"] and self.stage_.pause_bar is not None else 0
        remaining = total - now - slot["hold"] - fade_room
        if remaining < -0.02:
            problems.append(f"{beat['id']}: moves overrun the beat by {-remaining:.1f}s; lower pace or add hold")
        self.idle(max(0, remaining)) if beat.get("reading_hold") or beat["stage"] == "prediction" else self.idle_at(now, max(0, remaining))
        now += max(0, remaining)
        if slot["hold"]:
            bar = self.stage_.pause_bar
            if bar is not None:
                self.moving.append((self.beat_start + now, self.beat_start + now + slot["hold"]))
                length = T(f"Pause: {slot['hold']:g} s", 24, MUTED)
                _, y0, x1, y1 = ZONES["rule"]
                length.set_y((y0 + y1) / 2)
                length.align_to(np.array([x1 - 0.25, 0, 0]), RIGHT)
                self.add(length)
                self.play(bar.animate.stretch(0.002, 0, about_edge=np.array([-1, 0, 0])), run_time=self.anim_time(slot["hold"]), rate_func=linear)
                self.stage_.pause_bar = None
                self.play(*self.stage_.drop("_rule"), FadeOut(length), run_time=self.anim_time(0.2))
                self.prune()
            else:
                self.idle(slot["hold"])
        return problems

    def prune(self):
        """Anything no longer owned by the stage leaves the scene, so removed objects can't linger."""
        live = set()
        for mob in list(self.stage_.objs.values()) + list(self.stage_.marks.values()):
            live.update(id(m) for m in mob.get_family())
        self.mobjects[:] = keep_live(self.mobjects, live)

    def lint(self, beat_id):
        problems, boxes = [], []
        seen = set()
        for mob in self.mobjects:
            for sub in mob.get_family():
                if id(sub) in seen or not hasattr(sub, "kfont") or sub.get_num_points() == 0 and not sub.submobjects:
                    continue
                seen.add(id(sub))
                eff = sub.kfont * sub.height / max(sub.kheight, 1e-6)
                if eff < MIN_FONT - 0.6:
                    problems.append(f"{beat_id}: label '{getattr(sub, 'text', '?')}' is {eff:.0f} pt, under the {MIN_FONT} pt minimum")
                if abs(sub.get_x()) + sub.width / 2 > FRAME_X or abs(sub.get_y()) + sub.height / 2 > FRAME_Y:
                    problems.append(f"{beat_id}: label '{getattr(sub, 'text', '?')}' leaves the frame")
                boxes.append((sub, getattr(sub, "text", "?")))
        for mob in self.stage_.objs.values():
            if getattr(mob, "layout_overflow", None):
                problems.append(f"{beat_id}: {mob.layout_overflow}")
            if isinstance(mob, Net):
                labels = [d.label for d in mob.devices.values() if d.label is not None] + list(mob.badges.values())
                problems += [f"{beat_id}: label '{m.text}' sits on a link" for m in labels if mob.on_link(m)]
        for i, (a, ta) in enumerate(boxes):
            for b, tb in boxes[i + 1:]:
                dx = abs(a.get_x() - b.get_x()) - (a.width + b.width) / 2
                dy = abs(a.get_y() - b.get_y()) - (a.height + b.height) / 2
                if dx < -0.03 and dy < -0.03:
                    problems.append(f"{beat_id}: labels overlap: '{ta}' and '{tb}'")
        problems += self.band_problems(beat_id)
        return problems

    def band_problems(self, beat_id):
        """Title, source tag, and the takeaway must not meet each other or the diagram."""
        def span(mob):
            try:
                pts = np.asarray(mob.get_all_points())
            except (ValueError, IndexError):
                return None
            if pts.ndim != 2 or pts.shape[0] == 0 or pts.shape[1] < 2:
                return None
            return pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max()

        def hit(a, b):
            sa, sb = span(a), span(b)
            if sa is None or sb is None:
                return False
            dx = abs((sa[0] + sa[1]) / 2 - (sb[0] + sb[1]) / 2) - (sa[1] - sa[0] + sb[1] - sb[0]) / 2
            dy = abs((sa[2] + sa[3]) / 2 - (sb[2] + sb[3]) / 2) - (sa[3] - sa[2] + sb[3] - sb[2]) / 2
            return dx < -0.04 and dy < -0.04

        objs = self.stage_.objs
        title = [objs[n] for n in ("_heading", "_tag") if n in objs]
        rule = [objs[n] for n in ("_rule",) if n in objs]
        diagram = [m for n, m in objs.items() if n not in ("_heading", "_tag", "_rule")]
        problems = []
        if len(title) == 2 and hit(title[0], title[1]):
            problems.append(f"{beat_id}: title and source tag overlap")
        for band, label in ((title, "title band"), (rule, "rule band")):
            for mob in band:
                if any(hit(mob, other) for other in diagram):
                    problems.append(f"{beat_id}: {label} intersects the diagram")
                    break
        return problems

    def snapshot(self, beat_id):
        self.renderer.update_frame(self, ignore_skipping=True)
        image = self.renderer.camera.get_image()
        path = Path(self.snap_dir) / f"{beat_id}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
