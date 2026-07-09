# Streamlit Cloud + Groq — Easiest Deploy Guide

**Best for:** quick public hosting without Oracle/VPS complexity.  
**Cost:** **$0** (Groq free API + Streamlit Community Cloud free hosting).

---

## How it works

| Part | Service | Cost |
|------|---------|------|
| Website hosting | Streamlit Community Cloud | Free |
| AI chat answers | Groq API | Free tier |
| PDF search/indexing | FastEmbed (runs on Streamlit) | Free |

No Oracle. No Docker. No VPS.

---

## Step 1 — Get free Groq API key

1. Go to **[console.groq.com](https://console.groq.com)**
2. Sign up (Google/GitHub login works)
3. **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_`)

---

## Step 2 — Push latest code to GitHub

In VS Code terminal:

```powershell
cd "C:\Users\Macbook pro\Documents\gov-ai-assistant"
git add app.py requirements.txt .streamlit/secrets.toml.example STREAMLIT-DEPLOY.md
git commit -m "Add Groq support for Streamlit Cloud deploy"
git push
```

---

## Step 3 — Deploy on Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Sign in with **GitHub**
3. Click **New app**
4. Fill in:

| Field | Value |
|-------|--------|
| Repository | `YOUR_USERNAME/gov-ai-assistant` |
| Branch | `main` |
| Main file | `app.py` |

5. Click **Advanced settings** → **Secrets**
6. Paste:

```toml
AI_PROVIDER = "groq"
GROQ_API_KEY = "gsk-your-actual-key-here"
GROQ_MODEL = "llama-3.1-8b-instant"
FASTEMBED_MODEL = "BAAI/bge-small-en-v1.5"
ADMIN_PASSWORD = "YourSecurePassword123"
```

7. Click **Deploy**

Wait 5–10 minutes for first build. Your app URL will be:

```
https://gov-ai-assistant-xxxxx.streamlit.app
```

---

## Step 4 — Test the live app

1. Open your Streamlit URL
2. Sidebar should show:
   - **Groq API Key** ✅
   - **Active Documents: 2**
3. Wait for indexing (first time: 5–15 min)
4. Ask: *What are the main procurement rules?*

---

## Step 5 — Custom domain (tharshan.lk)

### Option A — Streamlit subdomain (free)

Your app lives at `something.streamlit.app` — share that link.

### Option B — Custom domain (may need Streamlit paid plan)

1. Streamlit app → **Settings** → **General** → custom domain
2. At your registrar for `tharshan.lk`, add CNAME:

| Type | Name | Value |
|------|------|-------|
| CNAME | `assistant` | `your-app-name.streamlit.app` |

3. Wait for DNS propagation (15 min – 48 hrs)

> If custom domain is not on your Streamlit plan, use `assistant.tharshan.lk` pointing to a redirect, or keep the `.streamlit.app` URL.

---

## Groq free tier limits

| Limit | Typical impact |
|-------|----------------|
| Requests per minute | Fine for small teams |
| Tokens per day | Enough for officer Q&A |
| Large PDF indexing | First load slower; then cached |

If you hit limits, wait a few minutes or switch model to `llama-3.1-8b-instant` (faster, lighter).

---

## Updating documents

1. Add PDFs to `data_source/` on your PC
2. `git add data_source/` → `git commit` → `git push`
3. Streamlit auto-redeploys
4. In app sidebar (Admin) → **Rebuild Knowledge Base**

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build fails | Check `requirements.txt` pushed to GitHub |
| Groq API error | Verify `GROQ_API_KEY` in Secrets |
| Indexing slow | Normal first time; keep tab open |
| App sleeps | Streamlit free tier sleeps when idle; wakes on visit |
| Memory error | Reduce PDF size or use fewer documents |

---

## Comparison

| | Streamlit + Groq | Oracle + Ollama |
|---|------------------|-----------------|
| Difficulty | ✅ Easy | ❌ Hard |
| Cost | Free | Free |
| Setup time | ~30 min | Hours/days |
| Custom domain | Limited on free | Full control |
| PC required | No | No |

---

## Recommended Groq models

| Model | Use |
|-------|-----|
| `llama-3.1-8b-instant` | Default — fast, free-friendly |
| `llama-3.3-70b-versatile` | Better answers, more quota use |

Set in Secrets: `GROQ_MODEL = "llama-3.3-70b-versatile"`

---

**You are ready.** Get Groq key → Streamlit deploy → share your live URL.
