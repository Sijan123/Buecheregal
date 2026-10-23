"""Check and preview the Tipp-Bücher without clicking through the app.

Uses a local Chrome or Edge in headless mode on a temporary copy of Lesehefte A2.1.html;
the book file itself is never changed.

    python tools/tipp_check.py verify                 # hotspots, game targets, question/answer alignment, speakers, voice clips, line endings
    python tools/tipp_check.py list                   # books, scenes and the art each scene uses
    python tools/tipp_check.py lines                  # export every spoken line to tools/tipp-lines.json
    python tools/tipp_check.py shot markt park        # scene art ids (TIPART keys) -> PNG files
    python tools/tipp_check.py shot samstag/kueche    # or book/scene
    python tools/tipp_check.py shot --book jahr --dark
    python tools/tipp_check.py shot cover:samstag     # a cover (400x240, saved at 2x)

PNGs go to --out (default: <temp>/tipp-shots) and their paths are printed, so they can be opened
or read by an agent. Set CHROME=/path/to/browser if no browser is found.
"""
import argparse, json, os, pathlib, re, shutil, subprocess, sys, tempfile, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOOK = ROOT / "Lesehefte A2.1.html"
CLIPS = ROOT / "audio" / "tipp"
ALIGN_OK = ROOT / "tools" / "tipp-align-ok.txt"

RENDER_JS = r"""
(function(){const q=new URLSearchParams(location.hash.slice(1)),id=q.get('id'),dark=q.get('dark')==='1';
document.documentElement.setAttribute('data-theme',dark?'dark':'light');
const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join(' ');let body;
if(id.startsWith('cover:'))body=TIPCOVERS[id.slice(6)]().replace('<svg ','<svg width="800" height="480" ');
else{let art=id;if(id.includes('/')){const [b,s]=id.split('/'),sc=TIPBOOKS.find(x=>x.id===b).scenes.find(x=>x.id===s);art=sc.art||sc.id}
  body=`<svg viewBox="0 0 800 440" width="800" height="440">${TIPART[art]()}</svg>`}
document.body.innerHTML=body;document.body.style.cssText='margin:0;background:#fff;overflow:hidden';
const st=document.createElement('style');st.textContent=css+' .sheet,.pen{display:none!important}';document.head.appendChild(st);})();
"""

CHECK_JS = r"""
(function(){const R={books:[],problems:[],lines:[]};
try{
 const idField={qs:'Rätsel',groups:'Sammle alle!',tf:'Richtig oder falsch?',hoer:'Hör genau!',wohin:'Wohin damit?',luecke:'Lückentext',react:'Reaktionstest'};
 const needs={raetsel:'qs',sammeln:'groups',wahr:'tf',hoeren:'hoer',wohin:'wohin',dialog:'dlg',reaktion:'react',darf:'darf',pruefung:'pruef',luecke:'luecke',satzbau:'satz',quiz:'quiz'};
 const stray=(where,x)=>{if(x&&typeof x.de==='string'&&/^[a-z]+: /.test(x.de))R.problems.push(`${where}: unknown speaker "${x.de.split(':')[0]}" (add it to SPK or fix the prefix)`)};
 TIPBOOKS.forEach(b=>{
  const B={id:b.id,title:b.title,level:b.level,modes:b.modes,games:b.games,scenes:[]};R.books.push(B);
  b.modes.forEach(m=>{if(!MODES[m])R.problems.push(`${b.id}: unknown mode ${m}`)});
  b.games.forEach(g=>{if(!GAMES[g])R.problems.push(`${b.id}: unknown game ${g}`)});
  if(!TIPCOVERS[b.id])R.problems.push(`${b.id}: no cover in TIPCOVERS`);
  else if(/undefined|NaN/.test(TIPCOVERS[b.id]()))R.problems.push(`${b.id}: cover contains undefined/NaN`);
  b.scenes.forEach(sc=>{const art=sc.art||sc.id,where=`${b.id}/${sc.id}`;B.scenes.push({id:sc.id,art,hotspots:Object.keys(sc.hs).length});
   if(!TIPART[art]){R.problems.push(`${where}: no art TIPART.${art}`);return}
   let svg;try{svg=TIPART[art]()}catch(e){R.problems.push(`${where}: art throws ${e.message}`);return}
   const drawn=new Set([...svg.matchAll(/data-h="(\w+)"/g)].map(m=>m[1]));
   Object.keys(sc.hs).filter(k=>!drawn.has(k)).forEach(k=>R.problems.push(`${where}: hotspot "${k}" has text but is not drawn`));
   [...drawn].filter(k=>!(k in sc.hs)).forEach(k=>R.problems.push(`${where}: drawn hotspot "${k}" has no text`));
   if(/undefined|NaN/.test(svg))R.problems.push(`${where}: art contains undefined/NaN`);
   for(const f in idField)(sc[f]||[]).forEach((x,i)=>{const ids=[...(x.a||[]),...(x.item?[x.item]:[])];
     ids.filter(k=>!drawn.has(k)).forEach(k=>R.problems.push(`${where}: ${idField[f]} item ${i+1} points to "${k}", which is not drawn`))});
   b.games.forEach(g=>{const f=needs[g];if(f&&!(sc[f]||[]).length)R.problems.push(`${where}: game ${g} needs ${f} data`);
     const need=g==='merken'?12:(g==='finde'||g==='artikel')?5:0;if(nounsOf(sc).length<need)R.problems.push(`${where}: game ${g} needs ${need}+ nouns with der/die/das, has ${nounsOf(sc).length}`)});
   sc.story.forEach((x,i)=>stray(`${where} story ${i+1}`,x));
   // story and dialogue lines only: in discover/knowledge lines "kochen: ich koche …" is meant to be read out
   for(const id in sc.hs)sc.hs[id].e.forEach(ex=>ex.forEach(x=>stray(`${where} ${id}`,x)));
  });
 });
 // question/answer alignment: an answer must be findable on its own page (the scene's texts or text drawn in its picture)
 const STOP=new Set('nein danke bitte hier gern gerne vielen dank okay klar natürlich vielleicht hallo tschüss wiedersehen entschuldigung beispiel gute guten alles herzlichen eine einen einem einer mein meine unser unsere dort dann noch nicht auch schon sehr aber oder wenn weil dass diese dieser dieses alle viele jeden jede kein keine sind sein haben wird'.split(' '));
 const NUM=/^(zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn|elf|zwölf|\w+zehn|\w+zig|\w+ßig|\w*hundert\w*|\w*tausend\w*|\d[\d,.]*)$/;
 const keyWords=t=>[...new Set((t.match(/[A-Za-zÄÖÜäöüß0-9][A-Za-zÄÖÜäöüß0-9,.]*/g)||[]).map(w=>w.replace(/[.,]+$/,''))
   .filter(w=>!STOP.has(w.toLowerCase())&&(/^[A-ZÄÖÜ]/.test(w)&&w.length>=4||NUM.test(w.toLowerCase()))))];
 const has=(corp,w)=>{const l=w.toLowerCase();return corp.includes(l.slice(0,Math.max(4,l.length-2)))};
 R.align=[];
 TIPBOOKS.forEach(b=>{
  const corp={};
  b.scenes.forEach(sc=>{const t=[sc.title,...sc.story.map(x=>x.de)];
   for(const id in sc.hs){const h=sc.hs[id];t.push(h.w,...h.d.map(x=>x.de),...h.k.map(x=>x.de));h.e.forEach(ex=>ex.forEach(x=>t.push(x.de)))}
   let svg='';try{svg=TIPART[sc.art||sc.id]()}catch(e){}
   t.push(...[...svg.matchAll(/<text[^>]*>([^<]*)<\/text>/g)].map(m=>m[1]));
   corp[sc.id]=t.join(' ').toLowerCase()});
  b.scenes.forEach(sc=>{
   // facts (true statements, corrections, quiz answers, the missing word of a gap) must be on the page;
   // a dialogue reply may be free speech, but must not depend on something only another page shows.
   // Theory-exam answers are general exam knowledge and are not checked.
   const answers=[...(sc.dlg||[]).map((x,i)=>[`Im Gespräch ${i+1}`,x.opts[0].de,1]),...(sc.quiz||[]).map((x,i)=>[`Wissensquiz ${i+1}`,x.opts[0].de]),
    ...(sc.tf||[]).map((x,i)=>[`Richtig oder falsch? ${i+1}`,x.t?x.q:(x.why?x.why.de:'')]),...(sc.luecke||[]).map((x,i)=>[`Lückentext ${i+1}`,x.fill])];
   answers.forEach(([g,t,free])=>keyWords(t).forEach(w=>{if(has(corp[sc.id],w))return;
    const other=b.scenes.filter(o=>o.id!==sc.id&&has(corp[o.id],w)).map(o=>o.id);
    if(free&&!other.length)return;
    R.align.push({at:`${b.id}/${sc.id}`,word:w,msg:`${b.id}/${sc.id}: ${g}: "${w}" ${other.length?`is only on another page (${other.join(', ')})`:'is not on this page'} · answer: ${t}`})}));
  });
 });
 R.lines=tipAllLines();
}catch(e){R.problems.push('checker failed: '+e.message)}
document.title='TIPCHECK:'+encodeURIComponent(JSON.stringify(R));})();
"""


def browser():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for p in [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]:
        if os.path.exists(p):
            return p
    for n in ["google-chrome", "chromium", "chromium-browser", "chrome", "msedge"]:
        if shutil.which(n):
            return shutil.which(n)
    sys.exit("No Chrome/Edge found. Set CHROME=/path/to/browser.")


def page(tmp, js, name):
    (tmp / f"{name}.js").write_text(js, encoding="utf-8")
    html = BOOK.read_bytes() + f'\n<script src="{name}.js"></script>\n'.encode()
    (tmp / f"{name}.html").write_bytes(html)
    return (tmp / f"{name}.html").as_uri()


def run(args):
    return subprocess.run([browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=4000", *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def check_data(tmp):
    out = run(["--dump-dom", page(tmp, CHECK_JS, "check")]).stdout
    m = re.search(r"<title>TIPCHECK:([^<]*)</title>", out)
    if not m:
        sys.exit("The check page did not finish (a script error in the book?). Open the book in a browser and look at the console.")
    return json.loads(urllib.parse.unquote(m.group(1)))


def cmd_verify(a, tmp):
    r = check_data(tmp)
    probs = list(r["problems"])
    keys = {l["key"] for l in r["lines"]}
    missing = [k for k in keys if not (CLIPS / f"{k}.mp3").exists()]
    if missing:
        probs.append(f"{len(missing)} of {len(keys)} spoken lines have no clip in audio/tipp/ -> run tools/tipp_check.py lines, then tools/make_voices.py")
    crlf = BOOK.read_bytes().count(b"\r\n")
    if crlf:
        probs.append(f"Lesehefte A2.1.html has {crlf} CRLF line endings; the repo uses LF (write files in binary or with newline='\\n')")
    n = sum(len(b["scenes"]) for b in r["books"])
    print(f"{len(r['books'])} books, {n} scenes, {len(keys)} spoken lines checked.")
    print("\n".join("- " + p for p in probs) if probs else "All OK.")
    ok = set()
    if ALIGN_OK.exists():
        for line in ALIGN_OK.read_text(encoding="utf-8").splitlines():
            parts = line.split("#")[0].split()
            if len(parts) >= 2:
                ok.add((parts[0], parts[1].lower()))
    align = [x["msg"] for x in r["align"] if (x["at"], x["word"].lower()) not in ok]
    if align:
        print("\nQuestion/answer alignment: a reader must find every answer on the same page (its text or its picture).")
        print("Fix the question or answer, or show the fact on that page. If it is fine after all, add")
        print("'<book>/<scene> <word>  # reason' to tools/tipp-align-ok.txt.")
        print("\n".join("- " + p for p in align))
    return 1 if probs or align else 0


def cmd_lines(a, tmp):
    lines = check_data(tmp)["lines"]
    with open(ROOT / "tools" / "tipp-lines.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(lines, f, ensure_ascii=False, indent=1)
    print(f"{len(lines)} lines written to tools/tipp-lines.json. Next: python tools/make_voices.py")
    return 0


def cmd_list(a, tmp):
    for b in check_data(tmp)["books"]:
        print(f"{b['id']}  {b['title']}  [{b['level']}]  modes: {', '.join(b['modes'])}  games: {', '.join(b['games'])}")
        for s in b["scenes"]:
            print(f"    {b['id']}/{s['id']:<14} art: {s['art']:<14} {s['hotspots']} hotspots")
    return 0


def cmd_shot(a, tmp):
    ids = list(a.ids)
    if a.book:
        b = next((b for b in check_data(tmp)["books"] if b["id"] == a.book), None)
        if not b:
            sys.exit(f"No book {a.book}. Try: python tools/tipp_check.py list")
        ids += [f"{a.book}/{s['id']}" for s in b["scenes"]] + [f"cover:{a.book}"]
    if not ids:
        sys.exit("Name scene art ids, book/scene, cover:<book>, or use --book.")
    out = pathlib.Path(a.out or pathlib.Path(tempfile.gettempdir()) / "tipp-shots")
    out.mkdir(parents=True, exist_ok=True)
    url = page(tmp, RENDER_JS, "render")
    for i in ids:
        size = "800,480" if i.startswith("cover:") else "800,440"
        f = out / (re.sub(r"[/:]", "_", i) + ("-dark" if a.dark else "") + ".png")
        run([f"--window-size={size}", f"--screenshot={f}", f"{url}#id={urllib.parse.quote(i)}&dark={'1' if a.dark else '0'}"])
        print(f if f.exists() else f"FAILED {i}")
    return 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify")
    sub.add_parser("list")
    sub.add_parser("lines")
    s = sub.add_parser("shot")
    s.add_argument("ids", nargs="*")
    s.add_argument("--book")
    s.add_argument("--dark", action="store_true")
    s.add_argument("--out")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as t:
        sys.exit({"verify": cmd_verify, "list": cmd_list, "lines": cmd_lines, "shot": cmd_shot}[a.cmd](a, pathlib.Path(t)))


if __name__ == "__main__":
    main()
