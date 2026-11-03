import pytest
from course.contracts import PhraseAnchor
from course.stage.timeline import resolve_anchor,compile_beat,build_assembly_plan


def test_anchor_occurrences():
    with pytest.raises(ValueError):resolve_anchor(PhraseAnchor('A',None),'A A',[[0,1],[2,3]],3)
    assert resolve_anchor(PhraseAnchor('A',2),'A A',[[0,1],[2,3]],3)==60


def test_mutating_move_not_created_by_compiler():
    b=dict(id='x',stage='prediction',hold=6,moves=[{'text':{'text':'x'},'when':'later'}])
    t=compile_beat(b,{'duration':4},[[0,1],[2,3]],'first later')
    assert t.moves[0]['start']==60 and t.prediction[0]>=120


def test_setup_precedes_speech_and_caption_offsets():
    beat={'id':'setup','stage':'animation','pre_roll':1.5,'moves':[
        {'clear':{},'t':0.5}, {'show':{},'t':1},
        {'mark':{},'when':'Hello','t':0.5}]}
    timeline=compile_beat(beat,{'duration':2},[[0,0.8],[1,2]],'Hello world')
    assert timeline.speech==(45,105)
    assert timeline.moves[1]['start']+timeline.moves[1]['frames']==45
    assert timeline.moves[2]['start']==timeline.speech[0]
    assert timeline.captions[0]['start']==timeline.speech[0]
    assert timeline.frames==171


def test_setup_does_not_hide_an_internal_anchor_conflict():
    beat={'id':'conflict','stage':'animation','pre_roll':2,'moves':[
        {'first':{},'when':'First','t':2},
        {'second':{},'when':'second','t':1}]}
    with pytest.raises(ValueError,match='overlaps'):
        compile_beat(beat,{'duration':3},[[0,1],[1,2]],'First second')


def test_export_captions_follow_compiled_schedule():
    from course.tools.kitchen import cues_for
    from course.stage.card import load_card,load_manifest,load_timing,narration_text,beat_times
    from course.stage.timeline import compile_dish
    from course.stage.moves import REGISTRY
    card=load_card('6.2');manifest=load_manifest()
    compiled=compile_dish(card,manifest,load_timing(),narration_text(),{k:v['t'] for k,v in REGISTRY.items()})
    slots,total=beat_times(card,manifest)
    assert round(total*30)==compiled.total_frames
    cues=cues_for('6.2',offset=10)
    for beat,slot in zip(compiled.beats,slots):
        actual=[c for c in cues if c['beat']==beat.beat_id]
        assert round(actual[0]['start']*30)==300+round(slot['start']*30)+beat.captions[0]['start']


def test_readable_captions_use_actual_word_boundaries():
    from course.stage.captioning import aligned_cues,fits_lines
    text='Discover: is any DHCP server out there? Offer: a server proposes an address.'
    words=text.split();times=[[i*.4,(i+1)*.4] for i in range(len(words))]
    cues=aligned_cues(text,len(words)*.4,times)
    boundaries={round(t[0]*30) for t in times}
    assert ' '.join(c[0] for c in cues)==text
    for cue,start,duration in cues:
        assert round(start*30) in boundaries
        assert len(cue)/duration<=19.5
        assert fits_lines(cue.split())


def test_impossible_caption_timing_is_not_silently_shifted():
    from course.stage.captioning import aligned_cues
    with pytest.raises(ValueError,match='No caption grouping'):
        aligned_cues('unreadablyfast',.1,[[0,.1]])


def test_supplement_assembly_has_its_own_origin():
    from course.tools.assembly import course_plans
    plans=course_plans()
    assert plans['main'].offsets['6.1']==0
    assert plans['supplements'].offsets['17.1']==0
    assert all(int(x.split('.')[0])<=16 for x in plans['main'].members)
    assert all(int(x.split('.')[0])>16 for x in plans['supplements'].members)


def test_synthesizer_alignment_counts_as_observed_timing():
    from copy import deepcopy
    from course.stage.card import load_card, load_manifest, load_timing, narration_text
    from course.stage.moves import REGISTRY
    from course.stage.timeline import compile_dish
    card = load_card("10.1")
    timing = deepcopy(load_timing())
    texts = narration_text()
    beat = next(b for b in card["beats"] if b["id"] == "10.1.init")
    index = len(texts[beat["id"]].split("Start by settling")[0].split())
    timing[beat["id"]]["provenance"][index] = "synthesizer_aligned"
    compile_dish(card, load_manifest(), timing, texts, {k: v["t"] for k, v in REGISTRY.items()})


def test_important_anchor_rejects_inferred_timing():
    from copy import deepcopy
    from course.stage.card import load_card,load_manifest,load_timing,narration_text
    from course.stage.timeline import compile_dish
    from course.stage.moves import REGISTRY
    card=load_card('10.1');timing=deepcopy(load_timing());texts=narration_text()
    beat=next(b for b in card['beats'] if b['id']=='10.1.init')
    index=len(texts[beat['id']].split('Start by settling')[0].split())
    timing[beat['id']]['provenance'][index]='interpolated'
    with pytest.raises(ValueError,match='important anchor'):
        compile_dish(card,load_manifest(),timing,texts,{k:v['t'] for k,v in REGISTRY.items()})


def test_player_pause_matches_compiled_prediction_hold():
    """The study player must cover the video hold, not the pad that follows the last spoken word."""
    from course.stage.card import beat_times, load_card, load_manifest, load_timing, narration_text
    from course.stage.moves import REGISTRY
    from course.stage.timeline import compile_beat
    from course.tools.player_build import prediction_pause_time
    manifest, timing, texts = load_manifest(), load_timing(), narration_text()
    defaults = {k: v["t"] for k, v in REGISTRY.items()}
    checked = 0
    for dish in ("6.1", "10.1", "17.1"):
        card = load_card(dish)
        slots = {s["id"]: s for s in beat_times(card, manifest)[0]}
        pad = card.get("pad", 2.2)
        for beat in card["beats"]:
            if beat.get("stage") != "prediction":
                continue
            asset = manifest[beat["id"]]
            schedule = compile_beat(beat, asset, timing[beat["id"]]["t"], texts[beat["id"]], pad, defaults=defaults)
            absolute = slots[beat["id"]]["start"] + schedule.prediction[0] / 30
            assert abs(prediction_pause_time(beat, slots[beat["id"]], pad) - absolute) < 1 / 30
            checked += 1
    assert checked == 3


def test_long_idle_preserves_reading_time_without_artificial_motion():
    from course.stage.player import idle_slices
    assert idle_slices(42) == [("wait", 42)]
    assert idle_slices(0) == []


def test_elevenlabs_pause_marks_are_not_spoken_text():
    from course.tools.tts import clip_key, pause_pieces
    assert pause_pieces("Hello. [[slnc 600]] World") == [("text", "Hello."), ("silence", 600), ("text", "World")]
    shared = {"sentence_pause": 600, "clause_pause": 160}
    say = clip_key("Hello", dict(shared, engine="say", voice="Samantha", rate=140))
    eleven = clip_key("Hello", dict(shared, engine="elevenlabs", voice="voice-id", model_id="eleven_multilingual_v2"))
    assert say != eleven


def test_schedule_check_clears_every_dish_without_rendering():
    from course.tools.kitchen import schedule_problems
    assert schedule_problems() == []


def test_waveform_identity_is_required():
    from copy import deepcopy
    from course.stage.card import word_times,load_manifest,load_timing
    timing=deepcopy(load_timing());timing['6.1.question']['wav_hash']='wrong'
    with pytest.raises(ValueError,match='waveform bytes changed'):
        word_times('6.1.question',load_manifest(),timing)
