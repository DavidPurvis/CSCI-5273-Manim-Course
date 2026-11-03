"""Provider-free regression tests for production synthesis and evidence."""
import base64
import io
import json
from types import SimpleNamespace
import urllib.error
import pytest
from course.tools import narration_pipeline as n
from course.tools.tts import clip_key

@pytest.fixture(autouse=True)
def isolate(monkeypatch,tmp_path):
    monkeypatch.setattr(n,'ROOT',tmp_path);monkeypatch.setattr(n,'_key',None);n.STOP.clear()
    yield
    n.STOP.clear()

def payload():
    return {'audio_base64':base64.b64encode(b'\0\0'*2400).decode(),
            'alignment':{'characters':['H','i'], 'character_start_times_seconds':[0,.04],
                         'character_end_times_seconds':[.04,.08]}}

def test_key_environment_precedes_keychain(monkeypatch):
    monkeypatch.setenv('ELEVENLABS_API_KEY','private-test-value')
    monkeypatch.setattr(n.subprocess,'run',lambda *a,**k:pytest.fail('Keychain should not run'))
    assert n.get_elevenlabs_key()=='private-test-value'

def test_keychain_error_is_redacted(monkeypatch):
    monkeypatch.delenv('ELEVENLABS_API_KEY',raising=False)
    monkeypatch.setattr(n.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1,stdout='secret',stderr='secret'))
    with pytest.raises(RuntimeError) as error:n.get_elevenlabs_key()
    assert 'secret' not in str(error.value)

def test_request_retry_cache_and_terminal_quota(monkeypatch):
    monkeypatch.setenv('ELEVENLABS_API_KEY','private-test-value')
    delays=[];monkeypatch.setattr(n.time,'sleep',delays.append)
    calls=[]
    class Response(io.BytesIO):
        headers={'request-id':'test','x-character-count':'2'}
    def request(*a,**k):
        calls.append(1)
        if len(calls)==1:raise urllib.error.HTTPError('url',429,'rate',{'Retry-After':'2'},io.BytesIO(b'busy'))
        return Response(json.dumps(payload()).encode())
    monkeypatch.setattr(n.urllib.request,'urlopen',request)
    first=n.request_piece('Hi',n.CONFIG);second=n.request_piece('Hi',n.CONFIG)
    assert first==second and len(calls)==2 and delays==[2]
    def quota(*a,**k):raise urllib.error.HTTPError('url',429,'rate',{},io.BytesIO(b'quota_exceeded'))
    monkeypatch.setattr(n.urllib.request,'urlopen',quota)
    with pytest.raises(RuntimeError,match='HTTP 429'):n.request_piece('Next',n.CONFIG)
    assert n.STOP.is_set()

def test_alignment_rejects_malformed_and_out_of_bounds():
    p=payload()['alignment'];n.validate_alignment(p,.1)
    for field,value in [('characters',['H']),('character_start_times_seconds',[0,float('nan')]),
                        ('character_end_times_seconds',[.04,2])]:
        with pytest.raises(ValueError):n.validate_alignment(dict(p,**{field:value}),.1)

def test_silence_offsets_and_explicit_provenance():
    from course.tools.ears import align
    side={'duration':1.0,'pieces':[{'offset':.6,'duration':.1,'characters':['H','i'], 'starts':[0,.04],'ends':[.04,.08]}]}
    heard=n.heard_words(side)
    assert heard==[['Hi',.6,pytest.approx(.68)]]
    result=align(['Hi','there'],heard,1,[])
    assert result.provenance==['asr_aligned','interpolated']
    assert not hasattr(align,'last_provenance')

def test_exact_dish_selection(monkeypatch):
    monkeypatch.setattr(n,'narration_text',lambda:{'6.1.a':'a','6.10.a':'b','16.1.a':'c'})
    assert n.selected(SimpleNamespace(all=False,dish='6.1',chapter=None))=={'6.1.a':'a'}

def test_identity_includes_settings():
    a=clip_key('Hi',n.CONFIG)
    assert a!=clip_key('Hi',dict(n.CONFIG,voice_settings={'speed':.9}))
    assert a!=clip_key('Hi',dict(n.CONFIG,model_id='other'))

def test_resume_reuses_completed_piece(monkeypatch,tmp_path):
    monkeypatch.setattr(n,'get_elevenlabs_key',lambda:'test')
    calls=[]
    class Response(io.BytesIO):headers={}
    monkeypatch.setattr(n.urllib.request,'urlopen',lambda *a,**k:(calls.append(1) or Response(json.dumps(payload()).encode())))
    n.raw_provider('Hi [[slnc 600]] Hi',tmp_path/'a.wav',n.CONFIG)
    n.raw_provider('Hi [[slnc 600]] Hi',tmp_path/'b.wav',n.CONFIG)
    assert len(calls)==1
    side=json.loads((tmp_path/'a.alignment.json').read_text())
    assert side['pieces'][1]['offset']==pytest.approx(.7)
