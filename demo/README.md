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

## Part 2: Demo page (Shums, after the scenario files)

**Goal:** one web page that shows the week of events and what the bank decided for each one, with colored badges. This is what the video records.

### Keep it simple (on purpose)
- **One `index.html` file** with plain HTML, CSS and a little JavaScript. No React, no npm, no build tools.
- **It runs on a laptop.** It does NOT need to run on LinuxONE (only the backend does). It calls the API on LinuxONE.
- **Don't use Streamlit.** It's hard to install on the LinuxONE server.

### Stage 1: show the sample file
Load `sample_decisions.json` (already in this folder) and show it as a table:

| Day | Customer | What happened | Action badge | Why (reasons) |
|---|---|---|---|---|

Badge colors (from CONTRACT.md): allow = green, warn = yellow, pause = orange, hold = red, escalate = dark red or purple.

Nice extras if there's time:
- Click a row to see the customer / staff / family messages
- A filter by customer
- A summary bar: "3 of 3 scams stopped, 0 innocent customers held"

Some browsers block loading a local JSON file from a double-clicked HTML file. Fixes:
1. Run `python -m http.server 8080` inside `demo/` and open `http://localhost:8080`, or
2. Paste the JSON into the HTML as `const decisions = [...]` for now.

### Stage 2 (pair with Nikhil): use the real backend
```javascript
const res = await fetch("http://148.100.77.223:8000/demo/replay", { method: "POST" });
const decisions = await res.json();
```
Same data shape as `sample_decisions.json`, so nothing else on the page changes.

**If the live connection breaks late at night, that's OK.** The engine writes its real results to `demo/decisions.json`, and the page shows that file instead.

### Checklist
- [ ] Page shows every row of `sample_decisions.json`
- [ ] Colored badges match the action
- [ ] Reasons visible for each row
- [ ] Messages (customer / staff / family) visible somehow
- [ ] Works with the real API on LinuxONE (with Nikhil)
- [ ] Ready for Kamali to record by 9 PM

### Prompt to start a Claude session
> I'm building the demo page for Senior Scam Shield (IBM Z Datathon). Read `CLAUDE.md`, `docs/CONTRACT.md` and `demo/README.md` (Part 2), then look at `demo/sample_decisions.json`. Help me build `demo/index.html` as a single file with plain HTML, CSS and JavaScript that shows the decisions as a table with colored action badges. Explain each part as we go.
