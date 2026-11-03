"""Packet/sample coverage checks, independent of perceived narration quality."""
import json
import subprocess

def inspect(path):
    result=subprocess.run(['ffprobe','-v','error','-select_streams','a:0','-show_packets','-show_streams',
                           '-show_entries','packet=pts_time,duration_time:stream=sample_rate,duration',
                           '-of','json',str(path)],capture_output=True,text=True,check=True)
    data=json.loads(result.stdout);packets=data.get('packets',[]);streams=data.get('streams',[])
    if not packets or not streams:return {'findings':['missing audio packets']}
    rate=int(streams[0]['sample_rate']);previous=None;gaps=[];nonmonotonic=[]
    for p in packets:
        start=float(p['pts_time']);duration=float(p.get('duration_time',0))
        if previous:
            if start < previous[0]:nonmonotonic.append(start)
            gap=start-previous[1]
            if gap>2/rate:gaps.append({'at':start,'seconds':gap})
        previous=(start,start+duration)
    # Decode to count actual output samples without retaining a large PCM file.
    proc=subprocess.Popen(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-ac','1','-ar',str(rate),
                           '-f','s16le','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    count=0
    while chunk:=proc.stdout.read(1024*1024):count+=len(chunk)
    errors=proc.stderr.read().decode();code=proc.wait()
    duration=float(streams[0].get('duration',0));decoded=count/2/rate
    findings=[]
    if gaps:findings.append(f'{len(gaps)} audio packet gaps above two samples')
    if nonmonotonic:findings.append('nonmonotonic audio timestamps')
    if code or errors.strip():findings.append('audio decode error')
    # AAC may contain one final partial codec frame; do not misreport it as drift.
    if abs(decoded-duration)>1024/rate+.002:findings.append('decoded coverage differs by more than one AAC frame')
    return {'sample_rate':rate,'packets':len(packets),'decoded_seconds':decoded,'stream_seconds':duration,
            'gaps':gaps,'nonmonotonic':nonmonotonic,'findings':findings}
