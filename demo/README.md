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

## Part 2: Demo page (`demo/index.html`)

Built by Shums, then extended with live data and the comparison column. One self-contained file:
plain HTML, CSS and JavaScript, no frameworks, no build step.

Shows the week as a bank ledger. Each row carries the transaction, what Senior Scam Shield decided,
what a single-transaction rule would have done, why, and the three messages the bank sent.

### Open it
Serve it over http. A page opened straight from the file system is blocked by the browser from
reading `decisions.json`.

```bash
python3 -m engine.replay          # from the repo root: writes demo/decisions.json
cd demo && python3 -m http.server 8080
# open http://localhost:8080
```

### Where its data comes from
Three sources, in order, shown in the top right:
1. `POST http://148.100.77.223:8000/demo/replay`, the live API on LinuxONE. Gives up after 2.5 seconds.
2. `decisions.json` next to the page, written by `python3 -m engine.replay`.
3. `sample_decisions.json`, the hand-written examples.

So it cannot go blank during a recording. If the server is unreachable it falls back and says so.

### Controls
- **Play the week**: rows appear a day at a time, to narrate over.
- **Customer dropdown**: one person's week on its own.
- **Action chips** (allowed / warn / pause / hold / escalate): click to hide or show that action.
  Turning off "allowed" leaves only the transactions the bank acted on.

### What to show on camera
- **Pick "Betty Ruiz"**: three cash withdrawals, every one allowed by the rule in use today, caught by
  the chain on the second. The clearest moment in the demo.
- **The two verdict columns.** The right one stays flat while the left climbs. That contrast is the
  whole argument; let it sit on screen.
- **Margaret's Friday row**: escalate, with the note to her daughter visible. Ethics and AI for Good
  in one frame.
- Check the top right says "live from LinuxONE" before recording.

### Checklist
- [x] Every row with both verdicts, reasons, and the three messages
- [x] Customer filter and action filters
- [x] Falls back to a file if the API is unreachable
- [x] Works at phone width
- [ ] Re-run `python3 -m engine.replay` after any scenario change, so `decisions.json` matches
