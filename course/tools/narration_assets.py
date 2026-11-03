"""Measured narration provenance; source and spoken text identities remain distinct."""
from dataclasses import asdict
import hashlib,json,wave
from course.contracts import NarrationAsset,Finding
from course.stage.card import ROOT,load_manifest,load_timing,narration_text
from course.tools.tts import CONFIG,load_rules,spoken_form,clip_key


def catalog_assets():
    manifest,timing,texts=load_manifest(),load_timing(),narration_text();_,rules=load_rules()
    config_hash=hashlib.sha256(json.dumps(CONFIG,sort_keys=True).encode()).hexdigest()
    records={};findings=[]
    for bid,text in texts.items():
        entry=manifest.get(bid,{})
        config=entry.get('config', CONFIG)
        _, asset_rules=load_rules(config)
        spoken=spoken_form(text,asset_rules,config)
        if entry.get('sha')!=clip_key(spoken,config):
            findings.append(Finding('NARRATION_TEXT','error',bid,'narration/manifest.json','written text, pronunciation or voice no longer matches cached speech','Regenerate narration and word alignment'));continue
        wav=ROOT/entry['wav']
        if not wav.exists():
            findings.append(Finding('NARRATION_AUDIO','error',bid,str(wav),'cached WAV is missing','Regenerate narration'));continue
        actual_hash=hashlib.sha256(wav.read_bytes()).hexdigest()
        with wave.open(str(wav),'rb') as sound:
            rate,count=sound.getframerate(),sound.getnframes()
            valid=rate==48000 and count>0 and sound.getnchannels()==1 and sound.getsampwidth()==2
        if not valid or abs(count/rate-entry['duration'])>.001:
            findings.append(Finding('NARRATION_FORMAT','error',bid,str(wav),'WAV format or measured duration differs','Regenerate narration and timing'))
        if timing.get(bid,{}).get('wav_hash')!=actual_hash:
            findings.append(Finding('NARRATION_ALIGNMENT','error',bid,str(wav),'word timing describes different WAV bytes','Rebuild word alignment'))
        records[bid]=asdict(NarrationAsset(bid,hashlib.sha256(text.encode()).hexdigest(),hashlib.sha256(spoken.encode()).hexdigest(),hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),actual_hash,rate,count))
    return records,findings


def write_catalog():
    records,findings=catalog_assets()
    if findings:raise ValueError('; '.join(f'{x.artifact_id}: {x.message}' for x in findings))
    (ROOT/'narration/assets.json').write_text(json.dumps({'schema_version':1,'assets':records},indent=2))
    return records


def export_alignment_evidence():
    """Preserve used cached transcriptions; reuse packaged evidence for unchanged assets."""
    import shutil
    output=ROOT/'narration/alignment-evidence';output.mkdir(exist_ok=True)
    index=output/'manifest.json';previous=json.loads(index.read_text()).get('clips',{}) if index.exists() else {}
    manifest,timing=load_manifest(),load_timing();records={}
    for beat,asset in manifest.items():
        key=asset['sha'];cached=ROOT/'narration/.heard'/f'{key}.json';target=output/f'{key}.json'
        if cached.exists():shutil.copy2(cached,target)
        elif not (target.is_file() and previous.get(key,{}).get('wav_hash')==timing[beat]['wav_hash']):
            raise ValueError(f'{beat}: transcribe this new asset before exporting alignment evidence')
        records[key]={'file':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                      'wav_hash':timing[beat]['wav_hash'],'aligner':timing[beat]['aligner']}
    index.write_text(json.dumps({'schema_version':1,'scope':'Provider-labelled word alignment evidence; no listening review is implied.','clips':records},indent=2))
    return records


def validate_alignment_evidence():
    index=ROOT/'narration/alignment-evidence/manifest.json';findings=[]
    if not index.exists():return [Finding('ALIGNMENT_EVIDENCE','error','narration',str(index),'cached transcription evidence is missing','Prepare the packaged evidence')]
    records=json.loads(index.read_text()).get('clips',{});manifest=load_manifest();timing=load_timing()
    checked=set()
    for beat,asset in manifest.items():
        if asset['sha'] in checked:continue
        checked.add(asset['sha']);record=records.get(asset['sha'],{});path=index.parent/record.get('file','missing')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=record.get('sha256') or record.get('wav_hash')!=timing.get(beat,{}).get('wav_hash') or record.get('aligner')!=timing.get(beat,{}).get('aligner'):
            findings.append(Finding('ALIGNMENT_EVIDENCE','error',beat,str(path),'cached transcription evidence is missing or stale','Regenerate transcription, then prepare'))
    return findings
