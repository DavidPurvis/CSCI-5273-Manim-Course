"""Pure frame schedule shared by the renderer and assembly tools."""
import math,re
from course.contracts import BeatTimeline,DishTimeline,PhraseAnchor

CRITICAL_MOVES=frozenset(('graph.promote','graph.relax','tunnel.reencapsulate','packet.wrap','packet.unwrap','bits.draw_mask','bar.cut','bar.slice'))


def resolve_anchor(anchor, text, times, speech, fps=30):
    if isinstance(anchor,str):anchor=PhraseAnchor(anchor)
    hits=list(re.finditer(re.escape(anchor.phrase),text))
    if len(hits)>1 and anchor.occurrence is None:raise ValueError('ambiguous phrase occurrence')
    occurrence=anchor.occurrence or 1
    if occurrence<1 or occurrence>len(hits):raise ValueError(f'anchor not found: {anchor.phrase}')
    at=hits[occurrence-1].start();idx=len(text[:at].split())
    t=times[idx][0] if times and idx<len(times) else speech*at/max(len(text),1)
    return round(t*fps)+anchor.frame_offset


def compile_beat(beat,asset,alignment,text='',pad=2.2,fps=30,defaults=None):
    defaults=defaults or {};speech=asset['duration'];speech_frames=math.ceil(speech*fps)
    adj=beat.get('adjust') or {};pace=adj.get('pace',1)
    if pace<=0:raise ValueError('pace must be positive')
    pre_roll=round(beat.get('pre_roll',0)*fps)
    if pre_roll<0:raise ValueError('pre_roll must be nonnegative')
    hold=round((beat.get('hold',0)+adj.get('hold',0))*fps)
    reading=round(beat.get('reading_hold',0)*fps)
    total=pre_roll+speech_frames+round(pad*fps)+hold+reading+(6 if hold else 0)
    moves=[]
    for i,raw in enumerate(beat.get('moves') or []):
        name=next(k for k in raw if k not in ('when','t','event_id'))
        args=dict(raw[name] or {});when=raw.get('when',args.pop('when',None));duration=raw.get('t',args.pop('t',defaults.get(name,1)))
        occurrence=args.pop('occurrence',None)
        if isinstance(when,dict):anchor=PhraseAnchor(when['phrase'],when.get('occurrence'),when.get('frame_offset',0))
        elif when:anchor=PhraseAnchor(when,occurrence)
        else:anchor=None
        start=pre_roll+resolve_anchor(anchor,text,alignment,speech,fps) if anchor else None
        moves.append(dict(event_id=raw.get('event_id',f"{beat['id']}:move:{i}"),name=name,args=args,start=start,frames=max(1,round(duration*pace*fps))))
    now=0
    for i,m in enumerate(moves):
        following=moves[i+1] if i+1<len(moves) else None
        # A clear is not a step. It runs right before what replaces it, so narration never plays over an empty screen.
        if m['name']=='clear' and m['start'] is None and following and following['start'] is not None:
            m['start']=max(now,following['start']-m['frames'])
        anchored=m['start'] is not None
        if anchored:
            if m['start']<now:raise ValueError(f"{beat['id']}: anchor {m['event_id']} overlaps preceding animation by {(now-m['start'])/fps:.2f}s")
            now=m['start']
        source=m['args'].get('data') if isinstance(m['args'].get('data'),dict) else m['args']
        rows=source.get('rows')
        # A table with nothing competing for the time builds row by row as the narration reads it.
        if m['name']=='table.show' and isinstance(rows,list) and len(rows)>=3 and m['args'].get('show') is None and beat['stage']!='prediction':
            later=[x for x in moves[i+1:] if x['name']!='keep']
            if not later or later[0]['start'] is not None:
                end=later[0]['start'] if later else pre_roll+speech_frames
                m['frames']=max(m['frames'],min(round(2.5*fps*len(rows)),round(.8*(end-now))))
        m['start']=now;now+=m['frames']
        if not anchored and m['name']!='clear':
            j=next((j for j in range(i+1,len(moves)) if moves[j]['start'] is not None),len(moves))
            end=moves[j]['start'] if j<len(moves) else pre_roll+speech_frames
            need=sum(x['frames'] for x in moves[i+1:j])
            now+=max(0,(end-now-need)//max(1,j-i))
    if now>total-hold-reading-(6 if hold else 0):raise ValueError(f"{beat['id']}: animation exceeds speech/pad budget")
    prediction=(total-hold-6,total-6) if hold and beat['stage']=='prediction' else None
    captions = build_captions(text, alignment, {'speech': speech}) if alignment else []
    for cue in captions:
        cue['start']+=pre_roll;cue['end']+=pre_roll
    return BeatTimeline(beat['id'],total,(pre_roll,pre_roll+speech_frames),moves,captions=captions,reading=(total-reading,total) if reading else None,prediction=prediction,cleanup=(total-6,total) if prediction else None)


def compile_dish(card,manifest,timing,texts,defaults=None):
    beats=[]
    for b in card['beats']:
        from course.stage.card import word_times
        item=timing.get(b['id'],{});times=word_times(b['id'],manifest,timing)
        provenance=item.get('provenance',[])
        for raw in b.get('moves',[]):
            name=next(k for k in raw if k not in ('when','t','event_id'))
            args=raw[name] or {};when=raw.get('when',args.get('when'))
            if not when or name not in CRITICAL_MOVES:continue
            anchor=when if isinstance(when,dict) else {'phrase':when,'occurrence':args.get('occurrence')}
            hits=list(re.finditer(re.escape(anchor['phrase']),texts[b['id']]))
            occurrence=anchor.get('occurrence') or 1
            if not hits or occurrence>len(hits):raise ValueError(f"{b['id']}: missing important phrase")
            index=len(texts[b['id']][:hits[occurrence-1].start()].split())
            if index>=len(provenance) or provenance[index] not in ('asr_aligned','manually_corrected','synthesizer_aligned'):
                raise ValueError(f"{b['id']}: important anchor {anchor['phrase']!r} needs observed or corrected timing")
        beats.append(compile_beat(b,manifest[b['id']],times,texts[b['id']],card.get('pad',2.2),defaults=defaults))
    return DishTimeline(card['dish'],30,beats,sum(b.frames for b in beats))


def validate_timeline(timeline):
    errors=[]
    for b in timeline.beats:
        for m in b.moves:
            if m['start']<0 or m['start']+m['frames']>b.frames:errors.append(f"{b.beat_id}: move outside interval")
    return errors


def build_assembly_plan(members,output_id):
    from course.contracts import AssemblyPlan
    offsets={};now=0
    for t in members:offsets[t.dish_id]=now;now+=t.total_frames
    return AssemblyPlan(output_id,[t.dish_id for t in members],offsets,now)


def validate_word_alignment(asset,alignment):
    errors=[]
    if len(alignment.provenance)!=len(alignment.intervals):errors.append('word provenance length mismatch')
    last=0
    for start,end in alignment.intervals:
        if not 0<=start<=end or start<last:errors.append('nonmonotonic word interval')
        last=start
    if asset.wav_hash!=alignment.narration_identity:errors.append('stale waveform alignment')
    return errors


def build_captions(text,alignment,policy=None):
    from course.stage.card import timed_cues
    times=alignment.intervals if hasattr(alignment,'intervals') else alignment
    speech=(policy or {}).get('speech',times[-1][1] if times else 0)
    return [dict(text=c,start=round(a*30),end=round((a+d)*30)) for c,a,d in timed_cues(text,speech,times)]


def validate_captions(cues,timeline):
    from course.stage.card import MAX_CPS
    errors=[];end=0
    for c in cues:
        if c['start']<end or c['end']<=c['start'] or c['end']>timeline.frames:errors.append('caption interval invalid')
        if len(c['text'])>84:errors.append('caption exceeds two-line text budget')
        if len(c['text'])/max((c['end']-c['start'])/30,.001)>MAX_CPS:errors.append('caption reading speed exceeds policy')
        end=c['end']
    return errors


def export_transcript(plan,catalog):
    from course.stage.card import load_card,narration_text
    texts=narration_text();lines=[]
    for dish in plan.members:
        lines.append(f'## {dish}')
        # Offsets are explicitly attached to the output the member belongs to.
        lines.append(f'Output {plan.output_id}, starts at frame {plan.offsets[dish]}')
        for b in load_card(dish)['beats']:lines.append(f"{b['id']} ({b['pdf']}): {texts[b['id']]}")
    return '\n\n'.join(lines)
