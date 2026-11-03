"use strict";
// The study player: one box at a time. All networking math was done ahead of time by tested models; this page only compares answers.

const KEY = "csci5273-player-brian-v1";
const LEGACY_KEY = "csci5273-player-v1";
let pendingProgress = null;
const MIDTERM_SECONDS = 75 * 60;
const CAUSES = ["Wrong scope", "Wrong table", "Wrong unit", "Wrong order", "Stale information", "Confused role"];
let D = null;       // course data
let S = null;       // saved progress
let cleanup = null; // stops the current view's timers and loops

function defaults() {
  return { route: "full", done: {}, tested: {}, q: {}, right: 0, completed: 0, speed: 1, captions: true, pos: {}, midterm: {}, drills: {}, ready: {} };
}
function load() {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(KEY) || localStorage.getItem(LEGACY_KEY)) || {}; } catch (e) { saved = {}; }
  S = Object.assign(defaults(), saved);
  if (Object.keys(saved).length && !saved.courseVersion) pendingProgress = saved;
}
function save() {
  if (pendingProgress) return;
  if (D) S.courseVersion = D.courseVersion;
  try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* progress lasts only for this visit */ }
  renderScore();
}

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, "");
    else if (v !== false && v != null) el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid != null && kid !== false) el.append(kid);
  }
  return el;
}
function fill(el, ...kids) {
  el.replaceChildren(...kids.flat().filter(k => k != null && k !== false));
}
function show(...kids) {
  fill(document.getElementById("app"), ...kids);
  window.scrollTo(0, 0);
  // Focus the view's title so keyboard and screen-reader users start at the top of new content.
  const title = document.querySelector("#app h1");
  if (title) { title.tabIndex = -1; title.focus({ preventScroll: true }); }
}
function go(hash) {
  if (location.hash === hash) route(); else location.hash = hash;
}
// Replaces the browser's native prompts: an in-page dialog with a clear action and a way out.
function confirmFirst({ title, body, action, tone, onConfirm }) {
  const dialog = h("dialog", { class: "dialog", "aria-labelledby": "dialog-title" },
    h("h2", { id: "dialog-title" }, title),
    h("p", { class: "text-muted" }, body),
    h("div", { class: "cluster spread" },
      h("button", { type: "button", class: "btn", onclick: () => dialog.close() }, "Cancel"),
      h("button", { type: "button", class: `btn btn--${tone}`, onclick: () => { dialog.close(); onConfirm(); } }, action)));
  dialog.addEventListener("close", () => dialog.remove());
  document.body.append(dialog);
  dialog.showModal();
}
function progressBar(done, total, label) {
  const pct = total ? (100 * done) / total : 0;
  return h("div", { class: "progress", role: "progressbar", "aria-label": label, "aria-valuemin": "0", "aria-valuemax": String(total), "aria-valuenow": String(done) },
    h("span", { class: "progress__fill", style: `--value:${pct}%` }));
}

// Questions and review --------------------------------------------------------
function itemsForDish(id) {
  return D.bank.filter(i => i.kind !== "midterm" && i.dishes.includes(id));
}
function hardFirst(items) {
  const rank = { "Application / Worked problem": 0, "Critical thinking": 1, "Understanding / Comparison": 2 };
  return [...items].sort((a, b) => (rank[a.section] ?? 3) - (rank[b.section] ?? 3) || (a.kind === "cue" ? 0 : 1) - (b.kind === "cue" ? 0 : 1) || a.id.localeCompare(b.id));
}
function pretestFor(id) {
  return hardFirst(itemsForDish(id)).slice(0, 2);
}
function checkFor(id) {
  const used = new Set(pretestFor(id).map(i => i.id));
  const rest = itemsForDish(id).filter(i => !used.has(i.id));
  const fresh = rest.filter(i => !(S.q[i.id] && S.q[i.id].box > 0));
  const pool = fresh.length >= 3 ? fresh : rest.length >= 3 ? rest : itemsForDish(id);
  return [...pool].sort((a, b) => (a.kind === "cue" ? 0 : 1) - (b.kind === "cue" ? 0 : 1) || a.id.localeCompare(b.id)).slice(0, 5);
}
function mark(item, gotIt) {
  const q = S.q[item.id] || { box: 0, tries: 0 };
  q.tries += 1;
  if (gotIt) {
    q.box = Math.min((q.box || 0) + 1, 2);
    q.due = q.box >= 2 ? null : S.completed + 5;
    S.right += 1;
  } else {
    q.box = 0;
    q.due = S.completed + 2;
  }
  S.q[item.id] = q;
  save();
}
function dueReviews() {
  return D.bank.filter(i => {
    const q = S.q[i.id];
    return i.kind !== "midterm" && q && q.tries && q.box < 2 && q.due != null && q.due <= S.completed;
  });
}

function questionCard(item, onDone, label) {
  const box = h("section", { class: "card stack" });
  const reveal = () => {
    box.replaceChildren(
      h("div", { class: "eyebrow" }, label || ""),
      h("div", { class: "question" }, item.q),
      h("div", { class: "answer" }, item.a),
      h("div", { class: "cluster" },
        h("button", { type: "button", class: "btn btn--success", onclick: () => { mark(item, true); onDone(true); } }, "Got it"),
        h("button", { type: "button", class: "btn btn--danger", onclick: () => { mark(item, false); onDone(false); } }, "Missed it")));
  };
  box.append(
    h("div", { class: "eyebrow" }, label || ""),
    h("div", { class: "question" }, item.q),
    h("p", { class: "text-muted text-sm" }, "Answer it in your head or on paper first."),
    h("button", { type: "button", class: "btn btn--primary", onclick: reveal }, "Show the answer"));
  return box;
}
function runQuestions(items, title, finish) {
  let i = 0, right = 0;
  const step = () => {
    if (i >= items.length) return finish(right);
    show(h("div", { class: "measure" }, h("h1", {}, title), questionCard(items[i], ok => { right += ok ? 1 : 0; i += 1; step(); }, `Question ${i + 1} of ${items.length}`)));
  };
  step();
}

// The route -------------------------------------------------------------------
function boxKey(box) { return `${box.kind}:${box.id}`; }
function routeBoxes() {
  const all = D.route.flatMap(day => day.boxes.map(b => Object.assign({ day: day.day }, b)));
  if (S.route === "express") return all.filter(b => b.kind !== "dish" ? b.kind === "midterm" : D.express.includes(b.id));
  return all;
}
function isDone(box) { return !!S.done[boxKey(box)]; }
function nextBox() { return routeBoxes().find(b => !isDone(b)) || null; }
function complete(box) {
  S.done[boxKey(box)] = true;
  S.completed += 1;
  save();
}
function setDone(box, on) {
  if (on) complete(box);
  else { delete S.done[boxKey(box)]; save(); }
}
function daysLeft() {
  if (!D.examDate) return null;
  const ms = new Date(D.examDate + "T00:00:00") - new Date();
  if (!Number.isFinite(ms)) return null;
  return Math.ceil(ms / 86400000);
}
function boxTitle(b) {
  if (b.kind === "dish") return `${b.id} ${D.dishes[b.id].title}`;
  return b.text;
}
function kindLabel(box) {
  if (box.kind === "midterm") return "Midterm";
  if (box.kind === "ready") return "Readiness";
  return box.kind === "stop" ? "Stop check" : "On paper";
}
// A lesson is a link with a tick. A task is a checkbox, so it can be ticked in any order.
function taskRow(b) {
  const done = isDone(b);
  const state = done ? "done" : "todo";
  if (b.kind === "dish") {
    return h("li", { class: "task", "data-state": state },
      h("span", { class: "task__mark", "aria-hidden": "true" }, done ? "✓" : ""),
      h("a", { href: `#dish/${b.id}/watch` }, boxTitle(b)));
  }
  return h("li", { class: "task", "data-state": state },
    h("label", { class: "task__label" },
      h("input", { type: "checkbox", checked: done, onchange: e => { setDone(b, e.target.checked); viewHome(); } }),
      h("span", { class: "task__text" }, boxTitle(b)),
      h("span", { class: "tag" }, kindLabel(b))));
}

function viewHome() {
  const next = nextBox();
  const due = dueReviews();
  let main;
  if (due.length) {
    main = h("section", { class: "card card--feature" },
      h("div", { class: "eyebrow" }, "Before the next box"),
      h("h1", {}, `Review ${Math.min(due.length, 5)} question${due.length === 1 ? "" : "s"} you missed`),
      h("a", { class: "btn btn--primary", href: "#review" }, "Start review"));
  } else if (!next) {
    main = h("section", { class: "card card--feature" }, h("h1", {}, "Every box is done."), h("p", { class: "text-muted" }, "Use drills and the readiness board for whatever still feels shaky."));
  } else if (next.kind === "dish") {
    const dish = D.dishes[next.id];
    main = h("section", { class: "card card--feature" },
      h("div", { class: "eyebrow" }, `${next.day} · ${dish.chapterTitle} · ${dish.minutes} min`),
      h("h1", {}, `${next.id} ${dish.title}`),
      h("a", { class: "btn btn--primary", href: `#dish/${next.id}` }, "Start"));
  } else if (next.kind === "midterm") {
    main = h("section", { class: "card card--feature" },
      h("div", { class: "eyebrow" }, next.day),
      h("h1", {}, next.text),
      h("a", { class: "btn btn--primary", href: "#midterm" }, "Open practice midterm"));
  } else if (next.kind === "ready") {
    main = h("section", { class: "card card--feature" },
      h("div", { class: "eyebrow" }, next.day),
      h("h1", {}, next.text),
      h("div", { class: "cluster" },
        h("a", { class: "btn btn--primary", href: "#ready" }, "Open readiness board"),
        h("button", { type: "button", class: "btn", onclick: () => { complete(next); viewHome(); } }, "Done")));
  } else {
    main = h("section", { class: "card card--feature" },
      h("div", { class: "eyebrow" }, `${next.day} · ${kindLabel(next)}`),
      h("h1", {}, next.text),
      h("div", { class: "cluster" },
        next.note ? h("a", { class: "btn", href: next.note }, "Open in the vault") : null,
        h("button", { type: "button", class: "btn btn--primary", onclick: () => { complete(next); viewHome(); } }, "Done")));
  }
  const all = routeBoxes();
  const doneCount = all.filter(isDone).length;
  const days = [...new Set(all.map(b => b.day))].map(day => {
    const boxes = all.filter(b => b.day === day);
    const done = boxes.filter(isDone).length;
    return h("details", { class: "day", open: next && next.day === day },
      h("summary", { class: "day__summary" }, h("b", {}, day), ` · ${done} of ${boxes.length}`),
      progressBar(done, boxes.length, `${day} progress`),
      h("ul", { class: "task-list" }, boxes.map(taskRow)));
  });
  const solved = Object.values(S.drills).filter(x => x.right).length;
  const concepts = D.bank.filter(i => i.kind === "cue" && S.q[i.id] && S.q[i.id].box > 0).length;
  const left = daysLeft();
  const status = h("div", { role: "status" });
  show(
    h("section", { class: "notice" },
      h("p", {}, left === null ? "Study at your own pace." : left > 0 ? `Midterm in ${left} day${left === 1 ? "" : "s"}.` : left === 0 ? "Midterm day." : "Continue your review.", " These are study explanations and generated practice, not an official exam outline.")),
    h("div", { class: "stack" },
      h("div", { class: "segmented", role: "group", "aria-label": "Route" },
        h("button", { type: "button", class: "btn", "aria-pressed": String(S.route === "full"), onclick: () => { S.route = "full"; save(); viewHome(); } }, "Full route"),
        h("button", { type: "button", class: "btn", "aria-pressed": String(S.route === "express"), onclick: () => { S.route = "express"; save(); viewHome(); } }, "Express route")),
      h("p", { class: "text-sm text-muted" }, S.route === "express" ? "Express: only the express dishes and the midterm." : "Full: every dish and task, in order.")),
    main,
    h("section", { class: "card progress-summary", "aria-label": "Your progress" },
      h("div", { class: "progress-summary__title" }, `${doneCount} of ${all.length} boxes done`),
      progressBar(doneCount, all.length, "Boxes done"),
      h("p", { class: "stat-row" },
        h("span", {}, h("b", {}, S.right), " questions right"),
        h("span", {}, h("b", {}, `${concepts}/176`), " concepts checked"),
        h("span", {}, h("b", {}, `${solved}/${D.drills.length}`), " drills solved"))),
    h("section", { class: "card" }, days),
    h("div", { class: "cluster text-sm" },
      h("button", { type: "button", class: "btn btn--ghost", onclick: exportProgress }, "Export progress"),
      h("label", { class: "btn btn--ghost" }, "Import progress",
        h("input", { type: "file", accept: "application/json", class: "sr-only", onchange: e => importProgress(e, status) }))),
    status);
}
function exportProgress() {
  const a = h("a", { href: URL.createObjectURL(new Blob([JSON.stringify(S, null, 1)], { type: "application/json" })), download: "csci5273-progress.json" });
  document.body.append(a); a.click(); a.remove();
}
// An export holds these saved fields with these shapes. Any other JSON must not replace progress.
function isProgressExport(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const base = defaults();
  if (!("route" in value) || !("done" in value)) return false;
  return Object.keys(base).every(key => {
    if (!(key in value) || base[key] === null) return true;
    const want = base[key], got = value[key];
    if (typeof want !== "object") return typeof got === typeof want;
    return got !== null && typeof got === "object" && Array.isArray(got) === Array.isArray(want);
  });
}
function importProgress(event, status) {
  const input = event.target;
  const file = input.files[0];
  if (!file) return;
  const reject = () => fill(status, h("div", { class: "notice notice--danger", role: "alert" }, "That file isn't a progress export."));
  file.text().then(text => {
    input.value = "";
    let imported;
    try { imported = JSON.parse(text); } catch (e) { return reject(); }
    if (!isProgressExport(imported)) return reject();
    confirmFirst({
      title: "Replace your progress?",
      body: "This replaces the progress saved in this browser with the imported file.",
      action: "Replace progress",
      tone: "danger",
      onConfirm: () => {
        S = Object.assign(defaults(), imported);
        if (!imported.courseVersion) { pendingProgress = imported; migrationView(); }
        else { if (imported.courseVersion !== D.courseVersion) S.pos = {}; save(); route(); }
      },
    });
  });
}

function viewReview() {
  const due = dueReviews().slice(0, 5);
  if (!due.length) return go("#home");
  runQuestions(due, "Review", () => go("#home"));
}

// A dish: test out, watch, check ----------------------------------------------
function viewDish(id, step, at) {
  const dish = D.dishes[id];
  if (!dish) return go("#home");
  const box = { kind: "dish", id };
  if (step === "watch") return viewWatch(dish, at);
  if (step === "check") return viewCheck(dish, box);
  const test = pretestFor(id);
  if (isDone(box) || !test.length) return viewWatch(dish, at);
  show(h("div", { class: "measure" },
    h("div", { class: "eyebrow" }, `${dish.chapterTitle} · ${dish.minutes} min`),
    h("h1", {}, `${id} ${dish.title}`),
    h("section", { class: "card" },
      h("h2", {}, "Test out?"),
      h("p", { class: "text-muted" }, "Two hard questions on this dish. Get both and you can skip it."),
      h("div", { class: "cluster" },
        h("button", { type: "button", class: "btn btn--primary", onclick: () => runTest(dish, test, box) }, "Try two questions"),
        h("a", { class: "btn", href: `#dish/${id}/watch` }, "Just watch")))));
}
function runTest(dish, test, box) {
  runQuestions(test, `${dish.id}: test out`, right => {
    if (right < test.length) return go(`#dish/${dish.id}/watch`);
    show(h("div", { class: "measure" }, h("section", { class: "card card--feature" },
      h("h1", {}, "You got both."),
      h("p", { class: "text-muted" }, "You can skip this lesson, or watch it anyway."),
      h("div", { class: "cluster" },
        h("button", { type: "button", class: "btn btn--primary", onclick: () => { S.tested[dish.id] = true; complete(box); go("#home"); } }, "Skip it"),
        h("a", { class: "btn", href: `#dish/${dish.id}/watch` }, "Watch anyway")))));
  });
}
function viewCheck(dish, box) {
  const items = checkFor(dish.id);
  const finish = right => {
    if (!isDone(box)) complete(box);
    show(h("div", { class: "measure" }, h("section", { class: "card card--feature" },
      h("h1", {}, `${right} of ${items.length} right.`),
      h("p", { class: "text-muted" }, right < items.length ? "Anything you missed comes back in a little while." : "Nice. On to the next box."),
      h("div", { class: "cluster" },
        h("a", { class: "btn btn--primary", href: "#home" }, "Next up"),
        h("a", { class: "btn", href: `#dish/${dish.id}/watch` }, "Watch again")))));
  };
  if (!items.length) return finish(0);
  runQuestions(items, `${dish.id}: check`, finish);
}

function beatIndexAt(dish, t) {
  let i = 0;
  while (i + 1 < dish.beats.length && dish.beats[i + 1].t <= t + 0.01) i += 1;
  return i;
}
function viewWatch(dish, startAt) {
  const pdfLink = beat => `/decks/${beat.deck}#page=${beat.pages[0]}`;
  const slideImg = h("img", { alt: "Instructor slide for this part of the dish" });
  const slideLink = h("a", { target: "_blank", rel: "noopener", class: "text-sm" });
  const conceptTags = h("div", { class: "cluster text-sm" });
  const transcript = h("div", { class: "transcript" });
  const lines = dish.beats.map(b => h("button", { type: "button", class: "line", onclick: () => seekTo(b.t) }, b.text));
  transcript.append(...lines);
  const slidePane = h("div", { class: "stack", role: "tabpanel", id: "pane-slide", "aria-labelledby": "tab-slide" }, slideImg, h("p", { class: "text-sm" }, slideLink), conceptTags);
  const transPane = h("div", { role: "tabpanel", id: "pane-text", "aria-labelledby": "tab-text", hidden: true }, transcript);
  const tabSlide = h("button", { type: "button", class: "btn", role: "tab", id: "tab-slide", "aria-controls": "pane-slide", "aria-selected": "true", onclick: () => pick(true) }, "Slide");
  const tabText = h("button", { type: "button", class: "btn", role: "tab", id: "tab-text", "aria-controls": "pane-text", "aria-selected": "false", onclick: () => pick(false) }, "Transcript");
  function pick(slide) {
    tabSlide.tabIndex = slide ? 0 : -1; tabText.tabIndex = slide ? -1 : 0;
    slidePane.hidden = !slide; transPane.hidden = slide;
    tabSlide.setAttribute("aria-selected", String(slide));
    tabText.setAttribute("aria-selected", String(!slide));
  }
  tabText.tabIndex = -1;
  for (const tab of [tabSlide,tabText]) tab.addEventListener("keydown",e=>{
    if (["ArrowLeft","ArrowRight","Home","End"].includes(e.key)) {
      e.preventDefault(); const slide=e.key==="Home" || (e.key!=="End" && tab===tabText);
      pick(slide); (slide?tabSlide:tabText).focus();
    }
  });
  let video = null, alive = true, current = -1;
  const passed = new Set();
  const stage = h("div", { class: "video-frame" });
  if (dish.cooked) {
    video = h("video", { controls: true, playsinline: true, preload: "metadata", src: dish.video },
      h("track", { kind: "captions", src: dish.vtt, srclang: "en", label: "English", default: true }));
    stage.append(video);
  } else {
    stage.append(h("div", { class: "empty-state" }, "This video is not in the pilot yet. Explore the transcript and slides, or check your understanding."));
    pick(false);
  }
  function seekTo(t) {
    if (video) { video.currentTime = t; video.play().catch(() => {}); }
    else showBeat(beatIndexAt(dish, t));
  }
  function showBeat(i) {
    if (i === current) return;
    current = i;
    const beat = dish.beats[i];
    slideImg.src = `/slides/${beat.slide}`;
    slideLink.href = pdfLink(beat);
    slideLink.textContent = `${beat.deck}, page ${beat.pages.join(", ")} ↗`;
    conceptTags.replaceChildren(...beat.concepts.map(c => h("a", { class: "tag", href: D.concepts[c] ? D.concepts[c].note : "#" }, c)));
    lines.forEach((el, k) => el.setAttribute("aria-current", String(k === i)));
    if (!transPane.hidden) lines[i].scrollIntoView({ block: "nearest" });
  }
  function pausePrompt(p) {
    video.pause();
    passed.add(p.t);
    const layer = h("div", { class: "prompt", role: "dialog", "aria-modal": "true", "aria-labelledby": "prompt-text" },
      h("div", { class: "eyebrow" }, "Pause and predict"),
      h("p", { id: "prompt-text" }, p.prompt),
      h("button", { type: "button", class: "btn btn--primary", id: "continue", onclick: () => { layer.remove(); video.focus(); video.currentTime = p.resume; video.play().catch(() => {}); } }, "Continue"));
    layer.addEventListener("keydown",e=>{
      if(e.key==="Tab") {e.preventDefault();layer.querySelector("button").focus();}
    });
    stage.append(layer);
    layer.querySelector("button").focus();
  }
  function tick() {
    if (!alive) return;
    if (video) {
      const t = video.currentTime;
      showBeat(beatIndexAt(dish, t));
      if (!video.paused) {
        const p = dish.pauses.find(x => !passed.has(x.t) && t >= x.t && t < x.resume);
        if (p) pausePrompt(p);
        S.pos[dish.id] = t;
      }
    }
    requestAnimationFrame(tick);
  }
  const speeds = [1, 1.25, 1.5, 1.75, 2].map(v => h("button", { type: "button", class: "btn", "data-speed": v, "aria-pressed": String(S.speed === v), onclick: () => {
    S.speed = v; save();
    if (video) video.playbackRate = v;
    speeds.forEach(b => b.setAttribute("aria-pressed", String(Number(b.dataset.speed) === v)));
  } }, `${v}×`));
  const capBtn = h("button", { type: "button", class: "btn", "aria-pressed": String(S.captions), onclick: () => {
    S.captions = !S.captions; save();
    capBtn.setAttribute("aria-pressed", String(S.captions));
    applyCaptions();
  } }, "Captions");
  function applyCaptions() {
    if (video && video.textTracks[0]) video.textTracks[0].mode = S.captions ? "showing" : "hidden";
  }
  const lessonIndex=D.order.indexOf(dish.id);
  const companion=h("details", {class:"side-panel stack",open:true},
    h("summary",{},"Slides and transcript"),
    h("div", { class: "segmented", role: "tablist", "aria-label": "Study material" }, tabSlide, tabText), slidePane, transPane);
  const watch=h("div",{class:"watch"});
  const focusButton=h("button",{class:"btn", "aria-pressed":"false",onclick:()=>{
    const focused=watch.classList.toggle("watch--focus");
    focusButton.setAttribute("aria-pressed",String(focused)); companion.hidden=focused;
  }},"Focus view");
  show(
    h("div", { class: "page-head" },
      h("div", {}, h("div", { class: "eyebrow" }, `${dish.chapterTitle} · ${dish.minutes} min`), h("h1", {}, `${dish.id} ${dish.title}`)),
      h("a", { class: "btn btn--primary", href: `#dish/${dish.id}/check` }, "Finish and check me")),
    watch);
  watch.append(h("div", {}, stage,
        h("div", { class: "cluster watch__controls" },
          h("div", { class: "segmented", role: "group", "aria-label": "Playback speed" }, speeds),
          capBtn, focusButton),
        h("nav",{class:"lesson-navigation", "aria-label":"Lesson navigation"},
          lessonIndex>0 ? h("a",{class:"btn",href:`#dish/${D.order[lessonIndex-1]}/watch`},"← Previous lesson") : null,
          h("a",{class:"btn btn--ghost",href:"#contents"},"All lectures"),
          lessonIndex<D.order.length-1 ? h("a",{class:"btn",href:`#dish/${D.order[lessonIndex+1]}/watch`},"Next lesson →") : null)),companion);
  showBeat(beatIndexAt(dish, startAt || 0));
  if (video) {
    video.addEventListener("loadedmetadata", () => {
      video.playbackRate = S.speed;
      applyCaptions();
      video.currentTime = startAt || S.pos[dish.id] || 0;
      video.play().catch(() => {});
    });
    video.addEventListener("ended", () => go(`#dish/${dish.id}/check`));
    video.addEventListener("seeking", () => {
      const t = video.currentTime;
      dish.pauses.forEach(p => { if (t < p.t) passed.delete(p.t); });
      const open = stage.querySelector(".prompt");
      if (open) open.remove();
    });
  }
  const keys = e => {
    if (!video || ["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
    if (e.code === "Space" && e.target.tagName !== "BUTTON") {
      e.preventDefault();
      const open = stage.querySelector(".prompt button");
      if (open) open.click(); else if (video.paused) video.play().catch(() => {}); else video.pause();
    }
    if (e.code === "Enter") { const open = stage.querySelector(".prompt button"); if (open && e.target !== open) open.click(); }
  };
  document.addEventListener("keydown", keys);
  cleanup = () => { alive = false; document.removeEventListener("keydown", keys); if (video) video.pause(); save(); };
  requestAnimationFrame(tick);
}

// Find -----------------------------------------------------------------------
function viewFind() {
  const input = h("input", { type: "search", placeholder: "Search 176 concepts and the whole transcript", "aria-label": "Search", autofocus: true, oninput: run });
  const results = h("div", {});
  function run() {
    const q = input.value.trim().toLowerCase();
    if (q.length < 2) {
      results.replaceChildren(h("p", { class: "empty-state" }, "Type a concept, protocol, or phrase."));
      return;
    }
    const concepts = Object.entries(D.concepts).filter(([name, c]) => name.toLowerCase().includes(q) || c.definition.toLowerCase().includes(q)).slice(0, 25);
    const beats = [];
    for (const id of D.order) {
      for (const b of D.dishes[id].beats) {
        if (b.text.toLowerCase().includes(q)) beats.push({ dish: id, b });
      }
    }
    fill(results,
      concepts.length ? h("section", { class: "card" }, h("h2", {}, `Concepts (${concepts.length})`), concepts.map(([name, c]) => h("div", { class: "result" },
        h("h3", {}, name), h("p", { class: "text-muted text-sm" }, `${c.lecture}. ${c.definition}`),
        h("div", { class: "cluster text-sm" },
          c.dish ? h("a", { href: `#dish/${c.dish}/watch/${c.t}` }, `Watch it in ${c.dish}`) : null,
          h("a", { href: c.note }, "Vault note"))))) : null,
      beats.length ? h("section", { class: "card" }, h("h2", {}, `In the transcript (${beats.length})`), beats.slice(0, 30).map(({ dish, b }) => h("div", { class: "result" },
        h("a", { href: `#dish/${dish}/watch/${b.t}` }, `${dish} ${D.dishes[dish].title}`),
        h("p", { class: "text-muted text-sm" }, snippet(b.text, q))))) : null,
      !concepts.length && !beats.length ? h("p", { class: "empty-state" }, "Nothing matches that.") : null);
  }
  show(h("div", { class: "measure" }, h("h1", {}, "Find anything"), h("div", { class: "search-field" }, input), results));
  run();
  input.focus();
}
function snippet(text, q) {
  const at = text.toLowerCase().indexOf(q);
  const start = Math.max(0, at - 70);
  return (start ? "…" : "") + text.slice(start, at + q.length + 90) + (at + q.length + 90 < text.length ? "…" : "");
}

// Practice midterm -----------------------------------------------------------
function midtermItems() {
  return D.bank.filter(i => i.kind === "midterm").sort((a, b) => a.n - b.n);
}
function fmtClock(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}
function viewMidterm() {
  const m = S.midterm;
  if (m.finishedAt) return viewMidtermMarks();
  if (!m.startedAt) {
    show(h("div", { class: "measure" },
      h("h1", {}, "Practice midterm"),
      h("section", { class: "notice" },
        h("p", {}, h("b", {}, "This is generated practice, not the instructor's exam or format."), " It covers Lectures 6–15 in 20 questions of 5 points each.")),
      h("section", { class: "card stack" },
        h("p", { class: "text-muted" }, "Suggested: 75 minutes, closed notes. Show arithmetic and state assumptions. The timer keeps running if you leave this page. The walkthrough videos stay locked until you finish."),
        h("button", { type: "button", class: "btn btn--primary", onclick: () => { S.midterm = { startedAt: Date.now(), answers: {}, marks: {} }; save(); viewMidterm(); } }, "Start the 75-minute timer"))));
    return;
  }
  const clock = h("div", { class: "timer" });
  const tick = () => {
    const left = MIDTERM_SECONDS - (Date.now() - S.midterm.startedAt) / 1000;
    clock.textContent = left > 0 ? fmtClock(left) : "Time";
    clock.dataset.level = left < 300 ? "low" : "normal";
  };
  tick();
  const timer = setInterval(tick, 1000);
  cleanup = () => clearInterval(timer);
  show(h("div", { class: "measure" },
    h("h1", {}, "Practice midterm"),
    h("div", { class: "toolbar card" }, clock,
      h("button", { type: "button", class: "btn btn--primary", onclick: () => confirmFirst({
        title: "Finish and mark your answers?",
        body: "Your answers stay saved. Marking shows the model answers next to yours.",
        action: "Finish and mark",
        tone: "primary",
        onConfirm: () => { S.midterm.finishedAt = Date.now(); save(); viewMidterm(); },
      }) }, "Finish and mark")),
    midtermItems().map(item => h("section", { class: "card stack" },
      h("div", { class: "eyebrow" }, `Question ${item.n} · ${item.lecture}`),
      h("h3", {}, item.title),
      h("p", {}, item.q),
      h("textarea", { "aria-label": `Answer to question ${item.n}`, oninput: e => { S.midterm.answers[item.n] = e.target.value; save(); } }, S.midterm.answers[item.n] || "")))));
}
function viewMidtermMarks() {
  const m = S.midterm;
  const total = () => midtermItems().reduce((sum, i) => sum + (m.marks[i.n] ? m.marks[i.n].points || 0 : 0), 0);
  const sum = h("div", { class: "timer" });
  const refresh = () => { sum.textContent = `${total()} / 100`; };
  refresh();
  show(h("div", { class: "measure" },
    h("h1", {}, "Mark your practice midterm"),
    h("p", { class: "text-muted" }, "Generated practice, not the instructor's exam. Equivalent correct reasoning earns credit. A right answer you can't defend is still a gap."),
    h("div", { class: "toolbar card" }, sum,
      h("button", { type: "button", class: "btn btn--danger", onclick: () => confirmFirst({
        title: "Clear this attempt and start over?",
        body: "Your answers and marks for this attempt are deleted.",
        action: "Start over",
        tone: "danger",
        onConfirm: () => { S.midterm = {}; save(); viewMidterm(); },
      }) }, "Start over")),
    midtermItems().map(item => {
      const mk = m.marks[item.n] || (m.marks[item.n] = {});
      const links = h("div", { class: "cluster text-sm" });
      const redo = () => {
        const missed = mk.points != null && mk.points < 5;
        links.replaceChildren(...[
          ...item.dishes.slice(0, 2).map(d => h("a", { href: `#dish/${d}/watch` }, `Watch ${d}`)),
          item.walkthrough && D.dishes[item.walkthrough] ? h("a", { href: `#dish/${item.walkthrough}/watch` }, "Walkthrough") : null,
          item.drill ? h("a", { href: `#drills/${item.drill}` }, "Drill with new numbers") : null].filter(Boolean));
        links.hidden = !missed;
        cause.hidden = !missed;
      };
      const cause = h("select", { "aria-label": `Why question ${item.n} went wrong`, onchange: e => { mk.cause = e.target.value; save(); } },
        h("option", { value: "" }, "What went wrong?"), CAUSES.map(c => h("option", { value: c, selected: mk.cause === c }, c)));
      const pts = h("select", { class: "select--compact", "aria-label": `Points for question ${item.n}`, onchange: e => { mk.points = Number(e.target.value); save(); refresh(); redo(); } },
        h("option", { value: "" }, "Points"), [5, 4, 3, 2, 1, 0].map(p => h("option", { value: p, selected: mk.points === p }, `${p} / 5`)));
      const card = h("section", { class: "card stack" },
        h("div", { class: "eyebrow" }, `Question ${item.n} · ${item.lecture}`), h("h3", {}, item.title), h("p", {}, item.q),
        h("p", { class: "text-muted text-sm" }, h("b", {}, "You wrote: "), m.answers[item.n] || "(blank)"),
        h("div", { class: "answer" }, item.a),
        pts, cause, links);
      redo();
      return card;
    })));
  save();
}

// Drills ---------------------------------------------------------------------
function viewDrills() {
  show(h("div", { class: "measure" },
    h("h1", {}, "Drills"),
    h("p", { class: "text-muted" }, "Fresh numbers, instant checks. Every answer was computed by the course's tested models."),
    D.drillTypes.map(t => {
      const items = D.drills.filter(p => p.type === t.key);
      const done = items.filter(p => S.drills[p.id] && S.drills[p.id].right).length;
      return h("a", { class: "card card--link", href: `#drills/${t.key}` },
        h("div", {}, h("h3", {}, t.title), h("span", { class: "text-muted text-sm" }, `Taught in dish ${t.dish}`)),
        h("span", { class: done ? "tag tag--success" : "tag" }, `${done} of ${items.length}`));
    })));
}
function normalize(text, answer) {
  let t = String(text).trim().toLowerCase().replace(/\s+/g, "");
  let a = String(answer).trim().toLowerCase().replace(/\s+/g, "");
  if (/^[+-]?\d+$/.test(a)) { t = t.replace(/,/g, "").replace(/^\+/, ""); a = a.replace(/^\+/, ""); }
  if (a.startsWith("/")) { t = t.replace(/^\//, ""); a = a.slice(1); }
  return [t, a];
}
function viewDrill(type, wantedId) {
  const info = D.drillTypes.find(t => t.key === type);
  if (!info) return go("#drills");
  const items = D.drills.filter(p => p.type === type);
  const problem = items.find(p => p.id === wantedId) || items.find(p => !(S.drills[p.id] && S.drills[p.id].right));
  if (!problem) {
    show(h("div", { class: "measure" }, h("h1", {}, info.title), h("section", { class: "card card--feature" }, h("h2", {}, `All ${items.length} solved.`),
      h("div", { class: "cluster" },
        h("button", { type: "button", class: "btn btn--primary", onclick: () => { items.forEach(p => delete S.drills[p.id]); save(); viewDrill(type); } }, "Start them again"),
        h("a", { class: "btn", href: "#drills" }, "Other drills")))));
    return;
  }
  const inputs = problem.fields.map(f => {
    const el = f.options
      ? h("select", {}, h("option", { value: "" }, "Choose"), f.options.map(o => h("option", { value: o }, o)))
      : h("input", { type: "text", autocomplete: "off", spellcheck: "false" });
    return { f, el };
  });
  const feedback = h("div", { class: "feedback", role: "status" });
  const after = h("div", { class: "cluster" });
  const form = h("form", { onsubmit: e => {
    e.preventDefault();
    let all = true;
    for (const { f, el } of inputs) {
      const [t, a] = normalize(el.value, f.answer);
      const ok = t === a;
      all = all && ok;
      el.dataset.result = ok ? "right" : "wrong";
      el.setAttribute("aria-invalid", String(!ok));
    }
    const rec = S.drills[problem.id] || { tries: 0 };
    rec.tries += 1;
    if (all) { rec.right = true; S.right += rec.tries === 1 ? 1 : 0; }
    S.drills[problem.id] = rec;
    save();
    feedback.dataset.result = all ? "right" : "wrong";
    fill(feedback, all ? h("b", {}, "Right.") : [h("b", {}, "Not yet."), " Red fields need another look."]);
    fill(after,
      h("button", { type: "button", class: "btn", onclick: () => reveal() }, "Show the steps"),
      all ? h("button", { class: "btn btn--primary", type: "button", onclick: () => viewDrill(type) }, "Next problem") : null);
    if (all) reveal();
  } },
    h("div", { class: "form-grid" }, inputs.map(({ f, el }) => h("label", { class: "field" }, f.label, el))),
    h("div", { class: "cluster" }, h("button", { class: "btn btn--primary", type: "submit" }, "Check")));
  const stepsBox = h("div", { class: "stack" });
  function reveal() {
    stepsBox.replaceChildren(
      h("ol", { class: "steps" }, problem.steps.map(s => h("li", {}, s))),
      h("p", { class: "text-sm text-muted" }, "Answers: " + problem.fields.map(f => `${f.label}: ${f.answer}`).join(" · ")),
      h("div", { class: "cluster" },
        !(S.drills[problem.id] && S.drills[problem.id].right) ? h("button", { type: "button", class: "btn btn--primary", onclick: () => { const k = items.indexOf(problem); viewDrill(type, items[(k + 1) % items.length].id); } }, "Next problem") : null,
        h("a", { class: "text-sm", href: `#dish/${info.dish}/watch` }, `Rewatch lesson ${info.dish}`)));
  }
  const solved = items.filter(p => S.drills[p.id] && S.drills[p.id].right).length;
  show(h("div", { class: "measure" },
    h("div", { class: "page-head" }, h("h1", {}, info.title), h("span", { class: "text-muted" }, `${solved} of ${items.length} solved`)),
    h("section", { class: "card stack" }, h("div", { class: "question" }, problem.prompt), form, feedback, after, stepsBox),
    h("a", { href: "#drills" }, "All drills")));
  if (inputs[0]) inputs[0].el.focus();
}

// Readiness ------------------------------------------------------------------
function viewReady() {
  const ticks = D.ready.filter((r, i) => S.ready[i]).length;
  show(h("div", { class: "measure" },
    h("h1", {}, "Readiness board"),
    h("p", { class: "text-muted" }, `${ticks} of ${D.ready.length} ticked. Tick a box only after doing the task from memory and checking a concrete example. These are study criteria, not an official rubric.`),
    D.ready.map((r, i) => h("section", { class: "card stack" },
      h("label", { class: "check" },
        h("input", { type: "checkbox", checked: !!S.ready[i], onchange: e => { S.ready[i] = e.target.checked; save(); viewReady(); } }),
        h("span", {}, h("b", {}, r.title), `: ${r.text}`)),
      h("div", { class: "cluster indent text-sm" },
        r.dishes.filter(d => D.dishes[d]).map(d => h("a", { href: `#dish/${d}/watch` }, `Watch ${d}`)),
        r.drills.map(k => h("a", { href: `#drills/${k}` }, `Drill: ${D.drillTypes.find(t => t.key === k).title}`)))))));
}


function migrationView() {
  const convert = original => {
    const remap = key => key.replace(/^(dish:)?(\d+)(\.\d+)(.*)$/, (whole, prefix, chapter, rest, tail) => {
      if (!original) return whole;
      if (Number(chapter) === 1) return "";
      return (prefix || "") + (Number(chapter) + 4) + rest + tail;
    });
    S = Object.assign(defaults(), pendingProgress);
    for (const field of ["done", "tested"]) {
      S[field] = Object.fromEntries(Object.entries(S[field] || {}).map(([k,v]) => [remap(k),v]).filter(([k]) => k));
    }
    // Question identifiers are content identities, not chapter numbers.
    S.pos = {}; S.courseVersion = D.courseVersion;
    pendingProgress = null; save(); route();
  };
  show(h("section", {class:"card measure stack"}, h("h1",{},"Bring your progress forward"),
    h("p",{},"Which course did you use? Lesson numbers overlap, so choose the numbering shown in your previous player. Listening positions will reset for the new narration."),
    h("button",{class:"btn",onclick:exportProgress},"Export a backup first"),
    h("button",{class:"btn btn--primary",onclick:()=>convert(true)},"Original: Lecture 6 was chapter 2"),
    h("button",{class:"btn",onclick:()=>convert(false)},"Renumbered: Lecture 6 was chapter 6")));
}

function viewContents() {
  const chapters = [...new Set(D.order.map(id => D.dishes[id].chapter))];
  show(h("div", {class:"page-head"}, h("div",{},h("div",{class:"eyebrow"},"MIDTERM 2 · LECTURES 6–15"),
    h("h1",{},"Your course"),h("p",{class:"text-muted"},"Follow a lecture, revisit a diagram, or pick up where you left off."))),
    ...chapters.map(ch => h("section",{class:"card lecture-group"},
      h("h2",{},D.dishes[D.order.find(id=>D.dishes[id].chapter===ch)].chapterTitle),
      ...D.order.filter(id=>D.dishes[id].chapter===ch).map(id=>{
        const d=D.dishes[id]; const pos=S.pos[id]||0;
        return h("a",{class:"lesson-row",href:`#dish/${id}/watch/${pos}`},
          h("span",{class:"lesson-number"},id),h("span",{class:"lesson-title"},d.title),
          h("span",{class:"text-sm text-muted"},`${d.minutes} min`),
          h("span",{class:"tag"},d.cooked ? (pos ? "Resume" : "Watch") : "Transcript"));
      }))));
}

// Page frame -----------------------------------------------------------------
function renderScore() {
  const el = document.getElementById("score");
  if (el) el.replaceChildren(h("b", {}, S.right), " right");
}
function route() {
  if (pendingProgress) return migrationView();
  if (cleanup) { cleanup(); cleanup = null; }
  const [view, a, b, c] = location.hash.replace(/^#/, "").split("/");
  const section = view || "home";
  document.querySelectorAll("[data-nav]").forEach(n => {
    const current = n.dataset.nav === section || (section === "dish" && n.dataset.nav === "home") || (section === "review" && n.dataset.nav === "home");
    if (current) n.setAttribute("aria-current", "page"); else n.removeAttribute("aria-current");
  });
  if (section === "dish") viewDish(a, b, c ? Number(c) : 0);
  else if (section === "review") viewReview();
  else if (section === "contents") viewContents();
  else if (section === "find") viewFind();
  else if (section === "midterm") viewMidterm();
  else if (section === "drills") a ? viewDrill(a) : viewDrills();
  else if (section === "ready") viewReady();
  else viewHome();
}
async function start() {
  load();
  renderScore();
  try {
    D = await (await fetch("/data.json", { cache: "no-cache" })).json();
  } catch (e) {
    show(h("div", { class: "notice notice--danger", role: "alert" }, "The course data didn't load. Open the course launcher and try again."));
    return;
  }
  if (S.courseVersion && S.courseVersion !== D.courseVersion) { S.pos = {}; save(); }
  window.addEventListener("hashchange", route);
  route();
}
start();
