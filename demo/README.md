# demo/ : Pitch video + demo page

Two jobs live in this folder:

| Part | Owner | When |
|---|---|---|
| **Pitch video** (script, slides, recording, editing) | Kamali | Starts now |
| **Demo page** (`index.html`, what the video records) | Shums | Starts after the scenario files are done (~4 PM) |

---

## Part 1: Pitch video (Kamali)

### What the judges asked for (from the LinuxONE prep session)
- **Strictly within the published time limit.** Check the exact limit and file format on the event portal first.
- Clearly state the **problem, target persona and value**.
- Show a **live demo recorded on LinuxONE**.
- Clearly present **each team member's role** and contributions.
- Community value: name the people helped, tie it to our challenge (Real-Time AI for Critical Decisions), frame it as AI for Good, show transparent decision reasoning.

### Suggested script outline
Adjust the timing to the real limit. Rough share of the video:

| Section | Share | Content |
|---|---|---|
| 1. The problem | 10% | Seniors lose billions to scams where they move their own money. Each step looks normal, so fraud checks approve every one |
| 2. The Frisco story | 10% | The local gold bar case: savings sold, cash withdrawn, gold handed to a courier |
| 3. What exists and the gap | 10% | Phone filters, family apps, bank fraud tools: they check single moments. Nobody watches the whole chain, including the workaround after a block |
| 4. Our solution | 15% | Triggers linked over 7 days. Warn, pause, hold + family alert, escalate. Opt-in and privacy |
| 5. **Live demo** | 30% | The mixed week on the demo page running against LinuxONE (see below) |
| 6. Results | 10% | Scams stopped, days earlier than a single-transaction rule, innocent customers held: 0 |
| 7. Built on IBM Z | 5% | `s390x`, Telum `nnpa` flag, Docker on LinuxONE |
| 8. Future + team | 10% | Neural sequence model on Telum, Granite explanations, consumer protection agencies. Who did what |

### Demo moments to show (from `docs/SCENARIOS.md`)
1. Mon: Margaret moves $150,000 to checking, gets a **warning**
2. Tue: her wire to a gold dealer is **paused**
3. Thu: she tries again, **hold** + her daughter gets a "please check in" message
4. Fri: she goes to a different branch for cash, **escalate** (the scammer working around the block)
5. Meanwhile, the home buyer's $118,500 title wire goes through untouched
6. Quick flash of the grandparent and phantom hacker scams also being stopped

You can plan all of this now using `sample_decisions.json`. The real page will show the same data shape.

### Checklist
- [ ] Time limit + format confirmed on the portal
- [ ] Script written
- [ ] Slides (reuse the mentor summary and competitor comparison)
- [ ] Evidence clips recorded now: `uname -m` and `lscpu | grep -i nnpa` on the server
- [ ] Demo segment recorded (tonight, once the page runs against LinuxONE)
- [ ] Results numbers filled in from the engine replay
- [ ] Final video under the limit, exported, uploaded

### Prompt to start a Claude session
> I'm making the pitch video for Senior Scam Shield (IBM Z Datathon). Read `CLAUDE.md`, `README.md`, `docs/SCENARIOS.md` and `demo/README.md`. Help me write a video script that fits a {N}-minute limit, following the outline in `demo/README.md`, with what to say and what to show on screen for each section.

---

## Part 2: Demo page (built, `demo/index.html`)

The page is written. It is one self-contained file: plain HTML, CSS and JavaScript, no frameworks,
no build step. Open it and it shows the week as a bank ledger, with two verdict columns side by side:
what Senior Scam Shield decided, and what a single-transaction rule would have done.

### Open it
The page needs to be served over http, because browsers block a file opened directly from disk
from reading `decisions.json`.

```bash
# from the repo root, with the latest scenario files
python3 -m engine.replay          # writes demo/decisions.json
cd demo && python3 -m http.server 8080
# then open http://localhost:8080
```

### Where its data comes from
It tries three sources in order and shows which one it used in the top right:
1. `POST http://148.100.77.223:8000/demo/replay`, the live API on LinuxONE. Gives up after 2.5 seconds.
2. `decisions.json` next to the page, written by `python3 -m engine.replay`.
3. `sample_decisions.json`, the hand-written examples.

So the demo cannot end up blank during a recording. If the server is unreachable it quietly falls
back to the file and says so.

**`decisions.json` currently holds placeholder output** built from `docs/SCENARIOS.md` so the page
is never empty. Once the real `data/scenarios/*.json` are on main, run `python3 -m engine.replay`
again and it is overwritten with the real thing.

### What to show on camera
- **Press "Play the week"**: rows appear a day at a time, which gives you something to narrate over.
- **Pick "Betty Ruiz" from the dropdown**: three cash withdrawals, every one of them allowed by the
  rule in use today, and the chain catches her on the second. This is the clearest moment in the demo.
- **Select any row with a verdict**: it opens to show the reasons, the message to the customer, the
  script for the teller, and the note to her trusted contact.
- The right-hand column staying flat while the left climbs is the argument. Let it sit on screen.

### If you want to change it
It is one file, about 400 lines, with the CSS at the top and the JavaScript at the bottom.
Colours are variables in `:root`. Ask Rinin or Nikhil before changing the data shape, since it
follows `docs/CONTRACT.md`.

### Checklist
- [x] Page shows every row with colored verdicts
- [x] Reasons and the customer / teller / family messages on a row
- [x] Falls back to a file if the API is unreachable
- [x] Works at phone width
- [ ] Pointed at the live API on the night (open it and check the top right says "live from LinuxONE")
- [ ] Re-run `python3 -m engine.replay` once Shums's scenarios are on main
