"""Word-boundary caption grouping; readability never changes the spoken timestamps."""
import math


def fits_lines(words,width=42):
    if any(len(w)>width for w in words):return False
    if len(' '.join(words))<=width:return True
    return any(len(' '.join(words[:i]))<=width and len(' '.join(words[i:]))<=width for i in range(1,len(words)))


def aligned_cues(text,speech,times,max_cps=19.5):
    words=text.split();n=len(words)
    if len(times)!=n:raise ValueError('caption word mapping does not match text')
    starts=[round(t[0]*30) for t in times]+[math.ceil(speech*30)]
    costs=[float('inf')]*(n+1);next_word=[None]*(n+1);costs[n]=0
    for a in range(n-1,-1,-1):
        for b in range(a+1,n+1):
            cue=' '.join(words[a:b])
            if len(cue)>84:break
            frames=starts[b]-starts[a]
            if frames<=0 or len(cue)*30>max_cps*frames or not fits_lines(words[a:b]):continue
            sentence_end=words[b-1].endswith(('.', '?', '!'))
            cost=costs[b]+1+((len(cue)-56)/56)**2+(0 if sentence_end or b==n else .5)
            if cost<costs[a]:costs[a]=cost;next_word[a]=b
    if next_word[0] is None:
        raise ValueError('No caption grouping satisfies speech synchronization and readability')
    out=[];a=0
    while a<n:
        b=next_word[a]
        out.append((' '.join(words[a:b]),starts[a]/30,(starts[b]-starts[a])/30));a=b
    return out
