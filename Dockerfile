# Senior Scam Shield API. Builds on IBM LinuxONE (s390x) and on laptops (amd64/arm64).
FROM python:3.12-slim

WORKDIR /app
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# The API plus what it reads at runtime: the engine, the scenarios and the sample decisions.
COPY api/ api/
COPY engine/ engine/
COPY data/ data/
COPY demo/sample_decisions.json demo/sample_decisions.json

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
