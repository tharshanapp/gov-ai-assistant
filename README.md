# 🏛️ Government Regulatory AI Assistant

A production-ready Streamlit application that helps public sector officers query government circulars, guidelines, and regulations with **precise, citation-backed answers**.

Built with **Streamlit**, **LlamaIndex**, **Ollama** (free), or **OpenAI**.

> **Easiest deploy:** Read **[STREAMLIT-DEPLOY.md](STREAMLIT-DEPLOY.md)** — Streamlit Cloud + free Groq API (no Oracle/VPS).  
> **VPS deploy:** Read **[DEPLOY.md](DEPLOY.md)** or **[SETUP-GUIDE.md](SETUP-GUIDE.md)** — Ollama on Oracle/Hetzner.

---

## Features

| Feature | Description |
|---------|-------------|
| **Official UI** | Deep navy, gold accents, and clean typography suited to a government portal |
| **RAG Pipeline** | LlamaIndex + ChromaDB indexes documents from `data_source/` |
| **Strict Citations** | Every answer cites Organization, Year, and Section/Paragraph |
| **Conversational Memory** | Follow-up questions via session-aware chat memory |
| **Admin Panel** | Password-protected sidebar for document management instructions |
| **Error Resilience** | Graceful handling of missing API keys and unreadable files |

---

## Project Structure

```
gov-ai-assistant/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── .env.example            # Local environment template
├── .gitignore
├── .streamlit/
│   └── config.toml         # Theme & server settings
├── data_source/            # Drop PDF / DOCX / TXT files here
│   └── .gitkeep
└── .chroma_db/             # Auto-generated vector store (gitignored)
```

---

## Local Development

> **Important:** Use **Python 3.11 or 3.12**. Python 3.14 is too new — packages like `pandas` will fail to install on Windows.

### 1. Clone or copy this folder

Use `gov-ai-assistant/` as the **repository root** when pushing to GitHub (recommended for a clean Streamlit Cloud deployment).

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure secrets

**Option A — Environment file (local only)**

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY, ADMIN_PASSWORD, etc.
```

**Option B — Streamlit secrets (recommended)**

Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "sk-your-key-here"
OPENAI_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"
ADMIN_PASSWORD = "your-secure-admin-password"
```

> `.streamlit/secrets.toml` is gitignored. Never commit API keys.

### 5. Add documents

Place files in `data_source/` using descriptive names:

```
Finance_Ministry_Procurement_Circular_2023.pdf
Public_Service_Commission_Leave_Guidelines_2022.docx
```

### 6. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## Deploy to GitHub

### 1. Create a new repository

On [GitHub](https://github.com/new), create a repository (e.g. `gov-ai-assistant`).

### 2. Initialize and push

From inside the `gov-ai-assistant/` folder:

```bash
git init
git add app.py requirements.txt README.md .gitignore .env.example .streamlit/config.toml data_source/.gitkeep
git commit -m "Initial commit: Government Regulatory AI Assistant"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/gov-ai-assistant.git
git push -u origin main
```

> **Tip:** Commit sample documents to `data_source/` if you want them available on first deploy. Otherwise, upload via admin workflow after deployment.

---

## Deploy to Streamlit Community Cloud

### 1. Sign in

Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.

### 2. Create a new app

| Field | Value |
|-------|-------|
| **Repository** | `YOUR_USERNAME/gov-ai-assistant` |
| **Branch** | `main` |
| **Main file path** | `app.py` |

### 3. Add secrets

In the app dashboard → **Settings** → **Secrets**, paste:

```toml
OPENAI_API_KEY = "sk-your-production-key"
OPENAI_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"
ADMIN_PASSWORD = "your-secure-admin-password"
```

Click **Save**. The app will redeploy automatically.

### 4. Verify deployment

- Sidebar shows **API Key Configured** and **Database Connected**
- **Active Documents** reflects files in `data_source/`
- Ask a test question and confirm citations appear in the gold callout box

---

## Custom Domain: tharshan.lk

Streamlit Community Cloud supports custom domains on paid plans. If your plan includes custom domains, or you use a reverse proxy, follow these steps.

### Option A — Streamlit Cloud native custom domain

1. Open your app on [share.streamlit.io](https://share.streamlit.io)
2. Go to **Settings** → **General** → **Custom subdomain / Custom domain**
3. Enter `tharshan.lk` (or a subdomain such as `assistant.tharshan.lk`)
4. Streamlit will provide a **CNAME target** (e.g. `your-app.streamlit.app`)

### Option B — DNS configuration at your registrar

Log in to your domain registrar (where `tharshan.lk` is managed) and add:

| Type | Name / Host | Value / Target | TTL |
|------|-------------|----------------|-----|
| **CNAME** | `assistant` (for `assistant.tharshan.lk`) | `your-app-name.streamlit.app` | 3600 |
| **CNAME** | `@` (apex — if supported) | `your-app-name.streamlit.app` | 3600 |

> **Note:** Many registrars do not allow CNAME on the apex (`tharshan.lk`). Use a subdomain like `assistant.tharshan.lk` or `gov.tharshan.lk`, or configure **ALIAS/ANAME** if your DNS provider supports it.

### DNS propagation

- Changes can take **15 minutes to 48 hours**
- Verify with: `nslookup assistant.tharshan.lk`
- Ensure SSL is active (Streamlit Cloud provisions HTTPS automatically)

### Alternative: Cloudflare proxy

If using Cloudflare:

1. Add `tharshan.lk` to Cloudflare
2. Create a CNAME: `assistant` → `your-app-name.streamlit.app`
3. Enable **Proxied** (orange cloud) for DDoS protection and caching control

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Chat model (`gpt-4o` for higher quality) |
| `EMBED_MODEL` | No | `text-embedding-3-small` | Embedding model |
| `ADMIN_PASSWORD` | No | `admin123` | Sidebar admin panel password |

---

## Admin: Adding Documents

1. Unlock **Administrator** in the sidebar with the admin password
2. Add PDF, DOCX, TXT, or MD files to `data_source/`
3. Click **Rebuild Knowledge Base**
4. For Streamlit Cloud: commit new files to GitHub and redeploy, or use your CI workflow

**Filename tips for better metadata extraction:**

```
Organization_Type_Topic_Year.pdf
Ministry_of_Finance_Procurement_Circular_2024.pdf
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "API Key Configured" shows ⚠️ | Set `OPENAI_API_KEY` in Secrets or `.env` |
| No documents indexed | Add files to `data_source/` and click Rebuild |
| PDF skipped | File may be scanned/image-only; use OCR or a text-based PDF |
| `.doc` not supported | Convert to `.docx` or `.pdf` |
| Custom domain not working | Confirm CNAME target, wait for DNS propagation, try subdomain |
| Out of memory on Cloud | Reduce document count or use smaller chunks |

---

## Security Notes

- Never commit `.env`, `secrets.toml`, or API keys to GitHub
- Change the default `ADMIN_PASSWORD` before production use
- Restrict document content to non-classified, approved public circulars
- Review OpenAI [data usage policies](https://openai.com/policies) for your jurisdiction

---

## License

MIT — use and adapt freely for public sector projects.

---

**Live domain target:** [tharshan.lk](https://tharshan.lk) · Built for government officers who need answers they can cite with confidence.
