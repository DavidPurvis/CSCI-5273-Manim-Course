"""Prep aid: the same paragraph in each candidate voice, for the owner to choose by ear."""
import json
import os
import subprocess
import sys
import urllib.request

from course.stage.card import ROOT
from course.tools.tts import CONFIG, load_rules, render_clip, spoken_form

TEXT = ("A host at 10.10.1.97/23 wants to reach a web server. Its mask says the destination is remote, so ARP finds the gateway's MAC address, "
        "and the Ethernet frame goes to the router. At each hop, TTL drops by one, and longest prefix match picks the output. "
        "Those tables came from the control plane: Dijkstra's algorithm in OSPF inside an AS, and BGP between ASes. "
        "If a link fails, we can get a transient forwarding loop until every router converges.")
VOICES = {"1-samantha": dict(CONFIG, engine="say", voice="Samantha", rate=140),
          "2-kokoro-heart": dict(CONFIG, engine="kokoro", voice="af_heart", speed=1.0),
          "3-kokoro-michael": dict(CONFIG, engine="kokoro", voice="am_michael", speed=1.12)}
OUT = ROOT.parent.parent / "CSCI-5273-Manim-Course-archive-before-review-notes" / "kitchen-trial" / "voices"


def eleven_audition(limit=3, model_id="eleven_multilingual_v2", voice_ids=None):
    """Speak the audition paragraph in a few account voices. Does not change voice.yaml or any dish."""
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise SystemExit("ELEVENLABS_API_KEY is not set. No voice was synthesized.")
    req = urllib.request.Request("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": key})
    with urllib.request.urlopen(req, timeout=60) as resp:
        voices = json.loads(resp.read().decode()).get("voices") or []
    if voice_ids:
        by_id = {voice["voice_id"]: voice for voice in voices}
        missing = [vid for vid in voice_ids if vid not in by_id]
        if missing:
            raise SystemExit(f"Voice id not on this account: {', '.join(missing)}")
        picked = [by_id[vid] for vid in voice_ids[:limit]]
    else:
        picked = voices[:limit]
    if not picked:
        raise SystemExit("The account returned no voices.")
    dest = ROOT / "build" / "voice-pilot" / "audition"
    dest.mkdir(parents=True, exist_ok=True)
    _, rules = load_rules(CONFIG)
    spoken = spoken_form(TEXT, rules, CONFIG)
    print(f"model {model_id}")
    print("Pick one voice id. Dish 1.1 is not rendered until you do.")
    for voice in picked:
        config = dict(CONFIG, engine="elevenlabs", voice=voice["voice_id"], model_id=model_id)
        wav = dest / f"{voice['name'].replace(' ', '-')}.wav"
        render_clip(spoken, wav, config)
        print(f"{voice['name']}: {voice['voice_id']} -> {wav}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "elevenlabs":
        model = sys.argv[2] if len(sys.argv) > 2 else "eleven_multilingual_v2"
        ids = sys.argv[3].split(",") if len(sys.argv) > 3 else None
        eleven_audition(model_id=model, voice_ids=ids)
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for name, config in VOICES.items():
        _, rules = load_rules(config)
        wav = OUT / f"{name}.wav"
        render_clip(spoken_form(TEXT, rules, config), wav, config)
        secs = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)], capture_output=True, text=True).stdout)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-c:a", "aac", "-b:a", "128k", str(wav.with_suffix(".m4a"))], check=True)
        print(f"{name}: {secs:.1f} s, {len(TEXT.split()) / secs * 60:.0f} wpm")


if __name__ == "__main__":
    main()
