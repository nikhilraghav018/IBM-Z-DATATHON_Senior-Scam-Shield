# demo/ : Demo screen

**Owner:** demo lead (5/10)
**Goal:** one web page that shows the week of events and what the bank decided for each one, with colored badges. This is what the judges watch.

## Keep it simple (on purpose)
- **One `index.html` file** with plain HTML, CSS and a little JavaScript. No React, no npm, no build tools.
- **It runs on your laptop.** Just double-click `index.html` or open it in Chrome. It does NOT need to run on LinuxONE (only the backend does).
- **Don't use Streamlit.** It's hard to install on the LinuxONE server.

## Build it in two stages

### Stage 1 (now to ~7 PM): show the sample file
Load `sample_decisions.json` (already in this folder) and show it as a table:

| Day | Customer | What happened | Action badge | Why (reasons) |
|---|---|---|---|---|

Badge colors (from CONTRACT.md): allow = green, warn = yellow, pause = orange, hold = red, escalate = dark red or purple.

Nice extras if you have time:
- Click a row to see the customer / staff / family messages
- A filter dropdown by customer
- A summary bar at the top: "3 of 3 scams stopped, 0 innocent customers held"

Note: some browsers block loading a local JSON file from a double-clicked HTML file. Two easy fixes:
1. Run `python -m http.server 8080` inside the `demo/` folder and open `http://localhost:8080`, or
2. Paste the JSON straight into the HTML as `const decisions = [...]` for now.

### Stage 2 (after ~7 PM, pair with the API lead): use the real backend
Swap the file for a call to the API:
```javascript
const res = await fetch("http://148.100.77.223:8000/demo/replay", { method: "POST" });
const decisions = await res.json();
```
The data shape is exactly the same as `sample_decisions.json`, so nothing else on the page changes.

**If the live connection breaks late at night, that's OK.** The engine can write its real results to `demo/decisions.json`, and the page shows that file instead. That is a fine demo.

## Checklist
- [ ] Page shows every row of `sample_decisions.json`
- [ ] Colored badges match the action
- [ ] Reasons are visible for each row
- [ ] Messages (customer / staff / family) visible somehow
- [ ] Works with the real API (with the API lead)
- [ ] Screen recording of the demo for the pitch video

## Prompt to start a Claude session
> I'm building the demo page for Senior Scam Shield (IBM Z Datathon). I'm a beginner. Read `CLAUDE.md`, `docs/CONTRACT.md` and `demo/README.md`, then look at `demo/sample_decisions.json`. Help me build `demo/index.html` as a single file with plain HTML, CSS and JavaScript that shows the decisions as a table with colored action badges. Explain each part simply.
