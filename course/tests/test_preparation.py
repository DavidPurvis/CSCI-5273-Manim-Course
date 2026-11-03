import json
from pathlib import Path
from course.tools.preparation import ROOT,load_course_resources,resolve_wikilink,record_review
from course.contracts import ReviewDecision
from course.model.examples import load_example_specs,run_example,verify_example


def test_packaged_catalog_resolves_alias():
    catalog=load_course_resources()
    assert len(catalog.concepts)==176
    ref=resolve_wikilink('Dijkstra Algorithm',catalog)
    assert ref.path.startswith('vault/') and ref.sha256


def test_instructor_expected_results():
    for spec in load_example_specs():assert verify_example(spec,run_example(spec))['passed'],spec['example_id']


def test_notes_do_not_implicitly_pass_review(tmp_path):
    p=tmp_path/'reviews.jsonl'
    record_review(ReviewDecision('abc','tester','2026-11-01','audio','failed','wrong pronunciation'),p)
    rows=[json.loads(x) for x in p.read_text().splitlines()]
    assert len(rows)==1 and rows[0]['result']=='failed' and rows[0]['category']=='audio'


def test_portioning_preserves_metadata_and_overrides_without_mutation():
    from copy import deepcopy
    from course.tools.portion import portion_dish
    dish={'dish':'1.1','title':'x','deck':'lec06-lan.pdf','target_min':1,'beats':[
        {'id':'a','stage':'animation','pdf':1,'say':'A packet moves.', 'pre_roll':1,
         'reading_hold':2,'prediction':{'pair':'b'},'answer_objects':['answer'],
         'assertions':[{'after':'event-A','kind':'present','object':'p'}],
         'moves':[{'packet.hop':{'name':'p','to':'R'},'event_id':'event-A',
                   'when':{'phrase':'moves','occurrence':2,'frame_offset':3}}]}]}
    dish['prediction_contracts']=[{'prediction_beat':'1.1.a','answer_beat':'1.1.b','answer_events':['answer-event'],'answer_objects':[{'object':'answer','before_answer':'hidden_or_neutral'}]}]
    before=deepcopy(dish);override={'1.1.a':{'nudge':{'p':[0,1]}}}
    output=portion_dish(dish,override);beat=output['recipe']['beats'][0]
    assert dish==before
    assert output['prediction_contracts']==dish['prediction_contracts']
    assert beat['moves']==dish['beats'][0]['moves']
    assert beat['assertions']==dish['beats'][0]['assertions']
    assert beat['pre_roll']==1 and beat['reading_hold']==2
    assert beat['adjust']==override['1.1.a']


def test_packaged_wikilinks_and_pdf_pages_resolve():
    from course.tools.preparation import validate_resources
    import pytest
    catalog=load_course_resources()
    assert validate_resources(catalog)==[]
    assert resolve_wikilink('Examples/01 - From Joining a LAN to Sending a Packet',catalog).path.endswith('.md')
    assert resolve_wikilink('lec06-lan.pdf#page=1',catalog).pages==[1]
    with pytest.raises(ValueError,match='one-based PDF page'):
        resolve_wikilink('lec06-lan.pdf#page=0',catalog)


def test_vlan_scene_follows_verified_model_after_arrival():
    from course.stage.card import load_card,load_manifest,load_timing,narration_text
    from course.stage.timeline import compile_dish
    from course.stage.moves import REGISTRY
    from course.model.ethernet import switch_step
    card=load_card('6.4');timelines=compile_dish(card,load_manifest(),load_timing(),narration_text(),{k:v['t'] for k,v in REGISTRY.items()})
    ports=[{'id':i,'vlans':([10,20] if i==5 else [10] if i in [1,2,6] else [20]),'state':'discarding' if i==6 else 'forwarding'} for i in range(1,7)]
    cases=[(10,'A','B',1),(20,'A','B',3),(10,'B','A',2),(20,'B','A',4)]
    state={}
    for n,(vlan,src,dst,ingress) in enumerate(cases,1):
        bid=f'6.4.vlan-trace-{n}';beat=next(b for b in card['beats'] if b['id']==bid)
        compiled=next(b for b in timelines.beats if b.beat_id==bid)
        events={m['event_id']:m for m in compiled.moves}
        arrived=events[f'vlan-{n}-arrive'];learned=events[f'vlan-{n}-learn'];forwarded=events[f'vlan-{n}-forward']
        assert arrived['start']+arrived['frames']<=learned['start']
        assert learned['start']+learned['frames']<=forwarded['start']
        if n>=3:
            lookup=events[f'vlan-{n}-lookup']
            assert learned['start']+learned['frames']<=lookup['start']
            assert lookup['start']+lookup['frames']<=forwarded['start']
            assert lookup['args']['r']==n-3
        trace=switch_step(state,{'vlan':vlan,'src':src,'dst':dst,'in_port':ingress},ports);state=trace['table']
        assert learned['args']['row']==[vlan,src,ingress]
        if trace['action']=='flood':
            assert forwarded['name']=='packet.flood'
            actual=[int(p[1:]) for p in forwarded['args']['to']]
        else:
            assert forwarded['name']=='packet.hop'
            actual=[int(forwarded['args']['to'][1:])]
        assert actual==trace['out_ports']


def test_review_notes_do_not_pass_categories_and_explicit_results_persist(tmp_path):
    from course.tools.review_page import save_notes
    entry={'dish':'1.1','fp':'abc','note':'Inspect the final transition','fresh':True,
           'reviews':{c:'not_reviewed' for c in ['content','visual','audio','captions']}}
    notes=tmp_path/'notes.md';store=tmp_path/'review/decisions.jsonl'
    save_notes(json.dumps([entry]),notes,tmp_path)
    assert not store.exists()
    entry['reviewer']='test reviewer'
    entry['reviews']['visual']='passed'
    save_notes(json.dumps([entry]),notes,tmp_path)
    save_notes(json.dumps([entry]),notes,tmp_path)
    rows=[json.loads(line) for line in store.read_text().splitlines()]
    assert len(rows)==1 and rows[0]['category']=='visual'
    entry['reviews']['visual']='not_reviewed'
    save_notes(json.dumps([entry]),notes,tmp_path)
    rows=[json.loads(line) for line in store.read_text().splitlines()]
    assert rows[-1]['result']=='not_reviewed'


def test_packaged_alignment_evidence_works_without_speech_engine(tmp_path,monkeypatch):
    from course.tools import ears
    from course.tools.narration_assets import validate_alignment_evidence
    from course.stage.card import load_manifest
    import sys
    monkeypatch.setattr(ears,'CACHE',tmp_path/'missing-cache')
    monkeypatch.setitem(sys.modules,'mlx_whisper',None)
    words=ears.transcribe('6.1.question',load_manifest()['6.1.question'])
    assert words and all(len(row)==3 for row in words)
    assert validate_alignment_evidence()==[]
