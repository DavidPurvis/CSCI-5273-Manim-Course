"""Prepared prediction contracts reference the actual compiled beats and events."""
import json
from pathlib import Path
from course.contracts import Finding
from course.stage.card import ROOT,load_card


def load_prediction_contracts():
    path=ROOT/'recipes/predictions.json'
    return json.loads(path.read_text())['predictions'] if path.exists() else []


def validate_prediction_contracts(timelines):
    contracts=load_prediction_contracts();by_id={c['prediction_beat']:c for c in contracts};findings=[]
    expected={b['id'] for path in (ROOT/'recipes').glob('*.yaml') for b in load_card(path.stem)['beats'] if b['stage']=='prediction'}
    def fail(artifact,message):findings.append(Finding('PREDICTION_CONTRACT','error',artifact,'recipes/predictions.json',message,'Correct authoritative prediction_contracts and prepare again'))
    if set(by_id)!=expected or len(by_id)!=len(contracts):fail('predictions','prediction declarations must cover every actual prediction exactly once')
    evidence=[]
    for timeline in timelines:
        by_beat={b.beat_id:b for b in timeline.beats};offsets={};cursor=0
        for beat in timeline.beats:offsets[beat.beat_id]=cursor;cursor+=beat.frames
        for contract in contracts:
            pred_id=contract['prediction_beat']
            if pred_id not in by_beat:continue
            pred=by_beat[pred_id];answer=by_beat.get(contract['answer_beat'])
            if not pred.prediction or not answer or offsets[answer.beat_id]<offsets[pred_id]+pred.frames:
                fail(pred_id,'answer must follow the complete prediction interval');continue
            actual={m['event_id']:m for m in answer.moves}
            if not contract['answer_objects'] or any(event not in actual for event in contract['answer_events']):
                fail(pred_id,'missing answer object or referenced answer event');continue
            for obj in contract['answer_objects']:
                if obj['after'] not in contract['answer_events'] or obj['before_answer']!='hidden_or_neutral':fail(pred_id,'invalid protection selector')
            evidence.append({'prediction_beat':pred_id,'answer_beat':answer.beat_id,
                             'protected_frames':[offsets[pred_id],offsets[answer.beat_id]],
                             'answer_events':[{**actual[event],'start':offsets[answer.beat_id]+actual[event]['start']} for event in contract['answer_events']],
                             'answer_objects':contract['answer_objects'],
                             'structural_result':'answer events follow the prediction hold',
                             'perceptual_result':'hidden or neutral object state still requires current visual/content review'})
    output=ROOT/'build/prediction-verification.json';output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({'predictions':evidence,'findings':[f.__dict__ for f in findings]},indent=2))
    return findings
