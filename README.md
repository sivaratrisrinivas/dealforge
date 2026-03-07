# Dealforge

**Turn a messy client email into a ready-to-run deployment script — in one click.**

---

## What is this?

Dealforge takes the kind of request you get from a customer (e.g. “We need to process 100,000 images a day with a custom Docker setup and multiple GPUs”) and turns it into:

- **A full Python script** you can save and run: it uses Fal’s APIs the way the docs describe (custom containers, multi-GPU, etc.).
- **Short notes** explaining what the script does and why it’s written that way.
- **Exact commands** to test and deploy: `fal run` and `fal deploy` with the right app name and flags.

You paste the requirement, click **Generate blueprint**, and get something you can hand to a client or use as a starting point — without rewriting everything from scratch.

---

## Why use it?

- **Save time** — No more manually translating vague emails into deployment code.
- **Fewer mistakes** — The app checks the script against Fal’s patterns and only shows code that fits.
- **Faster demos** — From “here’s what we need” to “here’s a script and how to run it” in one step.

It’s built for people who work with Fal (solutions engineers, forward-deployed engineers, anyone helping customers run on Fal). The goal is to make every request feel like it gets a direct, usable answer.

---

## How do I run it?

### 1. What you need

- **Python 3.10 or newer**
- A **Google AI API key** (used to power the “brain” that writes the script).  
  Create one if you don’t have it, then put it in a file named `.env` in the Dealforge folder:

  ```
  GOOGLE_API_KEY=your_key_here
  ```

  (You can use `GEMINI_API_KEY` instead of `GOOGLE_API_KEY` if you prefer; the app checks both.)

### 2. First-time setup

Open a terminal in the Dealforge folder and run:

```bash
# Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Build the internal “knowledge base” from the Fal docs (do this once)
python ingest.py
```

When ingestion finishes, you’ll see a short summary (e.g. how many docs and chunks were added). That means the app is ready to use.

### 3. Start the app

```bash
source .venv/bin/activate   # If you closed the terminal
uvicorn server:app --reload
```

Then open your browser at **http://localhost:8000**.

### 4. Use it

- Paste a client email or requirement into the text area (or click **Try with sample request** to fill it with an example).
- Click **Generate blueprint**.
- Wait a few moments. You’ll get the Python script, the notes, and the run/deploy commands. You can copy the script and the commands and use them as-is or adjust them.

---

## How does it work under the hood?

Roughly in order:

1. **Your input** is sent to the backend.
2. The app looks up **relevant bits of Fal’s docs** (multi-GPU, custom containers, CLI, etc.) from a local searchable store that was filled when you ran `python ingest.py`.
3. Those bits plus your text are sent to a **language model** (Google’s Gemini) with clear instructions: “You are a Fal solutions engineer; output a valid Python script and a short README using only these patterns.”
4. The app **checks the script**: it must be valid Python and must use the right Fal building blocks (e.g. `fal.App`, `@fal.endpoint("/")`, `DistributedRunner`). If something’s wrong, it retries up to a few times.
5. When everything passes, the **script, notes, and README** are sent back to the browser and shown in the rosa-themed UI.

So: your words → matched docs → one focused prompt → checked script and commands → back to you. The Fal docs are embedded once into `chroma_db`; each new user prompt is embedded at request time so it can be matched against those stored doc vectors. Exact repeated prompts are cached in memory, so the same request can come back almost instantly while the process stays warm.

---

## Project layout (for the curious)

| Path        | What it does |
|------------|----------------|
| `server.py` | Web server: serves the page and handles “generate” requests. |
| `static/`   | The page you see: HTML, rosa-themed CSS, and the script that talks to the server. |
| `agent.py`  | The “brain”: looks up docs, asks the model for a script, and checks it. |
| `dealforge_chroma.py` | Small Chroma integration shim used to disable product telemetry cleanly. |
| `ingest.py` | One-off: reads the Fal docs in `fal_docs/`, chops them into chunks, and stores them for search. |
| `fal_docs/` | Markdown files about Fal (apps, multi-GPU, containers, CLI, etc.). |
| `chroma_db/` | The searchable store created by `ingest.py` (don’t edit by hand). |
| `scripts/` | Railway build/deploy helper scripts. |
| `.env`      | Your API key (and optional settings). Not committed to git. |

---

## Optional settings (in `.env`)

| Variable | What it does |
|----------|----------------|
| `GOOGLE_API_KEY` or `GEMINI_API_KEY` | **Required.** Used to call the model and to embed text for search. |
| `DEALFORGE_DOCS_DIR` | Folder with Fal doc files. Default: `./fal_docs`. |
| `CHROMA_DB_DIR`     | Folder for the searchable store. Default: `./chroma_db`. |
| `DEALFORGE_FAST_CHAT_MODEL` | First model tried for generation. Default: `gemini-3-flash-preview`. |
| `DEALFORGE_CHAT_MODEL` | Fallback model when the fast path fails validation. Default: `gemini-2.5-pro`. |
| `DEALFORGE_RETRIEVAL_K` | Number of doc chunks to send to the LLM. Default: `3`. Higher = more context, slower. |

You can leave the rest unset; the app uses sensible defaults.

---

## Deploy on Railway

1. **Install CLI and log in** (one-time):
   ```bash
   npm i -g @railway/cli   # or: brew install railway
   railway login
   ```
2. **From the project root**, link or create a project, then set build/start and deploy:
   ```bash
   railway init --name dealforge   # or: railway link --project <existing-project-id>
   railway add --service web
   railway variables --service web --set "GOOGLE_API_KEY=your_key"
   railway variables --service web --set "RAILPACK_BUILD_CMD=bash scripts/railway-build.sh"
   railway variables --service web --set "RAILPACK_START_CMD=uvicorn server:app --host 0.0.0.0 --port \$PORT --log-level warning --no-access-log"
   railway up --detach --service web
   ```
3. **Add a public domain** in the Railway dashboard (Settings → Networking → Generate domain) so the app is reachable.
4. **Optional:** Pin Python with `railway variables --service web --set "RAILPACK_PYTHON_VERSION=3.12"`.

**One-shot after login:** From project root, run `bash scripts/railway-deploy.sh`. Set `GOOGLE_API_KEY` in the project (Dashboard → Variables or `railway variables --service web --set "GOOGLE_API_KEY=..."`) before the first deploy so the build’s `python ingest.py` succeeds.

The build runs `scripts/railway-build.sh` (install deps + `python ingest.py`), so the Chroma DB is baked into the image.

---

## If something goes wrong

- **“Chroma database not found”** → Run `python ingest.py` once from the Dealforge folder.
- **“Missing required environment variable”** → Add `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) to a `.env` file in the Dealforge folder.
- **Blank or black page** → Hard refresh (Ctrl+Shift+R or Cmd+Shift+R) and open `http://localhost:8000` (not a file path).
- **“No relevant Fal.ai documentation was retrieved”** → Re-run `python ingest.py` and try a request that clearly mentions Fal, GPUs, containers, or deployment.

---

You’re welcome to use Dealforge as-is, tweak the prompts in `agent.py`, or add more Fal docs under `fal_docs/` and run `python ingest.py` again to refresh the knowledge base.
