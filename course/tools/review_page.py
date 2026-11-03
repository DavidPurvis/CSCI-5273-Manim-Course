"""One page with every cooked dish: video, contact sheet, check results, and a notes box for prep."""
import html
import json
from datetime import datetime
from pathlib import Path


def build(build_dir, pack, dishes, load_card, fp_of):
    build_dir = Path(build_dir)
    final = build_dir / "dishes" / "final"
    cooked = [d for d in dishes if (final / f"{d}.mp4").exists()]
    if not cooked:
        return False
    decisions_path=build_dir/'review/decisions.jsonl'
    decisions=[json.loads(line) for line in decisions_path.read_text().splitlines() if line.strip()] if decisions_path.exists() else []
    latest={(row['artifact_hash'],row['category']):row['result'] for row in decisions if str(row.get('reviewer','')).strip()}
    identities={dish:fp_of(dish) for dish in cooked}
    (build_dir/'review').mkdir(parents=True,exist_ok=True)
    (build_dir/'review/artifacts.json').write_text(json.dumps(sorted(identities.values())))
    categories=('content','visual','audio','captions')
    fresh=[dish for dish in cooked if not all(latest.get((identities[dish],category))=='passed' for category in categories)]
    def selectors(dish):
        controls=[]
        for category in categories:
            current=latest.get((identities[dish],category),'not_reviewed')
            options=''.join(f'<option value="{value}"'+(' selected' if current==value else '')+'>'+label+'</option>' for value,label in [('not_reviewed','Not reviewed'),('passed','Passed'),('failed','Failed')])
            controls.append(f'<label>{category} <select data-category="{category}">{options}</select></label>')
        return ' '.join(controls)
    rows = []
    for d in fresh + [x for x in cooked if x not in fresh]:
        taste = build_dir / "taste" / f"{d}.json"
        info = json.loads(taste.read_text()) if taste.exists() else {"problems": ["not tasted"], "stills": {}}
        still = info.get("stills") or {}
        status = "FAIL" if info["problems"] else "PASS"
        problems = "".join(f"<li>{html.escape(x)}</li>" for x in info["problems"])
        flag = "review incomplete for this artifact" if d in fresh else "all four explicit reviews passed"
        rows.append(f"""<section data-dish="{d}" data-fp="{identities[d]}" class="{'fresh' if d in fresh else 'old'}">
<h2>{d} {html.escape(load_card(d)['title'])}</h2>
<p class="meta">Concepts: {html.escape(", ".join(load_card(d).get("concepts") or []) or "See the source bindings for this dish")}</p>
<p class="meta"><b class="{status}">{status}</b> · {flag} · {still.get('over_10s', 0):.0%} in stills over 10 s · longest still {still.get('longest', 0):.0f} s</p>
<ul class="problems">{problems}</ul>
<details><summary>Video and contact sheet</summary>
<video controls preload="none" src="/dishes/final/{d}.mp4"></video>
<img loading="lazy" src="/taste/{d}.png" alt="Contact sheet for dish {d}"></details>
<div>Review: {selectors(d)}</div>
<textarea placeholder="Note for prep: what looks or sounds wrong?"></textarea>
</section>""")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Kitchen review</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{background:#11141B;color:#F2F4F8;font:16px/1.5 "Helvetica Neue",Arial,sans-serif;margin:0 auto;max-width:1100px;padding:24px 16px}}
h1{{font-size:26px;margin:0 0 4px}} h2{{font-size:19px;margin:0}} section{{background:#1B2029;border-radius:8px;margin:14px 0;padding:14px 16px}}
.meta{{color:#A9B3C4;margin:4px 0}} .PASS{{color:#4CD07D}} .FAIL{{color:#FF5A5A}} .problems{{color:#FF5A5A;margin:4px 0}} .problems:empty{{display:none}}
video,img{{width:100%;margin-top:8px;border-radius:6px;background:#000}} summary{{cursor:pointer;color:#4A9EFF}}
textarea{{width:100%;box-sizing:border-box;margin-top:10px;min-height:44px;background:#11141B;color:#F2F4F8;border:1px solid #5B667A;border-radius:6px;padding:8px;font:inherit}}
button{{background:#FF8A3D;color:#11141B;border:0;border-radius:6px;padding:10px 18px;font:600 16px "Helvetica Neue",Arial,sans-serif;cursor:pointer}}
.bar{{position:sticky;top:0;background:#11141B;padding:10px 0;display:flex;gap:14px;align-items:center;flex-wrap:wrap}} #said{{color:#A9B3C4}}
</style></head><body><h1>Kitchen review</h1><p class="meta">{len(fresh)} of {len(cooked)} dishes still need explicit review. Incomplete reviews come first.</p>
<div class="bar"><label>Reviewer name or ID <input id="reviewer" required></label><button id="save">Save notes and explicit reviews</button><span id="said"></span></div>
{''.join(rows)}
<script>
document.getElementById('save').onclick = async () => {{
  const items = [...document.querySelectorAll('section')].map(s => ({{reviewer: document.getElementById('reviewer').value.trim(), dish: s.dataset.dish, fp: s.dataset.fp, note: s.querySelector('textarea').value.trim(), fresh: s.classList.contains('fresh'), reviews: Object.fromEntries([...s.querySelectorAll('select')].map(x => [x.dataset.category, x.value]))}}));
  if (items.some(i => Object.values(i.reviews).some(v => v !== 'not_reviewed')) && !document.getElementById('reviewer').value.trim()) {{ document.getElementById('said').textContent = 'Enter the reviewer name or ID.'; return; }}
  const r = await fetch('/notes', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(items)}});
  const j = await r.json();
  document.getElementById('said').textContent = j.error || ('Saved ' + j.notes + ' notes to review-notes.md');
}};
</script></body></html>"""
    out = build_dir / "review"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page)
    return True


def save_notes(data, notes_path, build_dir):
    items = json.loads(data)
    if any(any(v != "not_reviewed" for v in i.get("reviews",{}).values()) and not i.get("reviewer", "").strip() for i in items):
        return {"notes":0,"error":"Reviewer name or ID is required for explicit decisions"}
    seen_path = Path(build_dir) / "review" / "seen.json"
    seen = json.loads(seen_path.read_text()) if seen_path.exists() else {}
    notes = [i for i in items if i["note"]]
    if notes:
        with Path(notes_path).open("a") as f:
            f.write(f"\n## {datetime.now():%A %B %-d, %-I:%M %p}\n\n")
            for i in notes:
                f.write(f"- **{i['dish']}:** {i['note']}\n")
    from course.contracts import ReviewDecision
    from course.tools.preparation import record_review
    store=Path(build_dir)/'review/decisions.jsonl'
    existing=[json.loads(line) for line in store.read_text().splitlines() if line.strip()] if store.exists() else []
    latest={(row['artifact_hash'],row['category']):row['result'] for row in existing if str(row.get('reviewer','')).strip()}
    # Notes are already safe. Only a new decision about an old video is refused, because it would prove nothing about the current one.
    known_path = Path(build_dir) / "review" / "artifacts.json"
    if known_path.exists():
        known = set(json.loads(known_path.read_text()))
        if any(i.get("fp") not in known and any(r != latest.get((i.get("fp"),c),"not_reviewed") for c,r in i.get("reviews",{}).items()) for i in items):
            return {"notes":len(notes),"error":f"Saved {len(notes)} notes. Review decisions were not saved because that video is not current; reload the review page"}
    for item in items:
        for category,result in item.get('reviews',{}).items():
            key=(item['fp'],category)
            if result!=latest.get(key,'not_reviewed'):
                if not item.get('reviewer','').strip():
                    return {'notes':len(notes),'error':'Reviewer name or ID is required to change or revoke a decision'}
                record_review(ReviewDecision(item['fp'],item.get('reviewer','').strip(),datetime.now().isoformat(),category,result,item['note']),store)
                latest[key]=result
    return {"notes": len(notes)}
