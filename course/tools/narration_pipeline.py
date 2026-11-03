"""Resumable provider synthesis and timestamp alignment. No implicit ASR calls."""
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import wave

from course.stage.card import ROOT, narration_text, load_manifest, load_timing
from course.tools.tts import CONFIG, clip_key, load_rules, pause_pieces, render_clip, spoken_form

STOP = threading.Event()
KEY_LOCK = threading.Lock()
_key = None

def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False)
        tmp = handle.name
    os.replace(tmp, path)


def get_elevenlabs_key():
    """Never include credential output in exceptions or logs."""
    global _key
    with KEY_LOCK:
        if os.environ.get('ELEVENLABS_API_KEY'):
            return os.environ['ELEVENLABS_API_KEY']
        if _key:
            return _key
        try:
            result = subprocess.run(['security', 'find-generic-password', '-s', 'elevenlabs', '-w'],
                                    capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired):
            raise RuntimeError('ElevenLabs credential unavailable; set the environment key or unlock Keychain') from None
        if result.returncode or not result.stdout.strip():
            raise RuntimeError('ElevenLabs credential unavailable in environment and Keychain')
        _key = result.stdout.strip()
        return _key


def piece_body(text, config):
    return {'text': text, 'model_id': config['model_id'],
            'voice_settings': config.get('voice_settings', {})}


def piece_path(text, config):
    identity = {'voice': config['voice'], 'format': 'pcm_24000', 'body': piece_body(text, config)}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return ROOT / 'narration/request-cache' / (key + '.json')


def validate_alignment(alignment, duration):
    chars = alignment.get('characters', [])
    starts = alignment.get('character_start_times_seconds', [])
    ends = alignment.get('character_end_times_seconds', [])
    if not chars or len(chars) != len(starts) or len(chars) != len(ends):
        raise ValueError('Missing or unequal provider character timestamp arrays')
    last = 0.0
    for ch, start, end in zip(chars, starts, ends):
        if not isinstance(ch, str) or not ch or not all(isinstance(v, (int,float)) and math.isfinite(v) for v in (start,end)):
            raise ValueError('Invalid character or nonfinite timestamp')
        if start < last or not 0 <= start <= end <= duration + .025:
            raise ValueError('Provider timestamp outside audio or out of order')
        last = start


def validate_payload(payload):
    pcm = base64.b64decode(payload['audio_base64'], validate=True)
    if not pcm or len(pcm) % 2:
        raise ValueError('Invalid 16-bit PCM response')
    duration = len(pcm) / 48000
    validate_alignment(payload.get('alignment') or {}, duration)
    if payload.get('normalized_alignment'):
        validate_alignment(payload['normalized_alignment'], duration)
    return pcm


def retry_delay(header, attempt):
    try:
        value = float(header)
    except (ValueError,TypeError):
        try:
            value = (parsedate_to_datetime(header) - datetime.now(timezone.utc)).total_seconds()
        except (ValueError,TypeError,OverflowError):
            value = min(30, 2 ** attempt) + random.random()
    return max(0, min(value, 60))


def request_piece(text, config):
    path = piece_path(text, config)
    if path.exists():
        payload = json.loads(path.read_text()); validate_payload(payload)
        return payload
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config['voice']}/with-timestamps?output_format=pcm_24000"
    req = urllib.request.Request(url, data=json.dumps(piece_body(text,config)).encode(), method='POST',
          headers={'xi-api-key': get_elevenlabs_key(), 'Content-Type': 'application/json'})
    for attempt in range(5):
        if STOP.is_set():
            raise RuntimeError('Synthesis stopped after an earlier failure; completed requests are cached')
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                payload = json.loads(response.read())
                payload['request_id'] = response.headers.get('request-id')
                payload['charged_characters'] = response.headers.get('x-character-count')
            validate_payload(payload)
            atomic_json(path, payload)
            return payload
        except urllib.error.HTTPError as error:
            # Inspect error codes internally; never echo provider bodies or request headers.
            detail = error.read().decode(errors='replace')
            terminal = error.code in (401,403,422) or 'quota_exceeded' in detail
            if terminal or error.code not in (429,500,502,503,504) or attempt == 4:
                STOP.set()
                raise RuntimeError(f'ElevenLabs HTTP {error.code}; synthesis stopped, cached requests retained') from None
            time.sleep(retry_delay(error.headers.get('Retry-After'),attempt))
        except (urllib.error.URLError, TimeoutError):
            if attempt == 4:
                STOP.set()
                raise RuntimeError('ElevenLabs network request failed after bounded retries') from None
            time.sleep(retry_delay(None,attempt))


def raw_provider(spoken, path, config):
    frames = bytearray(); pieces = []
    for kind,value in pause_pieces(spoken):
        if kind == 'silence':
            frames.extend(b'\0\0' * round(24000 * value / 1000)); continue
        payload = request_piece(value,config)
        pcm = validate_payload(payload)
        alignment = payload.get('normalized_alignment') or payload['alignment']
        pieces.append({'offset': len(frames)/48000, 'duration':len(pcm)/48000,
                       'characters':alignment['characters'], 'starts':alignment['character_start_times_seconds'],
                       'ends':alignment['character_end_times_seconds'],
                       'alignment':payload['alignment'], 'normalized_alignment':payload.get('normalized_alignment'),
                       'request_id':payload.get('request_id'),'charged_characters':payload.get('charged_characters')})
        frames.extend(pcm)
    with wave.open(str(path),'wb') as sound:
        sound.setnchannels(1);sound.setsampwidth(2);sound.setframerate(24000);sound.writeframes(frames)
    atomic_json(Path(path).with_suffix('.alignment.json'),
                {'provider':'elevenlabs','model':config['model_id'],'voice':config['voice'],
                 'sample_rate':24000,'duration':len(frames)/48000,'pieces':pieces})


def heard_words(sidecar):
    words=[]; last_piece_end=0
    for p in sidecar['pieces']:
        offset=p['offset']; duration=p['duration']
        if not math.isfinite(offset) or offset < last_piece_end - .001:
            raise ValueError('Invalid piece offset')
        validate_alignment({'characters':p['characters'],'character_start_times_seconds':p['starts'],
                            'character_end_times_seconds':p['ends']}, duration)
        buf='';start=None;end=None
        for char,at,stop in zip(p['characters'],p['starts'],p['ends']):
            if char.isspace():
                if buf:words.append([buf,offset+start,offset+end])
                buf='';start=None
            else:
                if start is None:start=at
                buf+=char;end=stop
        if buf:words.append([buf,offset+start,offset+end])
        last_piece_end=offset+duration
    if last_piece_end > sidecar['duration']+.001:raise ValueError('Piece exceeds raw audio')
    return words


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def valid_clip(path):
    side=path.with_suffix('.alignment.json')
    if not path.exists() or not side.exists():return False
    try:
        metadata=json.loads(side.read_text())
        return metadata.get('wav_hash') == file_hash(path)
    except (OSError,ValueError):return False


def synthesize(text, config):
    _,rules=load_rules(config);spoken=spoken_form(text,rules,config);key=clip_key(spoken,config)
    wav=ROOT/'narration/audio'/f'{key}.wav';wav.parent.mkdir(exist_ok=True)
    if not valid_clip(wav):
        # Commit the pair in a temporary directory, with the sidecar as completion marker.
        with tempfile.TemporaryDirectory(dir=wav.parent) as tmp:
            candidate=Path(tmp)/'clip.wav';render_clip(spoken,candidate,config)
            with wave.open(str(candidate),'rb') as sound:duration=sound.getnframes()/sound.getframerate()
            side=candidate.with_suffix('.alignment.json');metadata=json.loads(side.read_text())
            if abs(metadata['duration']-duration)>1/24000:
                raise ValueError('Audio processing changed duration; timestamp mapping requires investigation')
            heard_words(metadata)
            metadata.update(wav_hash=file_hash(candidate),processed_duration=duration,processing_version='pcm-loudnorm-v2')
            atomic_json(side,metadata)
            os.replace(candidate,wav);os.replace(side,wav.with_suffix('.alignment.json'))
    with wave.open(str(wav),'rb') as sound:duration=sound.getnframes()/sound.getframerate()
    return {'sha':key,'wav':str(wav.relative_to(ROOT)),'duration':round(duration,3),
            'words':len(text.split()),'voice':config['voice'],'model':config['model_id'],'config':config}


def selected(args):
    texts=narration_text()
    result={b:t for b,t in texts.items() if args.all or
            (args.dish and b.rsplit('.',1)[0]==args.dish) or
            (args.chapter and b.split('.')[0]==str(args.chapter))}
    if not result:raise ValueError('Selection contains no narration beats')
    return result


def narrate(args):
    texts=selected(args); _,rules=load_rules(CONFIG)
    missing={}
    clips=0
    for text in texts.values():
        spoken=spoken_form(text,rules,CONFIG)
        if valid_clip(ROOT/'narration/audio'/f'{clip_key(spoken,CONFIG)}.wav'):continue
        clips+=1
        for kind,value in pause_pieces(spoken):
            if kind=='text' and not piece_path(value,CONFIG).exists():missing[str(piece_path(value,CONFIG))]=value
    report={'beats':len(texts),'uncached_clips':clips,'uncached_requests':len(missing),
            'expanded_characters':sum(len(x) for x in missing.values()),'model':CONFIG['model_id'],'voice':CONFIG['voice']}
    print(json.dumps(report),flush=True)
    if args.dry_run:return 0
    if args.workers < 1 or args.workers > 8:raise ValueError('workers must be between 1 and 8')
    STOP.clear();manifest=load_manifest()
    # Equal text is synthesized once even when reused in different lessons.
    groups={}
    for bid,text in texts.items():groups.setdefault(text,[]).append(bid)
    try:
        with ThreadPoolExecutor(args.workers) as pool:
            jobs={pool.submit(synthesize,text,CONFIG):bids for text,bids in groups.items()}
            for future in as_completed(jobs):
                asset=future.result()
                for bid in jobs[future]:manifest[bid]=asset
                atomic_json(ROOT/'narration/manifest.json',manifest)
                print(f"Cached {', '.join(jobs[future])}",flush=True)
    except Exception:
        STOP.set();raise
    return 0


def align_selected(args):
    from course.tools.ears import align
    texts=selected(args);manifest=load_manifest();timing=load_timing()
    evidence=ROOT/'narration/alignment-evidence';index=evidence/'manifest.json'
    records=json.loads(index.read_text()).get('clips',{}) if index.exists() else {}
    for bid,text in texts.items():
        asset=manifest[bid]
        if asset.get('config',{}).get('engine')!='elevenlabs':
            raise ValueError(f'{bid}: not synthesizer audio; no automatic Whisper fallback')
        wav=ROOT/asset['wav']
        if not valid_clip(wav):raise ValueError(f'{bid}: incomplete or stale waveform/sidecar pair')
        side=json.loads(wav.with_suffix('.alignment.json').read_text());heard=heard_words(side)
        _,rules=load_rules(asset['config']);result=align(text.split(),heard,asset['duration'],rules)
        provenance=['synthesizer_aligned' if p=='asr_aligned' else p for p in result.provenance]
        item={'sha':asset['sha'],'t':result.times,'provenance':provenance,'wav_hash':file_hash(wav),
              'aligner':'elevenlabs:'+asset['model'],'mismatch_spans':result.mismatches,'corrections':[], 'match':result.ratio}
        # Preserve explicit corrections only when the exact audio/text alignment is unchanged.
        old=timing.get(bid,{})
        if old.get('wav_hash')==item['wav_hash'] and old.get('corrections'):
            item=old
        timing[bid]=item
        cached=ROOT/'narration/.heard'/f"{asset['sha']}.json"
        atomic_json(cached,heard)
        atomic_json(cached.with_suffix('.meta.json'),{'wav_hash':item['wav_hash'],'aligner':item['aligner']})
        target=evidence/cached.name;atomic_json(target,heard)
        records[asset['sha']]={'file':target.name,'sha256':file_hash(target),'wav_hash':item['wav_hash'],
                               'aligner':item['aligner'],'provider':'elevenlabs','sidecar_sha256':file_hash(wav.with_suffix('.alignment.json'))}
        atomic_json(ROOT/'narration/timing.json',timing)
        atomic_json(index,{'schema_version':1,'scope':'Provider-labelled alignment; not a listening review','clips':records})
        print(f"Aligned {bid}: {result.ratio:.3f}; {provenance.count('interpolated')} interpolated",flush=True)
    return 0


def add_commands(sub):
    for name,fn in [('narrate',narrate),('align',align_selected)]:
        parser=sub.add_parser(name);group=parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--dish');group.add_argument('--chapter');group.add_argument('--all',action='store_true')
        if name=='narrate':
            parser.add_argument('--dry-run',action='store_true');parser.add_argument('--workers',type=int,default=2)
        parser.set_defaults(fn=fn)
