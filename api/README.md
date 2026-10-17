# api/ : FastAPI service + LinuxONE deployment

**Owner:** Nikhil
**Goal:** wrap the engine in a small web API, run it in Docker on the team's LinuxONE server, and help connect the demo page to it.

## Endpoints to build
| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/health` | none | `{"status": "ok", "arch": "s390x"}` (use `platform.machine()`; nice screenshot for judges) |
| POST | `/customers` | `{"customer": Customer, "history": [Event]}` | `{"registered": "C1"}` |
| POST | `/events` | `Event` | `Decision` |
| GET | `/customers/{id}/timeline` | none | list of Decisions for that customer |
| POST | `/demo/replay` | none | Loads every file in `data/scenarios/`, runs them all, returns a list of `{customer, event, decision}` replay items sorted by time (CONTRACT.md section 5). **The demo page mainly uses this one.** |
| POST | `/reset` | none | Clears memory so the replay can run again |

Shapes are in [`docs/CONTRACT.md`](../docs/CONTRACT.md). The engine interface is in [`engine/README.md`](../engine/README.md):
```python
eng.register(customer, history)
decision = eng.process(event)
```
Until the engine is ready, return a hard-coded Decision from `demo/sample_decisions.json` so the demo can connect early.

## Must-dos people forget
1. **CORS.** The demo page runs on a laptop and calls this server. Without CORS the browser blocks it:
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
   ```
2. **Open the port on the server** (same idea as Jupyter's 38888). Pick 8000:
   ```bash
   sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
   ```
3. **Bind to all interfaces** inside Docker: `uvicorn api.main:app --host 0.0.0.0 --port 8000`
4. **s390x check:** build the Docker image on the LinuxONE server early (before 4 PM). `python:3.12-slim` supports s390x. Test that `pip install fastapi uvicorn` works there before writing lots of code.
5. **Docker needs sudo** on our server unless someone ran `sudo usermod -aG docker linux1` and logged back in.

## Checklist
- [x] `api/requirements.txt` (fastapi, uvicorn)
- [x] `api/main.py`: every endpoint above, CORS on, stub mode until the engine lands (tested locally)
- [ ] `/health` running on LinuxONE (screenshot it)
- [x] `Dockerfile` at repo root (written; not yet built on LinuxONE)
- [ ] Docker image builds and runs on LinuxONE
- [ ] CORS on, port 8000 open, demo page can reach `/health`
- [ ] `/events` and `/demo/replay` calling the real engine
- [ ] Screenshot: `docker ps` + `/health` showing `s390x` (judging evidence)

## Stub mode vs real engine
`api/main.py` tries `from engine.engine import Engine` at startup.
- **Engine missing:** "stub" mode. `/demo/replay` returns `demo/sample_decisions.json`, `/events` returns the sample decision with the same `event_id` (or a plain `allow`).
- **Engine present:** `/demo/replay` resets memory, registers every `data/scenarios/*.json` (files starting with `_` are skipped) and replays all `live` events in time order.

`/health` and the `X-Engine` response header say which mode is on. The API strips `truth` from every event before the engine sees it, but the replay items keep it for the demo page.

## Run locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r api/requirements-dev.txt
python -m pytest api -q
uvicorn api.main:app --reload --port 8000      # http://127.0.0.1:8000/docs
```

## Deploy on LinuxONE
```bash
ssh -i <key> linux1@148.100.77.223
git clone https://github.com/nikhilraghav018/IBM-Z-DATATHON_Senior-Scam-Shield.git && cd IBM-Z-DATATHON_Senior-Scam-Shield
sudo docker build -t scam-shield-api .
sudo docker run -d --name scam-shield-api --restart unless-stopped -p 8000:8000 scam-shield-api
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
curl localhost:8000/health                     # expect "arch": "s390x"
```
To pick up new engine or scenario commits: `git pull && sudo docker rm -f scam-shield-api`, then the build and run lines again.

## Server facts
- Login: `ssh -i <key> linux1@148.100.77.223` (key is shared privately, **never commit it**)
- 7.8 GB RAM, no swap, 36 GB free disk, Python 3.12, Docker 29
- Jupyter already runs in a container on port 38888 (don't stop it)

## Prompt to start a Claude session
> I'm working on the API and LinuxONE deployment for Senior Scam Shield (IBM Z Datathon). Read `CLAUDE.md`, `docs/CONTRACT.md` and `api/README.md`. Help me write `api/main.py` with FastAPI and a Dockerfile that runs on an IBM LinuxONE s390x Ubuntu server. Start with `/health` and a hard-coded `/demo/replay`.
