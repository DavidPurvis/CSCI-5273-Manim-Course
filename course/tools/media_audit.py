"""Decode and seek every delivered MP4; reuse only checks for identical verified bytes."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,subprocess,time
from pathlib import Path
from course.stage.card import ROOT
from course.tools.kitchen import PACK,BUILD,dishes,verify_playback,run


def sha256(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def inspect_media(path):
    identity=sha256(path)
    findings,seconds=verify_playback(path)
    data=json.loads(run(['ffprobe','-v','error','-count_packets','-show_streams','-show_chapters','-of','json',str(path)]).stdout)
    from course.tools.audio_continuity import inspect
    continuity=inspect(path)
    findings.extend(continuity['findings'])
    streams=data.get('streams',[])
    video=next((s for s in streams if s['codec_type']=='video'),{})
    if (video.get('width'),video.get('height'),video.get('r_frame_rate'))!=(1920,1080,'30/1'):findings.append('expected 1080p/30 fps')
    audio=next((s for s in streams if s['codec_type']=='audio'),{})
    if not audio or int(audio.get('nb_read_packets','0'))<=0:findings.append('missing or empty audio stream')
    if path.parent.name!='dishes':
        captions=next((s for s in streams if s['codec_type']=='subtitle'),{})
        if not captions or int(captions.get('nb_read_packets','0'))<=0:findings.append('missing or empty selectable caption stream')
    from course.catalog import MAIN, SUPPLEMENTS
    markers=len(MAIN) if path.name=='CSCI-5273-Lectures-06-15.mp4' else len(SUPPLEMENTS) if path.name=='CSCI-5273-Practice-and-Warm-up.mp4' else None
    if markers is not None and len(data.get('chapters',[]))!=markers:findings.append(f'expected {markers} chapter markers')
    if sha256(path)!=identity:findings.append('artifact changed during verification')
    return {'path':str(path.relative_to(PACK)),'sha256':identity,'seconds':seconds,'findings':findings,'verified_at':time.time(),'audio_continuity':continuity}



def verification_identity():
    from course.tools import kitchen
    return hashlib.sha256((Path(__file__).read_text()+Path(kitchen.__file__).read_text()).encode()).hexdigest()


def main():
    output=BUILD/'media-audit.json'
    verification_fingerprint=verification_identity()
    previous=json.loads(output.read_text()) if output.exists() else {}
    cached={row['sha256']:row for row in previous.get('artifacts',[]) if not row['findings']} if previous.get('verification_fingerprint')==verification_fingerprint else {}
    paths=sorted((PACK/'video').rglob('*.mp4'));results=[];todo=[]
    for path in paths:
        identity=sha256(path)
        if identity in cached:
            results.append(dict(cached[identity],path=str(path.relative_to(PACK)),reused=True))
        else:todo.append(path)
    with ThreadPoolExecutor(3) as pool:
        pending={pool.submit(inspect_media,p):p for p in todo}
        for task in as_completed(pending):
            path=pending[task]
            try:row=task.result()
            except (OSError,ValueError,subprocess.CalledProcessError) as exc:
                row={'path':str(path.relative_to(PACK)),'sha256':sha256(path),'findings':[str(exc)],'verified_at':time.time()}
            results.append(row)
            print(('FAIL ' if row['findings'] else 'PASS ')+row['path'],flush=True)
    expected=len(dishes())+len({d.split('.')[0] for d in dishes()})+2
    findings=[] if len(paths)==expected else [f'{len(paths)} delivered MP4s found; expected {expected}']
    report={'verification_fingerprint':verification_fingerprint,'expected_mp4_count':expected,'artifacts':sorted(results,key=lambda r:r['path']),
            'findings':findings,'automatic_media_verified':not findings and all(not r['findings'] for r in results),
            'perceptual_review':'separate explicit evidence required'}
    output.write_text(json.dumps(report,indent=2))
    print('MEDIA VERIFIED' if report['automatic_media_verified'] else 'MEDIA FINDINGS REMAIN',flush=True)
    return int(not report['automatic_media_verified'])

if __name__=='__main__':raise SystemExit(main())
