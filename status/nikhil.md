# Nikhil: status log

**Role:** API + LinuxONE (`api/`)

Add a new entry at the TOP each time you finish something, then commit and push.
Keep it short. "Blocked on" is the important line: if you're stuck, say so here.

<!-- Copy this block for each new entry:
## <time>: Done: <what you finished>
Next: <what you're starting>
Blocked on: <nothing, or what you need and from whom>
-->

## 3:25 PM: Done: LinuxONE serves the real scenarios
Redeployed with Shums's 8 scenario files. `POST http://148.100.77.223:8000/demo/replay` returns 18 live decisions from the real engine: gold bar warn, pause, hold, escalate; grandparent reaches hold; phantom hacker pause, hold, escalate; all 5 innocents only allow/warn. Same result locally and on the server, identical on every replay. 40 tests pass, `data/validate.py` passes.
Next: on call for redeploys if engine or data changes before judging
Blocked on: nothing

## 2:10 PM: Done: API deployed on LinuxONE
Running in Docker on the LinuxONE server as `scam-shield-api`, port 8000 open. http://148.100.77.223:8000/health gives `"arch": "s390x", "engine": "real"` from a laptop browser. Screenshots of `docker ps` + `/health` taken. Redeploy steps are in `api/README.md`.
Next: redeploy once Shums's scenario files are on main, then check `/demo/replay` shows the real stories
Blocked on: nothing. Shums: demo page can call `POST http://148.100.77.223:8000/demo/replay` now; it returns the sample decisions until `data/scenarios/*.json` land.

## 1:40 PM: Done: API works with Rinin's real engine
Fixed the `test_health` failure Rinin reported (stub test now forces stub mode). Added an end-to-end test: gold bar through the API with the real engine gives warn, pause, hold, escalate, and the same answer on every replay. A scenario file with broken JSON is now skipped instead of crashing `/demo/replay`. 40 tests pass (api + engine).
Next: build and run the Docker image on LinuxONE, screenshot `/health` showing s390x
Blocked on: nothing. Shums: until real files land in `data/scenarios/`, `/demo/replay` returns the sample decisions.

## 12:30 PM: Starting
Next: FastAPI `/health` running in Docker on LinuxONE, then `/demo/replay` with a hard-coded response
Blocked on: nothing
