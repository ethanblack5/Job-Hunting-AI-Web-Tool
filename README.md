# Job-Hunting AI Web Tool

This project contains a React frontend and a FastAPI backend for searching
RemoteOK job listings.

## Prerequisites

- Python 3.10 or newer
- Node.js and npm

## Run the backend locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install "fastapi[standard]" requests beautifulsoup4 ftfy
```

The backend currently uses imports relative to its `python` directory. Start
it with:

```bash
cd python
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

The API documentation is available at:

<http://127.0.0.1:8000/docs>

## Run the frontend locally

In a second terminal:

```bash
cd website
npm install
npm start
```

Open <http://localhost:3000>. The development proxy forwards `/api` requests
to the backend at `http://127.0.0.1:8000`.

## Run semantic matching

Activate the virtual environment and install the semantic-ranking
dependencies:

```bash
source .venv/bin/activate
python -m pip install sentence-transformers scikit-learn requests
cd semantic_matching
```

Fetch and normalize sample jobs:

```bash
python remoteok_client.py --limit 25
python preprocess_jobs.py
```

Run a semantic-ranking query:

```bash
python semantic_baseline.py \
  "Python machine learning engineer with cloud experience"
```

The first run may take longer because the sentence-transformer model must be
downloaded.

## Run tests

From the repository root with the virtual environment active:

```bash
python -m pytest
```

## EC2 deployment

The backend can run behind Nginx using Uvicorn bound only to the EC2 loopback
interface:

```bash
cd /home/ubuntu/Job-Hunting-AI-Web-Tool/python
source ../.venv/bin/activate
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Recommended EC2 security-group inbound rules:

| Type | Port | Source |
| --- | ---: | --- |
| SSH | 22 | Your public IP address (`/32`) |
| HTTP | 80 | `0.0.0.0/0` |
| HTTPS | 443 | `0.0.0.0/0` |

Do not expose Uvicorn port 8000 or ChromaDB directly to the internet. Use
Nginx on ports 80 and 443 as the public entry point.

Build the React frontend for production:

```bash
cd /home/ubuntu/Job-Hunting-AI-Web-Tool/website
npm install
npm run build
```

The generated static site is placed in `website/build` and can be served by
Nginx. Configure Nginx to proxy `/api/` to `http://127.0.0.1:8000` so the
frontend and backend share the same origin.

## Common problems

If port 8000 is already in use:

```bash
sudo lsof -i :8000
```

If a Python module is missing, confirm that the virtual environment is active
and reinstall the dependencies:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```
