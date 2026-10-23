"""Generate the recorded voices for the Tipp-Bücher.

Every spoken line of a tip book becomes one MP3 in audio/tipp/, named by the same key the
page computes (clipKey in Lesehefte A2.1.html), so the page finds it without a manifest.
Voices are Microsoft's free neural voices, fetched with the edge-tts package.

1. Export the line list: open Lesehefte A2.1.html, open the browser console and run
       copy(JSON.stringify(tipAllLines()))
   then paste it into tools/tipp-lines.json.
2. pip install edge-tts
3. python tools/make_voices.py            (only missing clips are generated)
   python tools/make_voices.py --prune    (also delete clips no longer used)

If you change a voice below, delete that speaker's clips (or the whole folder) and run it again.
"""
import asyncio, json, pathlib, sys
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "audio" / "tipp"
LINES = ROOT / "tools" / "tipp-lines.json"

# speaker -> (voice, rate, pitch)
VOICES = {
    "stift":     ("de-DE-SeraphinaMultilingualNeural", "-4%",  "+0Hz"),   # the magic pen
    "erz":       ("de-DE-FlorianMultilingualNeural",   "-6%",  "+0Hz"),   # narrator
    "shruti":    ("de-DE-AmalaNeural",                 "+0%",  "+0Hz"),
    "sijan":     ("de-DE-KillianNeural",               "+0%",  "+0Hz"),
    "lena":      ("de-DE-KatjaNeural",                 "+4%",  "+10Hz"),
    "huber":     ("de-AT-IngridNeural",                "-3%",  "+0Hz"),   # market seller
    "wagner":    ("de-DE-ConradNeural",                "-5%",  "-6Hz"),   # cheese and bread seller
    "frau":      ("de-DE-KatjaNeural",                 "-4%",  "-8Hz"),   # woman giving directions
    "durchsage": ("de-DE-ConradNeural",                "-10%", "-2Hz"),   # station announcement
    "tim":       ("de-DE-KillianNeural",               "+8%",  "+45Hz"),  # child
    "eismann":   ("de-AT-JonasNeural",                 "+0%",  "+0Hz"),   # ice cream seller
    "katze":     ("de-DE-AmalaNeural",                 "-10%", "+60Hz"),
    "hund":      ("de-DE-ConradNeural",                "-10%", "-30Hz"),
    "taube":     ("de-DE-KatjaNeural",                 "-20%", "+20Hz"),
    "ente":      ("de-DE-KillianNeural",               "+0%",  "+60Hz"),
    # Tipp-Buch 2 speakers
    "sie":       ("de-DE-KatjaNeural",                 "+0%",  "+0Hz"),
    "er":        ("de-DE-ConradNeural",                "+0%",  "+0Hz"),
    "kind":      ("de-DE-KillianNeural",               "+8%",  "+45Hz"),
    # Tipp-Buch 3: your own answers in the dialogues
    "ich":       ("de-DE-AmalaNeural",                 "+0%",  "+0Hz"),
    # Tipp-Buch 6: Familie Bär
    "mila":      ("de-DE-KatjaNeural",                 "+6%",  "+35Hz"),
    "ben":       ("de-DE-KillianNeural",               "+10%", "+60Hz"),
    "mama":      ("de-DE-AmalaNeural",                 "-2%",  "-4Hz"),
    "papa":      ("de-DE-ConradNeural",                "-2%",  "+0Hz"),
    "oma":       ("de-AT-IngridNeural",                "-10%", "-6Hz"),
    "reh":       ("de-CH-LeniNeural",                  "+0%",  "+0Hz"),
    "igel":      ("de-AT-JonasNeural",                 "-8%",  "-12Hz"),
}


async def make(item, sem, stats):
    path = OUT / f"{item['key']}.mp3"
    if path.exists() and path.stat().st_size > 0:
        stats["kept"] += 1
        return
    voice, rate, pitch = VOICES.get(item["s"], VOICES["stift"])
    async with sem:
        for attempt in range(4):
            try:
                tmp = path.with_suffix(".part")
                await edge_tts.Communicate(item["text"], voice, rate=rate, pitch=pitch).save(str(tmp))
                tmp.replace(path)
                stats["made"] += 1
                return
            except Exception as e:  # network hiccups: wait and retry
                if attempt == 3:
                    stats["failed"].append((item["key"], item["text"], str(e)))
                await asyncio.sleep(1.5 * (attempt + 1))


async def main():
    items = json.loads(LINES.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    stats = {"made": 0, "kept": 0, "failed": []}
    sem = asyncio.Semaphore(6)
    await asyncio.gather(*(make(i, sem, stats) for i in items))
    if "--prune" in sys.argv:
        used = {i["key"] for i in items}
        for f in OUT.glob("*.mp3"):
            if f.stem not in used:
                f.unlink()
    print(f"{len(items)} lines: {stats['made']} generated, {stats['kept']} already there, {len(stats['failed'])} failed")
    for k, t, e in stats["failed"]:
        print("  failed", k, t[:60], e)


if __name__ == "__main__":
    asyncio.run(main())
