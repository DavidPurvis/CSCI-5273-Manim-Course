"""Explicit source preparation and read-only acceptance audit."""
import hashlib
import json
import shutil
from dataclasses import asdict
from pathlib import Path
import yaml
from course.contracts import Finding, ReviewDecision
from course.catalog import MAIN, SUPPLEMENTS, is_main

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT/'sources/snapshot'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def discover_vault(root):
    root=Path(root)
    return [p for p in sorted(root.rglob('*')) if p.is_file() and (p.name=='.vault-progress.md' or not any(s.startswith('.') for s in p.relative_to(root).parts)) and p.suffix in ('.md','.canvas','.pdf','.png','.jpg')]


def snapshot_sources(inventory, destination):
    destination=Path(destination);records=[]
    # inventory is (root, files); explicit root makes relative names unambiguous.
    root,files=inventory
    for p in files:
        rel=p.relative_to(root);out=destination/'vault'/rel
        out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
        records.append(dict(source_id=rel.as_posix(),path=out.relative_to(destination).as_posix(),original=str(p),sha256=digest(out),category=rel.parts[0]))
    return records


def write_source_manifest(records):
    from course.stage.card import load_card
    decks=sorted({b['pdf'][0] for p in (ROOT/'recipes').glob('*.yaml') for b in load_card(p.stem)['beats']})
    deck_paths=[]
    for deck in decks:
        matches=[r['path'] for r in records if Path(r['path']).name==deck]
        if len(matches)!=1:raise ValueError(f'Required deck must appear exactly once: {deck}')
        deck_paths.append(matches[0])
    manifest=dict(schema_version=1,snapshot_id=hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest(),
                  records=records,required_decks=deck_paths)
    (SNAPSHOT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    return manifest


def parse_note(path):
    text=Path(path).read_text();parts=text.split('---',2)
    meta=yaml.safe_load(parts[1]) if text.startswith('---\n') and len(parts)>2 else {}
    return dict(text=text,metadata=meta or {},sections={line[3:]:i for i,line in enumerate(text.splitlines(),1) if line.startswith('## ')})


def audit():
    findings=[]
    def fail(code,artifact,msg):findings.append(Finding(code,'error',artifact,artifact,msg,code))
    manifest=json.loads((SNAPSHOT/'manifest.json').read_text())
    for item in manifest['records']:
        p=SNAPSHOT/item['path']
        if not p.exists() or digest(p)!=item['sha256']:fail('SOURCE_HASH',item['source_id'],'source missing or changed')
    concepts=json.loads((ROOT/'sources/concepts.json').read_text())
    bindings=json.loads((ROOT/'sources/bindings.json').read_text()) if (ROOT/'sources/bindings.json').exists() else {}
    if set(concepts)!=set(bindings):fail('COVERAGE','bindings','expected one binding per concept')
    from course.stage.card import load_card,load_manifest,beat_times
    frames=0
    for p in (ROOT/'recipes').glob('*.yaml'):
        c=load_card(p.stem)
        if is_main(p.stem):frames+=round(beat_times(c,load_manifest())[1]*30)
        for b in c['beats']:
            deck=b.get('pdf',[None])[0]
            if deck and not (SNAPSHOT/'vault/Assets/Slides'/deck).exists():fail('MISSING_DECK',b['id'],str(deck))
    if not 210<=frames/1800<=240:fail('DURATION','main',f'{frames/1800:.2f} minutes')
    timing=json.loads((ROOT/'narration/timing.json').read_text())
    for bid,entry in timing.items():
        if len(entry.get('provenance',[]))!=len(entry.get('t',[])):
            fail('ALIGNMENT_PROVENANCE',bid,'word provenance missing')
    from course.tools.narration_assets import catalog_assets,validate_alignment_evidence
    _,narration_findings=catalog_assets()
    findings.extend(narration_findings)
    findings.extend(validate_alignment_evidence())
    findings.extend(validate_resources(load_course_resources()))
    findings.extend(validate_bindings(load_course_resources(),[load_card(p.stem) for p in (ROOT/'recipes').glob('*.yaml')],bindings))
    from course.tools.reference_integrity import validate_reference_integrity
    for message in validate_reference_integrity():
        findings.append(Finding('REFERENCE_INTEGRITY','error','events','sources/event-reference-baseline.json',message,'Review event remapping and deliberately update baseline'))
    from course.tools.gemini import validate_freshness
    for message in validate_freshness():
        findings.append(Finding('GEMINI_FRESHNESS','error','gemini','Gemini context',str(message),'Regenerate with python -m course.tools.gemini'))
    return findings


def record_review(decision, store):
    if decision.category not in ('content','visual','audio','captions'):raise ValueError('unknown review category')
    if decision.result not in ('passed','failed','not_reviewed'):raise ValueError('unknown review result')
    p=Path(store);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a') as f:f.write(json.dumps(asdict(decision))+'\n')


def prepare():
    from course.tools import sources,portion
    sources.main();portion.main()
    from course.tools.narration_assets import write_catalog,export_alignment_evidence
    write_catalog()
    export_alignment_evidence()
    cards=[yaml.safe_load(p.read_text()) for p in (ROOT/'recipes').glob('*.yaml')]
    concepts=json.loads((ROOT/'sources/concepts.json').read_text())
    binding_path=ROOT/'sources/teaching-bindings.yaml'
    if not binding_path.exists():raise ValueError('Missing authoritative teaching-bindings.yaml')
    bindings=yaml.safe_load(binding_path.read_text())
    if set(bindings)!=set(concepts):raise ValueError('Curated bindings must cover exactly the current concepts')
    (ROOT/'sources/bindings.json').write_text(json.dumps(bindings,indent=1,ensure_ascii=False))
    generate_docs(cards,bindings)
    return audit()


def generate_docs(cards,bindings):
    out=ROOT/'docs';out.mkdir(exist_ok=True)
    texts={
    '00-START-HERE':'Run ./kitchen prepare only when updating ingredients. Then ./kitchen audit and ./kitchen check. Cook with ./kitchen run. Inspect with ./kitchen review. Use ./kitchen verify-release for the release evidence. A failed check stops assembly; do not improvise numeric results.',
    '01-DECISIONS-AND-SOURCES':'Instructor PDFs define scope; the vault supplies explanations and corrections. The pasted review is a proposal. Keep native Manim sound/subcaptions and Samantha. Retain the simplified instructor BGP order. Poison reverse does not eliminate longer cycles. Main duration is 210–240 minutes; supplements use separate clocks. Original source paths in the snapshot manifest are provenance only.',
    '02-RESOURCE-AND-COVERAGE-MAP':'Generated bindings below are candidates requiring substantive content review. A tag does not prove explanation.\n\n'+'\n'.join(f'- {k}: '+', '.join(v['primary_beats']+v['supporting_beats']) for k,v in bindings.items()),
    '03-CONTRACTS':'See course/contracts.py for dataclass contracts. Schema version 1. Frame intervals are half-open. Layout ownership is sources/layout-overrides.yaml. Authoring YAML owns content; recipes and narration Markdown are generated. No generated file owns new content. Missing sources and unresolved anchors are errors.',
    '04-SCENE-RECIPES':'Generated scene inventory. Existing choreography is preserved except the explicit work orders.\n\n'+'\n'.join(f"## {c['dish']} {c['title']}\n"+'\n'.join(f"- {b['id']} ({b['stage']}): {len(b.get('moves',[]))} moves; source {b.get('pdf')}" for b in c['beats']) for c in sorted(cards,key=lambda c:[int(x) for x in str(c['dish']).split('.')]) if is_main(c['dish'])),
    '05-NARRATION-AND-TIMELINE':'Samantha, 140 words/minute. Preserve cached WAV bytes. ASR alignment and interpolation are distinct; neither proves intelligibility. Legacy timing lacks provenance and requires migration. Caption policy: two lines, 42 characters/line, target 19.5 characters/second. Resolve repeated phrase occurrences explicitly. Use one compiled frame timeline for video and exports.',
    '06-VERIFICATION':'Numeric tests use ipaddress, Floyd–Warshall, payload reconstruction, scalar CDMA arithmetic, and explicit model answers. Source hashes are audited. Visual/audio/caption/content review is separate from automatic checks. Unknown provenance is not a pass. Fresh-environment reproduction must render 1.1 and 3.4. See implementation-status.json for uncompleted acceptance work.',
    '07-BUILD-AND-RECOVERY':'Snapshot inputs before rendering. Fingerprints must include WAV bytes and timing as well as rendering code. Assembly has a separate fingerprint. Preserve artifacts until successors verify. Delete only project build caches. A copied source using the original virtual environment is not fresh-environment reproduction.',
    '08-WORK-ORDERS':'1. Snapshot resources. 2. Contracts and overrides. 3. Portable consumers. 4. VLAN/STP/poison models. 5. Timeline compiler and dish 1.1. 6. Scene changes. 7. Assembly receipts and reviews. 8. Fresh reproduction and source packaging. Each order needs tests and evidence; consult implementation-status.json before claiming completion.'}
    import ast
    api=[]
    for folder in ('model','stage','tools'):
        for module in sorted((ROOT/'course'/folder).glob('*.py')):
            tree=ast.parse(module.read_text())
            for node in tree.body:
                if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and not node.name.startswith('_'):
                    signature = node.name+"("+ast.unparse(node.args)+")" if isinstance(node,ast.FunctionDef) else "class "+node.name
                    api.append(f"- `{folder}/{module.name}:{node.lineno}`: `{signature}` — {ast.get_docstring(node) or 'See implementation and tests.'}")
    texts['00-START-HERE'] += '\n\n## Fresh checkout setup and exact render commands\n\n'+(ROOT/'SETUP.md').read_text()
    texts['03-CONTRACTS'] += '\n\n## Shared records\n\n```python\n'+(ROOT/'course/contracts.py').read_text()+'\n```\n'
    texts['03-CONTRACTS'] += '\n\n## Actual API inventory\n\n'+'\n'.join(api)
    vault=SNAPSHOT/'vault'
    resource_lines=[]
    for folder in ('Lectures','Examples','Formulas','Practice'):
        for p in sorted((vault/folder).glob('*.md')):
            resource_lines.append(f"- {folder}/{p.name}: packaged unchanged; SHA-256 {digest(p)}")
    texts['02-RESOURCE-AND-COVERAGE-MAP'] += '\n\n## Resource inventory\n\n'+'\n'.join(resource_lines)
    texts['02-RESOURCE-AND-COVERAGE-MAP'] += '\n\n## Curated resource destinations\n\n```yaml\n'+(ROOT/'sources/resource-destinations.yaml').read_text()+'\n```\n'
    texts['02-RESOURCE-AND-COVERAGE-MAP'] += '\n\n## Corrections\n\n'+(ROOT/'sources/clarifications.yaml').read_text()
    texts['04-SCENE-RECIPES'] += '\n\n## Exact generated cards\n\n```yaml\n'+yaml.safe_dump_all([c for c in sorted(cards,key=lambda c:[int(x) for x in str(c['dish']).split('.')]) if is_main(c['dish'])],sort_keys=False,allow_unicode=True)+'\n```\n'
    texts['01-DECISIONS-AND-SOURCES'] += "\n\n## Review dispositions\n\n1. Segmentation: accepted; preserve reading/prediction holds.\n2. Protocol audit: accepted; independent fixtures and source hashes.\n3. Add practice: modified; use existing supplements, no padding.\n4. Voiceover plugin: rejected; native interfaces retained.\n5. Accessibility: accepted as production rules, not universal empirical thresholds.\n6. Fill a 13-minute gap: rejected; that baseline is obsolete.\n7. Production: modified; explicit prepare versus read-only audit, resumed renders and receipts.\n\nSingle unscoped VLAN learning, forwarding across blocked STP ports, a universal Cisco BGP ladder, mandatory spelled-out MAC, and claims that poison reverse prevents all cycles are rejected. Source corrections remain explicit."
    texts['01-DECISIONS-AND-SOURCES'] += '\n\n## Evaluated proposal register\n\nThe preserved review supplies proposals and unverified claims, not execution authority. Each row identifies its original source line, disposition, implementation decision and evidence.\n\n```yaml\n'+(ROOT/'sources/proposal-decisions.yaml').read_text()+'\n```\n'
    texts['05-NARRATION-AND-TIMELINE'] += '\n\nScene setup uses authoritative `pre_roll` seconds, quantized to frames. Audio and captions begin at the compiled speech start; unanchored setup runs before it. Internal anchor conflicts remain errors. Every deliberate cue change is recorded in sources/choreography-decisions.json.\n'
    texts['05-NARRATION-AND-TIMELINE'] += "\n\n## Timing pipeline\n\nProvider character timestamps or explicit ASR → written/spoken token mapping → synthesizer/ASR/interpolated provenance → occurrence-qualified phrase anchors → integer frame schedule. The renderer invokes mutating move functions only at their start. Anchor conflicts are errors, not permission to speed up animations. Audio-byte identity invalidates timing. Caption intervals and animation schedules use 30 fps. Prediction holds prevent incidental highlighting. `build/audit.json` identifies authored conflicts. No transcription score establishes perceptual review."
    texts['07-BUILD-AND-RECOVERY'] += '\n\nRendering captures its input fingerprint before dry run and compares it after rendering. Input changes during a render reject that result. Receipts bind profile, narration bytes, beat-specific alignment and measured durations, stage code, lock and traces. Notes never imply review completion.\n'
    texts['07-BUILD-AND-RECOVERY'] += "\n\n## Reproduction\n\nUse a new Python 3.12 environment at build/reproduction/.venv and install requirements.lock with uv pip sync. Run python -m course.tools.reproduction. It copies source and cached assets, excludes environments/caches, runs tests and renders 6.1 and 7.4 sequentially. Results are in build/reproduction/report.json. Package with python -m course.tools.package."
    texts['06-VERIFICATION'] += '\n\n## Explicit review scope\n\nA content pass means the current dish substantively explains every bound concept and communicates its source corrections; use the bindings and scene inventory to check this. A visual pass covers clipping, labels, arrows and state transitions. An audio pass requires listening for intelligibility and pronunciation. A caption pass checks timing, text and readability. Source-frame sampling and ASR agreement are evidence with limited scope; neither passes all four categories. A note without explicit category results changes no review state.\n\nRun python -m course.tools.media_audit after production to decode and seek every delivered MP4, inspect audio/caption packets and marker counts, and record content hashes. It caches checks only for unchanged bytes and verifier code.\n'
    texts['03-CONTRACTS'] += '\n\n## Prepared prediction records\n\nA prepared recipe consists of its generated YAML card and its record in recipes/predictions.json. Authoring YAML owns top-level prediction_contracts; portioning exports them losslessly. Each record declares the prediction/answer beat pair, exact answer event IDs and answer-bearing object selectors. Compilation checks the actual frame intervals and event references. These verification declarations belong beside the render card because they describe what a reviewer must inspect. The prediction-verification report separates structural timing checks from hidden/neutral-state perceptual review.\n'
    texts['03-CONTRACTS'] += '\n\n## Compatibility and failure examples\n\nA unique string phrase remains valid. A repeated phrase must supply an occurrence. An explicit pre_roll shifts audio and captions together; it does not resolve two conflicting actions within speech. An inferred important routing, mask, fragmentation or encapsulation anchor is rejected. Changed WAV bytes reject the old alignment. Source references use one-based PDF pages; page zero is invalid. Source-link aliases must resolve uniquely. Exact regression examples are in course/tests/test_timeline.py and test_preparation.py. Template illustrative links are preserved as inert examples, outside the navigation graph.\n'
    texts['02-RESOURCE-AND-COVERAGE-MAP'] += '\n\n## Authoritative teaching bindings\n\nCurate sources/teaching-bindings.yaml. Prepare exports bindings.json without replacing the curated choices. Each entry records the actual primary narration, visible event IDs, PDF references and prediction/answer pairs; content review remains explicit.\n'
    from course.tools.architecture_notes import NOTES
    for name,detail in NOTES.items():texts[name] += detail
    for name,text in texts.items():(out/f'{name}.md').write_text('# '+name.split('-',1)[1].replace('-',' ')+'\n\n'+text+'\n')


def cmd_prepare(args):
    if args.vault:
        # Existing snapshot retains reviewed extra sources; refuse silent replacement.
        if not Path(args.vault).is_dir():raise ValueError('vault directory does not exist')
        records=snapshot_sources((Path(args.vault),discover_vault(args.vault)),SNAPSHOT)
        old=json.loads((SNAPSHOT/'manifest.json').read_text())
        keep=[x for x in old['records'] if x['category'] in ('foundation','proposal')]
        structured=Path(args.vault)/'.vaultcraft/source-manifest.json'
        shutil.copy2(structured,SNAPSHOT/'vault-source-manifest.json')
        records.append(dict(source_id='vault-source-manifest',path='vault-source-manifest.json',original=str(structured),sha256=digest(structured),category='source_manifest'))
        write_source_manifest(records+keep)
    errors=prepare()
    print('PREPARED' if not errors else 'PREPARATION FAILED')
    return bool(errors)


def timeline_findings():
    from course.stage.card import load_card,load_manifest,load_timing,narration_text
    from course.stage.timeline import compile_dish
    from course.stage.moves import REGISTRY
    from dataclasses import asdict
    findings=[];timelines=[];output=ROOT/'build/timelines';output.mkdir(parents=True,exist_ok=True)
    for p in sorted((ROOT/'recipes').glob('*.yaml')):
        try:
            t=compile_dish(load_card(p.stem),load_manifest(),load_timing(),narration_text(),{k:v['t'] for k,v in REGISTRY.items()})
            timelines.append(t)
            from course.tools.predictions import load_prediction_contracts
            record=asdict(t)
            record['prediction_contracts']=[c for c in load_prediction_contracts() if c['prediction_beat'].rsplit('.',1)[0]==p.stem]
            (output/f'{p.stem}.json').write_text(json.dumps(record))
        except (ValueError,KeyError) as e:
            findings.append(Finding('TIMELINE','error',p.stem,str(p.relative_to(ROOT)),str(e),'Correct phrase occurrence/order or explicit animation durations in authoring; prepare again'))
    from course.tools.predictions import validate_prediction_contracts
    findings.extend(validate_prediction_contracts(timelines))
    return findings


def cmd_audit(args):
    findings=audit()+timeline_findings()
    out=ROOT/'build/audit.json';out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps([asdict(f) for f in findings],indent=2))
    for f in findings:print(f'{f.code} {f.artifact_id}: {f.message}')
    print('MISE COMPLETE' if not findings else f'NOT READY: {len(findings)} findings; build/audit.json')
    return bool(findings)


def cmd_verify(args):
    findings=verify_release()
    (ROOT/'build').mkdir(exist_ok=True)
    (ROOT/'build/release-verification.json').write_text(json.dumps([asdict(f) for f in findings],indent=2))
    print('RELEASE VERIFIED' if not findings else f'RELEASE NOT VERIFIED: {len(findings)} findings; build/release-verification.json')
    return bool(findings)


def load_course_resources(snapshot=SNAPSHOT):
    from course.contracts import ResourceCatalog
    notes={};aliases={};groups={k:{} for k in ('concepts','lectures','examples','formulas','exercises','corrections','figures')}
    snapshot=Path(snapshot)
    for p in (snapshot/'vault').rglob('*.md'):
        key=p.relative_to(snapshot/'vault').as_posix();note=parse_note(p);notes[key]=note
        for alias in [p.stem,*note['metadata'].get('aliases',[])]:aliases.setdefault(alias,[]).append(key)
        first=Path(key).parts[0]
        group={'Concepts':'concepts','Lectures':'lectures','Examples':'examples','Formulas':'formulas','Practice':'exercises'}.get(first)
        if group:groups[group][key]=note
    for p in (snapshot/'vault/Assets/Figures').glob('*'):groups['figures'][p.name]=p.relative_to(snapshot).as_posix()
    groups['corrections']=yaml.safe_load((ROOT/'sources/clarifications.yaml').read_text())
    return ResourceCatalog(notes,**groups,aliases=aliases)


def resolve_wikilink(link,catalog):
    from course.contracts import SourceRef
    raw=link.strip('![]').split('|')[0];target,_,heading=raw.partition('#')
    if Path(target).suffix in ('.pdf','.png','.jpg','.canvas'):
        exact=SNAPSHOT/'vault'/target
        matches = [exact] if exact.is_file() else [p for p in (SNAPSHOT/'vault').rglob(Path(target).name) if p.is_file()]
        if len(matches) != 1:raise ValueError(f'Unresolved or ambiguous asset: {link}')
        p=matches[0]
        pages=[int(heading.split('=',1)[1])] if heading.startswith('page=') else []
        if pages:
            decks=json.loads((ROOT/'sources/decks.json').read_text())
            count=decks.get(p.name,{}).get('pages')
            if pages[0]<1 or count is None or pages[0]>count:raise ValueError(f'Invalid one-based PDF page: {link}')
        return SourceRef(target,p.relative_to(SNAPSHOT).as_posix(),heading,pages,digest(p),'asset')
    key=target if target.endswith('.md') else target+'.md'
    matches=[key] if key in catalog.notes else catalog.aliases.get(target.removesuffix('.md'),[])
    if len(matches)!=1:raise ValueError(f'Unresolved or ambiguous link: {link}')
    if heading:
        import re
        headings=[re.sub(r'^#+\s+','',line).strip() for line in catalog.notes[matches[0]]['text'].splitlines() if line.startswith('#')]
        if heading not in headings:raise ValueError(f'Unresolved note heading: {link}')
    path='vault/'+matches[0]
    return SourceRef(matches[0],path,heading,sha256=digest(SNAPSHOT/path),category=Path(matches[0]).parts[0])


def validate_resources(catalog):
    import re
    findings=[]
    for name,note in catalog.notes.items():
        # Template examples such as [[Previous]] and [[Next]] are literal authoring guidance.
        if name.startswith('Templates/'):continue
        for link in re.findall(r'!?\[\[([^\]]+)\]\]',note['text']):
            try:resolve_wikilink(link,catalog)
            except (ValueError,KeyError) as exc:
                findings.append(Finding('SOURCE_LINK','error',name,name,str(exc),'Repair packaged source binding or include referenced asset'))
    for canvas in (SNAPSHOT/'vault').rglob('*.canvas'):
        try:
            data=json.loads(canvas.read_text())
            for node in data.get('nodes',[]):
                if node.get('type')=='file' and not (SNAPSHOT/'vault'/node['file']).is_file():
                    findings.append(Finding('CANVAS_ASSET','error',canvas.name,node['file'],'Canvas target is absent from snapshot','Snapshot the referenced source'))
        except (ValueError,KeyError) as exc:
            findings.append(Finding('CANVAS','error',canvas.name,str(canvas),str(exc),'Repair source canvas'))
    return findings


def load_bindings(path):
    return json.loads(Path(path).read_text())


def validate_bindings(catalog,dishes,bindings):
    beats={b['id']:b for d in dishes for b in d['beats']};out=[]
    def fail(name,message):
        out.append(Finding('BINDING','error',name,'sources/teaching-bindings.yaml',message,'Repair the curated binding and prepare again'))
    for name,binding in bindings.items():
        if not binding['primary_beats'] or any(x not in beats for x in binding['primary_beats']+binding['supporting_beats']):
            fail(name,'missing explanatory beat');continue
        if not binding.get('explanation_claim'):fail(name,'missing explanation claim')
        for reference in binding.get('source_refs',[]):
            try:resolve_wikilink(reference,catalog)
            except ValueError as exc:fail(name,str(exc))
        evidence=binding.get('mechanism')
        if isinstance(evidence,dict):
            beat=beats.get(evidence.get('beat'))
            if beat is None:fail(name,'missing demonstration beat')
            else:
                events={r.get('event_id',f"{beat['id']}:move:{i}") for i,r in enumerate(beat['moves'])}
                if set(evidence.get('visible_events',[]))-events:fail(name,'demonstration event no longer exists')
        for question,answer in binding.get('prediction_pairs',[]):
            if question not in beats or answer not in beats or beats[question]['stage']!='prediction' or beats[answer]['stage']!='explanation':fail(name,'prediction/answer pair does not resolve')
    return out


def build_coverage_report(catalog,bindings):
    return dict(total=len(catalog.concepts),mapped=sum(bool(b['primary_beats']) for b in bindings.values()),bindings=bindings)


def verify_release(context=None):
    from course.tools.evidence import fingerprint_dish,fingerprint_assembly,artifact_hash,artifact_matches
    from course.tools.kitchen import verify_playback,run,chapter_title,dishes,matches_plan
    findings=audit()+timeline_findings()
    def fail(code,artifact,location,message,remedy):
        findings.append(Finding(code,'error',artifact,str(location),message,remedy))
    review=ROOT/'build/review/decisions.jsonl'
    decisions=[json.loads(line) for line in review.read_text().splitlines() if line.strip()] if review.exists() else []
    for dish in dishes():
        video=ROOT/'build/dishes/final'/f'{dish}.mp4';receipt=video.with_suffix('.receipt.json')
        if not video.exists() or not receipt.exists():
            fail('RENDER_RECEIPT',dish,receipt,'current final video and receipt required','Cook after audit passes');continue
        data=json.loads(receipt.read_text());sha=artifact_hash(video)
        if data['profile']!='final' or data['input_fingerprint']!=fingerprint_dish(dish) or not artifact_matches(video,data['output_hashes'].get(video.name)):
            fail('STALE_RENDER',dish,receipt,'render inputs, profile or output changed','Cook again');continue
        for category in ('content','visual','audio','captions'):
            matching=[x for x in decisions if x['artifact_hash']==sha and x['category']==category and str(x.get('reviewer','')).strip()]
            if not matching or matching[-1]['result']!='passed':
                fail('REVIEW',dish,category,'current explicit review absent or failed','Review the current artifact')
    repro=ROOT/'build/reproduction/report.json'
    rows=json.loads(repro.read_text()) if repro.exists() else []
    if not rows or any(x['exit_code'] for x in rows):
        fail('REPRODUCTION','release',repro,'successful fresh reproduction required','Run course.tools.reproduction')
    else:
        proof=next((row for row in rows if row.get('test')=='fresh environment tests'),{})
        if not proof.get('tested_candidate_zip') or not proof.get('candidate_sha256') or not proof.get('source_content_matches'):
            fail('REPRODUCTION','release',repro,'actual candidate ZIP reproduction required','Run course.tools.reproduction against the candidate ZIP')
        from course.tools.reproduction import source_content_identity
        if proof.get('source_content_sha256')!=source_content_identity(ROOT):
            fail('STALE_REPRODUCTION','release',repro,'candidate source content differs from current source','Reproduce the current candidate ZIP')
        from course.tools.reproduction import DISHES
        for dish in DISHES:
            row=next((x for x in rows if x.get('dish')==dish),{})
            if not row.get('source_unchanged') or row.get('input_fingerprint')!=fingerprint_dish(dish,{'profile':'preview'}):
                fail('STALE_REPRODUCTION',dish,repro,'reproduction does not describe current inputs','Run course.tools.reproduction')
    media_report=ROOT/'build/media-audit.json'
    cached_media={}
    if not media_report.exists():
        fail('MEDIA_AUDIT','release',media_report,'full delivered-media audit required','Run python -m course.tools.media_audit')
    else:
        from course.tools.media_audit import sha256,verification_identity
        report=json.loads(media_report.read_text())
        if not report.get('automatic_media_verified') or report.get('verification_fingerprint')!=verification_identity():
            fail('MEDIA_AUDIT','release',media_report,'delivered media has unresolved automatic findings','Run media audit after production')
        for row in report.get('artifacts',[]):
            path=ROOT.parent/row['path']
            if not path.exists() or sha256(path)!=row['sha256']:
                fail('STALE_MEDIA_AUDIT',row['path'],media_report,'media changed after playback checks','Run media audit again')
            elif not row['findings'] and report.get('verification_fingerprint')==verification_identity():
                cached_media[row['path']]=row
    from course.tools.assembly import course_plans
    plans=course_plans()
    media=[]
    for ch in sorted({d.split('.')[0] for d in dishes()},key=int):
        paths=list((ROOT.parent/'video/chapters').glob(f'ch{int(ch):02}-*.mp4'))
        media.append(('chapter-'+ch,paths[0] if len(paths)==1 else ROOT.parent/'video/chapters'/f'ch{int(ch):02}.mp4',True,0))
    media.extend([
        ('main',ROOT.parent/'video/CSCI-5273-Lectures-06-15.mp4',True,len(MAIN)),
        ('supplements',ROOT.parent/'video/CSCI-5273-Practice-and-Warm-up.mp4',True,len(SUPPLEMENTS))])
    for output_id,video,needs_captions,chapter_count in media:
        if not video.exists():
            fail('MEDIA',output_id,video,'assembled video missing','Assemble verified dishes');continue
        cached=cached_media.get(str(video.relative_to(ROOT.parent)))
        errors=[] if cached else ['current decode/seek evidence missing; run media audit']
        data=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-show_chapters','-of','json',str(video)]).stdout)
        duration=float(data['format']['duration'])
        if not matches_plan(duration,plans[output_id]):errors.append('duration differs from compiled assembly')
        streams=data.get('streams',[])
        v=next((x for x in streams if x['codec_type']=='video'),{})
        if int(v.get('nb_frames','0'))!=plans[output_id].total_frames:errors.append('video frame count differs from compiled assembly')
        if v.get('width')!=1920 or v.get('height')!=1080 or v.get('r_frame_rate')!='30/1':errors.append('expected 1080p at 30 fps')
        if not any(x['codec_type']=='audio' for x in streams):errors.append('audio stream missing')
        if needs_captions and not any(x['codec_type']=='subtitle' for x in streams):errors.append('selectable caption track missing')
        if chapter_count and len(data.get('chapters',[]))!=chapter_count:errors.append(f'expected {chapter_count} chapter markers')
        receipt=video.with_suffix('.receipt.json')
        if not receipt.exists():errors.append('assembly receipt missing')
        else:
            receipt_data=json.loads(receipt.read_text());identity=receipt_data['assembly_inputs']
            if not artifact_matches(video,receipt_data['artifact_hash']) or receipt_data['input_fingerprint']!=fingerprint_assembly(identity):errors.append('assembly receipt is stale')
            if identity['plan']!=asdict(plans[output_id]):errors.append('assembly membership or frame offsets changed')
            current=[json.loads((ROOT/'build/dishes/final'/f'{d}.receipt.json').read_text()) for d in plans[output_id].members if (ROOT/'build/dishes/final'/f'{d}.receipt.json').exists()]
            if current!=identity['member_receipts']:errors.append('assembly member receipts changed')
        if output_id=='main' and not 12600<=duration<=14400:errors.append('main course outside 210–240 minutes')
        for error in errors:fail('MEDIA',output_id,video,error,'Reassemble from current verified members')
    return findings
