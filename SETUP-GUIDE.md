# Complete Setup Guide — Publish to tharshan.lk

Follow these **3 phases** in order. Total time: ~1–2 hours (first deploy).

---

## Architecture (what you are building)

```
Internet users
      ↓
assistant.tharshan.lk  (your domain, HTTPS)
      ↓
Nginx on VPS  (free SSL certificate)
      ↓
Streamlit app  (Docker container — your UI)
      ↓
Ollama AI  (Docker container — free, no API key)
      ↓
PDF documents  (data_source/ folder)
```

Your PC is **not needed** after deployment. The server runs 24/7.

---

# PHASE 1 — Push to GitHub (on your Windows PC)

## 1.1 Install Git (if needed)

Download: [git-scm.com/download/win](https://git-scm.com/download/win)

## 1.2 Create GitHub repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `gov-ai-assistant`
3. Set to **Public** or **Private**
4. Do **NOT** add README (you already have one)
5. Click **Create repository**

## 1.3 Copy your PDFs into the project

Make sure these files are in:

```
C:\Users\Macbook pro\Documents\gov-ai-assistant\data_source\
```

Example:
- `PROCUREMENT MANUAL 2024.pdf`
- `FINANCIAL REGULATION.pdf`

## 1.4 Push from VS Code terminal

Open terminal in VS Code (`Ctrl + `` ` ``):

```powershell
cd "C:\Users\Macbook pro\Documents\gov-ai-assistant"

git init
git add app.py requirements.txt Dockerfile docker-compose.yml
git add scripts/ deploy/ .streamlit/ data_source/
git add .gitignore .env.example .env.production.example
git add README.md DEPLOY.md SETUP-GUIDE.md

git commit -m "Government AI Assistant — production deploy with Ollama"

git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/gov-ai-assistant.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

> **Login prompt?** Use a [GitHub Personal Access Token](https://github.com/settings/tokens) as the password.

---

# PHASE 2 — Create a cloud server (VPS)

You need a server with **at least 8 GB RAM** (16 GB recommended).

## Option A — Oracle Cloud (FREE forever)

1. Sign up: [oracle.com/cloud/free](https://www.oracle.com/cloud/free/)
2. Create an **Ampere A1** VM (ARM):
   - Shape: `VM.Standard.A1.Flex`
   - OCPUs: **4**
   - RAM: **12–24 GB**
   - OS: **Ubuntu 22.04**
3. Download your **SSH private key** (.key file)
4. Note the **Public IP address**
5. Open ports in Oracle **Security List / Firewall**:
   - **22** (SSH)
   - **80** (HTTP)
   - **443** (HTTPS)

## Option B — Paid VPS (simpler setup)

| Provider | Plan | Cost |
|----------|------|------|
| [Hetzner](https://www.hetzner.com/cloud) | CX32 (8 GB RAM) | ~€6/month |
| [DigitalOcean](https://www.digitalocean.com) | 8 GB droplet | ~$48/month |

Choose **Ubuntu 22.04**.

## 2.1 Connect to your server

From PowerShell on your PC:

```powershell
ssh -i "C:\path\to\your-key.key" ubuntu@YOUR_SERVER_IP
```

(On Hetzner/DigitalOcean the user may be `root` instead of `ubuntu`.)

---

# PHASE 3 — Deploy on the server

Run these commands **on the VPS** (after SSH login):

## 3.1 Clone your GitHub repo

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/gov-ai-assistant.git
cd gov-ai-assistant
```

## 3.2 Create production config

```bash
cp .env.production.example .env
nano .env
```

Set a strong password:

```
ADMIN_PASSWORD=YourSecurePassword123!
```

Save: `Ctrl+O`, Enter, `Ctrl+X`

## 3.3 Run automated setup

```bash
chmod +x scripts/setup-vps.sh
./scripts/setup-vps.sh assistant.tharshan.lk
```

**First run takes 15–30 minutes** (downloads AI models). Watch progress:

```bash
docker compose logs -f app
```

When you see `Starting Government AI Assistant`, it is ready.

## 3.4 Test before DNS

Open in browser:

```
http://YOUR_SERVER_IP:8501
```

You should see the Government AI Assistant login page.

---

# PHASE 4 — Connect tharshan.lk

## 4.1 DNS settings (at your domain registrar)

Log in where you bought **tharshan.lk** and add:

| Type | Name / Host | Value | TTL |
|------|-------------|-------|-----|
| **A** | `assistant` | `YOUR_SERVER_IP` | 3600 |

This creates: **assistant.tharshan.lk** → your server

Wait 15–60 minutes for DNS to propagate.

Check:

```powershell
nslookup assistant.tharshan.lk
```

## 4.2 Enable HTTPS (free SSL)

On the VPS:

```bash
sudo certbot --nginx -d assistant.tharshan.lk
```

Follow prompts (enter email, agree to terms).

**Live URL:** [https://assistant.tharshan.lk](https://assistant.tharshan.lk)

---

# PHASE 5 — Using the live app

| Task | How |
|------|-----|
| Ask questions | Open the website, type in chat |
| Admin panel | Sidebar → enter `ADMIN_PASSWORD` |
| Add new PDFs | Upload to `data_source/` via git or SCP, then Admin → Rebuild |
| View logs | `docker compose logs -f app` |
| Restart | `docker compose restart app` |
| Update code | `git pull && docker compose up -d --build` |

---

# Checklist

### On your PC
- [ ] PDFs in `data_source/`
- [ ] Code pushed to GitHub

### On VPS
- [ ] Ubuntu 22.04, 8 GB+ RAM
- [ ] Ports 22, 80, 443 open
- [ ] `docker compose up` running
- [ ] App loads at server IP

### Domain
- [ ] A record: `assistant` → server IP
- [ ] Certbot HTTPS installed
- [ ] https://assistant.tharshan.lk works

---

# Troubleshooting

| Problem | Fix |
|---------|-----|
| `docker compose` not found | `sudo apt install docker-compose-v2` |
| App shows "Ollama not running" | `docker compose logs ollama` — wait for models to download |
| Indexing very slow | Normal first time (10–30 min for large PDFs) |
| Site not loading | Check firewall ports 80/443; `docker compose ps` |
| DNS not working | Wait longer; verify A record at registrar |
| Out of memory | Use 12 GB+ RAM VM; restart: `docker compose restart` |

---

# Cost summary

| Item | Cost |
|------|------|
| Ollama AI | **Free** |
| Oracle Cloud VM | **Free** (Always Free tier) |
| Domain tharshan.lk | Already yours |
| SSL certificate | **Free** (Let's Encrypt) |
| OpenAI API | **Not needed** |

**Total: $0/month** on Oracle Cloud free tier.

---

Need help? Share which phase you are on and any error message.
