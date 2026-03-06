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
5. When everything passes, the **script, notes, and README** are sent back to the browser and shown in the Jony Ive-inspired premium dark mode UI.

So: your words → matched docs → one focused prompt → checked script and commands → back to you. No need to know the words “RAG,” “vector store,” or “AST” to use it; they’re just the internal machinery.

---

## Project layout (for the curious)

| Path        | What it does |
|------------|----------------|
| `server.py` | Web server: serves the page and handles “generate” requests. |
| `static/`   | The page you see: HTML, rosa-themed CSS, and the script that talks to the server. |
| `agent.py`  | The “brain”: looks up docs, asks the model for a script, and checks it. |
| `ingest.py` | One-off: reads the Fal docs in `fal_docs/`, chops them into chunks, and stores them for search. |
| `fal_docs/` | Markdown files about Fal (apps, multi-GPU, containers, CLI, etc.). |
| `chroma_db/` | The searchable store created by `ingest.py` (don’t edit by hand). |
| `.env`      | Your API key (and optional settings). Not committed to git. |

---

## Optional settings (in `.env`)

| Variable | What it does |
|----------|----------------|
| `GOOGLE_API_KEY` or `GEMINI_API_KEY` | **Required.** Used to call the model and to embed text for search. |
| `DEALFORGE_DOCS_DIR` | Folder with Fal doc files. Default: `./fal_docs`. |
| `CHROMA_DB_DIR`     | Folder for the searchable store. Default: `./chroma_db`. |
| `DEALFORGE_CHAT_MODEL` | LLM for code gen. Default: `gemini-2.0-flash` (fast). Use `gemini-2.5-pro` for best quality. |
| `DEALFORGE_RETRIEVAL_K` | Number of doc chunks to send to the LLM. Default: `3`. Higher = more context, slower. |

You can leave the rest unset; the app uses sensible defaults.

---

## If something goes wrong

- **“Chroma database not found”** → Run `python ingest.py` once from the Dealforge folder.
- **“Missing required environment variable”** → Add `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) to a `.env` file in the Dealforge folder.
- **Blank or black page** → Hard refresh (Ctrl+Shift+R or Cmd+Shift+R) and open `http://localhost:8000` (not a file path).
- **“No relevant Fal.ai documentation was retrieved”** → Re-run `python ingest.py` and try a request that clearly mentions Fal, GPUs, containers, or deployment.

---

You’re welcome to use Dealforge as-is, tweak the prompts in `agent.py`, or add more Fal docs under `fal_docs/` and run `python ingest.py` again to refresh the knowledge base.
