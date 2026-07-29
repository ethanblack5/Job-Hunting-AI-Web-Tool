# Job-Hunting AI Web Tool

This project has a React frontend and a FastAPI backend. Run them in two
separate terminal windows during development.

## Prerequisites

- Python 3.10 or newer
- Node.js and npm

Check that they are installed:

```bash
python3 --version
node --version
npm --version
```

On macOS, if `npm` is not found and Homebrew is installed:

```bash
brew install node
```

## Start the backend

From the repository root, create and activate a Python virtual environment:

```bash
cd /Users/user/Job-Hunting-AI-Web-Tool
python3 -m venv venv
source venv/bin/activate
```

Install the project dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start FastAPI from the repository root:

```bash
python -m uvicorn python.api:app --reload
```

The backend is now available at:

- API: <http://127.0.0.1:8000>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- RemoteOK jobs endpoint: <http://127.0.0.1:8000/job-batch/>

Populate the shared `job_postings_v2` ChromaDB collection from RemoteOK:

```bash
curl -X POST "http://127.0.0.1:8000/api/jobs/refresh"
```

Run a semantic search against the indexed jobs:

```bash
curl -X POST "http://127.0.0.1:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "machine learning engineer",
    "skills": ["python", "pytorch"],
    "location": "remote",
    "experience_level": "mid",
    "top_n": 10
  }'
```

Both indexing and search use `all-MiniLM-L6-v2` and the same collection under
`vector_db/chroma_store`. The first indexing or search request may take longer
while the model is downloaded and loaded.

For demo-scale performance, embeddings are generated in batches of 32 and
Chroma inserts are split into batches of 100. Search requests are capped at 50
results and automatically reduced when the collection contains fewer jobs.
These defaults can be adjusted through `SemanticMatchingService` and
`ChromaJobStore` constructor arguments.

Stop the server with `Ctrl+C`.

If port 8000 is already in use, either stop the existing server or use another
port:

```bash
python -m uvicorn python.api:app --reload --port 8001
```

## Start the frontend

Open a second terminal and run:

```bash
cd /Users/user/Job-Hunting-AI-Web-Tool/website
npm install
npm start
```

The React development server should open automatically. If it does not, visit:

<http://localhost:3000>

Stop the frontend with `Ctrl+C`.

After the first setup, you normally only need:

```bash
cd /Users/user/Job-Hunting-AI-Web-Tool/website
npm start
```

## Run semantic ranking

Activate your Python virtual environment from the repository root:

```bash
cd /Users/user/Job-Hunting-AI-Web-Tool
source venv/bin/activate
```

If your environment is named `.venv` instead, use:

```bash
source .venv/bin/activate
```

Install the semantic-ranking dependencies into the active environment:

```bash
python -m pip install sentence-transformers scikit-learn requests
```

Confirm that the packages are installed in the Python environment currently in
use:

```bash
which python
python -c "import sentence_transformers, sklearn; print('Dependencies installed')"
```

Run the pipeline from the `semantic_matching` directory:

```bash
cd semantic_matching
```

First, fetch a sample of jobs from RemoteOK:

```bash
python remoteok_client.py --limit 25
```

Next, clean and normalize the job records:

```bash
python preprocess_jobs.py
```

Finally, rank the jobs against a natural-language query:

```bash
python semantic_baseline.py "Python machine learning engineer with cloud experience"
```

To return a different number of results:

```bash
python semantic_baseline.py "React frontend developer" --top-k 10
```

This workflow creates:

```text
remoteok_jobs_raw.json
remoteok_jobs_normalized.json
```

The first ranking run downloads the `all-MiniLM-L6-v2` model and therefore
requires an internet connection. Later runs use the cached model.

## Run both services

Keep both terminal windows running:

```text
Terminal 1: FastAPI  -> http://127.0.0.1:8000
Terminal 2: React    -> http://localhost:3000
```

## AWS deployment hardening

The EC2 security-group allowlist and automated EBS snapshot workflow are
documented in [infra/aws/README.md](infra/aws/README.md). The accompanying
script is plan-only unless it is run with `--apply`.

## Common errors

### `npm: command not found`

Install Node.js, which includes npm:

```bash
brew install node
```

### `ModuleNotFoundError`

Make sure the virtual environment is active, then install the missing backend
dependencies:

```bash
cd /Users/user/Job-Hunting-AI-Web-Tool
source venv/bin/activate
python -m pip install -r requirements.txt
```

### `[Errno 48] Address already in use`

Find the process using port 8000:

```bash
lsof -i :8000
```

Stop that process with `Ctrl+C` in its original terminal, or start FastAPI on
port 8001:

```bash
python -m uvicorn python.api:app --reload --port 8001
```
