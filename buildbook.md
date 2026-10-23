# How to build a Tipp-Buch

A Tipp-Buch is a tap-and-listen picture book in `Lesehefte A2.1.html`: five big pictures (scenes), each with
about 15–22 tappable things (hotspots), three reading modes, three games and recorded voices. This guide is
the source of truth for planning, drawing and shipping one. The agents in `.claude/agents/` follow it.

| Step | What comes out | Agent |
|---|---|---|
| 1. Find a topic | a ranked shortlist with scene ideas | `topic-scout` |
| 2. Plan theme and games | `plans/<book-id>.md`: scenes, hotspots, modes, games, game data | `book-planner` |
| 3. Write the content | a `TIPBOOKS.push({…})` block in the book file | `book-planner` |
| 4. Draw the pictures | `TIPART.<scene>` functions and `TIPCOVERS.<book>` | `illustration-builder` |
| 5. Record the voices | MP3s in `audio/tipp/` | you (`tools/make_voices.py`) |
| 6. Check and ship | `python tools/tipp_check.py verify` passes, then commit | any |

## The books today

| # | id | Title | Level | Modes | Games |
|---|---|---|---|---|---|
| 1 | `samstag` | Ein Samstag in der Stadt (story) | A2 | entdecken, erzaehlen, wissen | finde, artikel, raetsel |
| 2 | `jahr` | Das Jahr in Deutschland (Sachbuch) | A2 | entdecken, sagen, wissen | sammeln, wahr, hoeren |
| 3 | `wohnen` | Wohnen in Deutschland | A2 | entdecken, wo, wissen | wohin, dialog, merken |
| 4 | `verkehr` | Unterwegs im Verkehr | A2.2 | entdecken, regeln, wissen | reaktion, darf, pruefung |
| 5 | `ausfluege` | Ausflüge in Deutschland | B1 | entdecken, erklaeren, wissen | luecke, satzbau, quiz |
| 6 | `geburtstag` | Omas Geburtstag (Familie Bär, Folge 1) | A2 | entdecken, erzaehlen, wissen | finde, dialog, wahr |

Run `python tools/tipp_check.py list` for the live list with every scene.

## 1. Choosing a topic that works

A good Tipp-Buch topic is something learners in Germany meet in everyday life *and* can be drawn as busy,
recognisable places. Score each candidate from 0 to 2 on every line; build only topics with 10 or more points.

| Criterion | 2 points when … |
|---|---|
| Drawable | it splits into 5 different places, each with 15+ concrete, tappable things |
| Useful | learners need the words this year (exam topics, Integrationskurs, daily life) |
| Grammar hook | one clear grammar focus per scene (Wo/Wohin, modal verbs, Perfekt, Relativsätze …) |
| Culture | at least 3 "So ist das in Deutschland" facts per scene |
| Story spine | there is a reason to turn the page (a day, a trip, a problem that gets solved) |
| Game fit | at least two game types fit naturally (see section 2) |
| New | little overlap with the books above |

Rules:

- **Only original characters, stories and art.** Do not adapt TV episodes, films, comics or other people's
  characters (for example Peppa Pig, Paw Patrol or Bluey), not even "in their style" with the same family or
  names. The *format* is free to use: short everyday episodes with one family and one small problem.
- One level per book (A2, A2.2, B1, B2), shown as the badge on the cover.
- German first, English second, written `"deutsch|english"`.

Ideas not built yet: Beim Arzt und in der Apotheke · Auf dem Amt (Bürgeramt, Ausländerbehörde) ·
Arbeit und Bewerbung · Im Supermarkt · Kita und Schule · Im Restaurant · Feste in der Familie ·
Sport und Verein · Natur und Umwelt (Wald, Mülltrennung draußen) · more episodes of Familie Bär (see
`plans/familie-baer.md`).

## 2. Planning modes and games

Every book has three **modes** (the first is always `entdecken`) and three **games**. `storyMode` is the mode
that also reads the scene's `story` lines when it is chosen.

### Modes: what the fourth hotspot field means

| Mode | Fourth hotspot field | Good for |
|---|---|---|
| `erzaehlen` | the story: dialogue lines `speaker: deutsch\|english` joined by ` // ` | a book with characters |
| `sagen` | what people say about the thing in daily life | Sachbuch, phrases |
| `wo` | where it is: stehen/liegen/hängen + Dativ | rooms, places |
| `regeln` | the rule: darf/muss/soll | traffic, offices, school |
| `erklaeren` | an explanation, usually a relative clause | B1 and up |
| `wissen` | always the fifth field: grammar, facts, culture | every book |

### Games: the data each scene needs

| Game | What it trains | Scene data |
|---|---|---|
| `finde` Finde es! | listening for nouns | nothing extra (5+ hotspots with der/die/das) |
| `artikel` Der, die, das | articles | nothing extra (5+ nouns) |
| `merken` Merkspiel | memory, word order | nothing extra (12+ nouns) |
| `raetsel` Rätsel | reading riddles | `qs: [['frage\|question','ids that count'], …]` |
| `sammeln` Sammle alle! | word groups | `groups: [['task\|…','id id id'], …]` |
| `wahr` Richtig oder falsch? | facts, negation | `tf: [['statement\|…', 1 or 0, 'ids', 'correction\|…'], …]` |
| `hoeren` Hör genau! | listening without text | `hoer: [['description\|…','ids'], …]` |
| `wohin` Wohin damit? | Wohin + Akkusativ | `wohin: [['thing or ""','places','question\|…','answer\|…'], …]` |
| `dialog` Im Gespräch | choosing replies | `dlg: [['prompt\|…', ['right\|…','wrong\|…','wrong\|…']], …]` |
| `reaktion` Reaktionstest | fast recognition | `react: [['situation\|…','ids'], …]` |
| `darf` Darf man das? | modal verbs | `darf: [['action\|…','darf' / 'nicht' / 'muss','explanation\|…'], …]` |
| `pruefung` Theorieprüfung | several right answers | `pruef: [['question\|…', [answers], 'indices of right ones', 'explanation\|…'], …]` |
| `luecke` Lückentext | words in context | `luecke: [['sentence with ___\|…','missing word','ids'], …]` |
| `satzbau` Satzbau | word order, verb position | `satz: ['chunk / chunk / chunk\|English', …]` |
| `quiz` Wissensquiz | culture and facts | `quiz: [['question\|…', ['right\|…','wrong\|…','wrong\|…'], 'explanation\|…'], …]` |

Write at least 6 items per game per scene (games play 4–5 rounds, picked at random).

**Good combinations:** one *find* game (finde, hoeren, reaktion, merken), one *sentence* game (luecke, satzbau,
dialog, wohin) and one *knowledge* game (raetsel, wahr, quiz, darf, pruefung). For A2, keep the sentences short
and use present tense and Perfekt. For B1, use Nebensätze and relative clauses.

A new game type needs code: an entry in `GAMES` (name, icon, intro, `items(sc)`), its parser line in the
"voices, parsing" block, and its answer handling. Plan new games only when no existing one fits.

### Questions and answers must match the page

A game runs on one page, so the reader must be able to find every answer **on that same page**, either in
its picture or in its texts. A question whose answer is only shown on another page feels like a trick. For
example, "Was schenken wir Oma?" on page 1 must not expect "eine Tasse" when the cup first appears on page 2.

- **Facts:** true statements, corrections, quiz answers and the missing word of a gap must be visible or
  written on the page. Numbers, times and prices need to be in the picture too ("200 g", "14 €", a clock).
- **Dialogue replies (Im Gespräch)** may be free, polite speech, but must not depend on something only
  another page shows. The two wrong replies must clearly not fit the question (not just a different fact).
- **Riddles and Hör genau!** point to hotspots that are drawn on the page (`verify` checks the ids).
- **Avoid duplicates:** don't ask the same thing in two games of the same scene.
- **Theory-exam answers** (`pruef`) may be general exam knowledge.

`python tools/tipp_check.py verify` checks this automatically. It collects the words of each page (its
texts plus the text drawn in its picture) and reports answer nouns and numbers that the page doesn't have,
marking those that only appear on another page. Fix the question or answer, or add the fact to the
picture. A warning that is fine after review goes into `tools/tipp-align-ok.txt` with a reason, for
example `jahr/kalender Sommermonat  # the year wheel shows Juli inside the Sommer ring`.

### Content format

Each hotspot is written as `id:['der Tisch|the table', 'die Tische', discover, fourth, knowledge]`:

- **Ids** are lowercase ASCII with no umlauts (`kuehlschrank`). `_bg` is the background.
- **Plural** is `''` when there is none.
- **Speakers** must exist in `SPK`, and each new speaker also needs a voice in `tools/make_voices.py`.
- **Story lines** are plain narrator text, or `speaker: text|english`.

## 3. Illustration: where the best work must go

All Tipp-Bücher use the **realistic kit**: thin warm outlines (`RL`), gradients, soft shadows, one-point
perspective rooms, and people drawn with `human()`. Never use the old cartoon helpers (`person`, `box` with
`I`). Those belong to the ten reading books (Lesehefte).

### Spend the effort where the reader taps and looks

1. **The things the text talks about.** If the text says "Die Uhr zeigt halb zehn" or "2 € / kg", the
   picture must show exactly that. Read every hotspot's text before drawing it.
2. **People.** They are the biggest hotspots and carry the story. Give each one a pose that matches the text
   (holding the list, waving, sitting, paying) using `human()` options. A story's characters are defined once
   (see `WHO` for Book 1) so they look the same on every page.
3. **Foreground objects.** They are big, so draw them with gradients, a highlight and a shadow.
4. **The background** sets mood and place. Keep it calmer and paler (haze, lighter colours) so the hotspots
   stand out.

### Canvas and layout

- Each scene is **800 × 440**. On wide screens it fills a two-page spread; on phones each half (x 0–400 and
  400–800) is a page of its own. **Keep important hotspots away from x = 400**, and make sure each half is
  interesting on its own.
- Hotspots should be at least about 30 × 30 px so a finger can hit them. Split tiny things into a group (a
  bowl of eggs, a row of tulips).
- **Draw order is tap order.** Later groups sit on top, so draw back to front. Pieces that sit on a person
  (clothes, a held list) are separate hotspots drawn *after* the person.
- Decorative overlays that must not catch taps go outside any `hs()` group with `pointer-events="none"`.

### Helpers you can use

| Kit | Helpers |
|---|---|
| Book 3 (rooms) | `P R L` shapes, `lg rgr` gradients, `shade`, `box3`, `shell` (room), `quadL quadR` (side walls), `glow`, `win3` (window), `treeR`, `cloudR`, `human` |
| Book 4 (outdoors) | `sky4`, `haze`, `mtn`, `fir`, `forest`, `cloud4`, `grassTex`, `flowers4`, `cow4`, `fachwerk` |
| Book 5 (traffic) | `rsign` (German road signs), `ampel5`, `pedAmpel`, `carRear carFront carSide`, `cyclistBack`, `backOf` |
| Book 6 (animal cast) | `critter(kind, x, y, h, options)` (kind `baer` (teddy bear, own `fur` colour), `reh` or `igel`; all `human()` options, plus `bow`, `flower`, `pearls`, `strawHat`, `glasses`), `baer(id, …)` and `BAER` (the cast), `roseCup`, `bouquetR`, `presentR`, `balloon6`, `roseBush`, `blossomTree`, `lampionR`, `gardenChair`, `numberCandles`, `chairBackR`, `paperChain` |
| Books 1–2 | `who` and `WHO`, `clockR` (also a railway clock), `leafR`, `catR`, `dogR`, `duckR`, `pigeonR`, `hareR`, `squirrelR`, `hedgehogR`, `bikeR`, `busR`, `townhouse`, `cobbles`, `stallR`, `crateR`, fruit and veg (`appleR`, `tomatoR`, …), `sunflowerR`, `wildflower`, `farTree`, `rainCloud`, `flakeR`, `burstR`, `snowmanR`, `ringR`, `magicPen` |

`human(x, y, height, options)` draws a person with the feet at (x, y). Its options:

- **Looks:** `skin`, `hair`, `hairStyle` (`short`, `long`, `bob`, `pony`, `bun`, `bald`), `top`, `bottom`,
  `shoes`, `skirt`, `sleeves:'long'`, `glasses`, `beard`, `cap`, `hat`, `chef`, `apron`, `clip`
- **Poses:** `sit:'chair'` or `sit:'ground'`, `hands:[[lx,ly],[rx,ry]]` (body units; `null` keeps that arm
  hanging), `wave`, `reach:<degrees>`
- **Body:** `kid` (larger head)
- **Things and extras:** `box`, `broom`, `pack`, `camera`, `umbrellaUp`, `add` and `addBack` (your own
  SVG in body units)

### Colours and dark mode

- **Use tokens only:** `--rl-*` (objects, rooms), `--ls-*` (landscapes, sky), `--tb-*` (extras), so dark mode
  works. Dark mode turns rooms into a lamp-lit evening and outdoor scenes into dusk. A scene that is always
  at night (like the Christmas market) may use fixed night colours.
- **Gradient ids** carry a per-scene prefix (`mk…`, `bh…`) so they never clash.
- **New tokens** go in all three blocks: `:root`, the `prefers-color-scheme: dark` block and
  `:root[data-theme="dark"]`.

### Covers

A cover is 400 × 240 with `preserveAspectRatio="xMidYMid slice"`, and the edges get cropped on the shelf. Show
the book's world and its main characters, keep text short, and use unique gradient ids (`cs6…`).

### Drawing loop

Draw, then shoot, look, fix, and shoot again:

```
python tools/tipp_check.py shot <book>/<scene>          # light
python tools/tipp_check.py shot <book>/<scene> --dark   # dark
python tools/tipp_check.py shot --book <book>           # every scene plus the cover
```

Before calling a scene done, check all of these:

- Every hotspot from the text is drawn and recognisable.
- Facts match the text (times, prices, colours, counts).
- Nothing important sits on x = 400.
- People have poses that match the text.
- Light and dark mode both look right.
- `verify` passes.

## 4. Voices

1. Run `python tools/tipp_check.py lines`. It writes every spoken line to `tools/tipp-lines.json`.
2. Run `python tools/make_voices.py`, which needs `pip install edge-tts`. Use `--prune` to delete clips that
   are no longer used.
3. `verify` reports how many lines still have no clip.

## 5. Check and ship

- `python tools/tipp_check.py verify` must print **All OK**. It checks:
  - every hotspot is both written and drawn
  - every game target exists
  - every answer can be found on its own page (see "Questions and answers must match the page")
  - the games have their data
  - story speakers exist
  - voice clips exist
  - no `undefined` or `NaN` appears in the art
  - the book file has no CRLF line endings
- **Keep LF line endings.** When editing the book with a script, write with `newline='\n'` or in binary mode.
- New Tipp-Bücher get a level badge (`level:'A2'` …) and a `cert` sentence for the album page.
- Commit messages follow the history: `Add Tipp-Buch N "<Titel>" (<Level>) …`.
