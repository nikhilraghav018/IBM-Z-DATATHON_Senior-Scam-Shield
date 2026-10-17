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
- [ ] `requirements.txt` (fastapi, uvicorn)
- [ ] `api/main.py` with `/health` running on LinuxONE (screenshot it)
- [ ] `Dockerfile` at repo root, builds and runs on LinuxONE
- [ ] CORS on, port 8000 open, demo page can reach `/health`
- [ ] `/events` and `/demo/replay` calling the real engine
- [ ] Screenshot: `docker ps` + `/health` showing `s390x` (judging evidence)

## Server facts
- Login: `ssh -i <key> linux1@148.100.77.223` (key is shared privately, **never commit it**)
- 7.8 GB RAM, no swap, 36 GB free disk, Python 3.12, Docker 29
- Jupyter already runs in a container on port 38888 (don't stop it)

## Prompt to start a Claude session
> I'm working on the API and LinuxONE deployment for Senior Scam Shield (IBM Z Datathon). Read `CLAUDE.md`, `docs/CONTRACT.md` and `api/README.md`. Help me write `api/main.py` with FastAPI and a Dockerfile that runs on an IBM LinuxONE s390x Ubuntu server. Start with `/health` and a hard-coded `/demo/replay`.
