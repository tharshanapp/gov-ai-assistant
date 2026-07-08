# Deploy & Publish Guide — tharshan.lk

This app uses **Ollama** for free AI. Ollama must run **on the same server** as the app.

| Platform | Ollama works? | Best for |
|----------|---------------|----------|
| **Your VPS + Docker** (recommended) | ✅ Yes | Production + custom domain |
| **Oracle Cloud Free VM** | ✅ Yes | Free hosting |
| **Streamlit Community Cloud** | ❌ No | Cannot run Ollama there |
| **Your local PC only** | ✅ Yes | Testing only |

---

## Recommended: Deploy to a cloud VPS with Docker

You get a **public URL**, **custom domain (tharshan.lk)**, and **free AI** — no OpenAI billing.

### Server requirements

| Resource | Minimum |
|----------|---------|
| RAM | **8 GB** (16 GB recommended for 2 large PDFs) |
| CPU | 2+ cores |
| Disk | 20 GB |
| OS | Ubuntu 22.04 |

**Free option:** [Oracle Cloud Always Free ARM VM](https://www.oracle.com/cloud/free/) (up to 24 GB RAM).

---

## Step 1 — Push code to GitHub

On your PC:

```bash
cd gov-ai-assistant
git init
git add app.py requirements.txt Dockerfile docker-compose.yml scripts/ .streamlit/ data_source/ .gitignore .env.example
git commit -m "Government AI Assistant — Docker deploy"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/gov-ai-assistant.git
git push -u origin main
```

Commit your PDFs to `data_source/` if you want them live on first deploy.

---

## Step 2 — Create a cloud server (VPS)

1. Create an Ubuntu 22.04 VM (Oracle Cloud, DigitalOcean, Hetzner, etc.)
2. Note the **public IP address**
3. Open firewall ports: **22** (SSH), **80** (HTTP), **443** (HTTPS)

SSH into the server:

```bash
ssh ubuntu@YOUR_SERVER_IP
```

---

## Step 3 — Install Docker on the server

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker $USER
newgrp docker
```

---

## Step 4 — Deploy the app

```bash
git clone https://github.com/YOUR_USERNAME/gov-ai-assistant.git
cd gov-ai-assistant

# Set a secure admin password
echo "ADMIN_PASSWORD=YourSecurePassword123" > .env

# Build and start (first run downloads AI models — allow 15–30 min)
docker compose up -d --build

# Watch logs
docker compose logs -f app
```

When ready, open: `http://YOUR_SERVER_IP:8501`

---

## Step 5 — Connect tharshan.lk (custom domain)

### A. DNS at your domain registrar

| Type | Name | Value | TTL |
|------|------|-------|-----|
| **A** | `assistant` | `YOUR_SERVER_IP` | 3600 |

This creates **assistant.tharshan.lk** → your server.

> Apex (`tharshan.lk` without subdomain) usually needs ALIAS/ANAME. A subdomain is simpler.

### B. Install Nginx + free HTTPS (on the VPS)

```bash
sudo apt install -y nginx certbot python3-certbot-nginx

sudo tee /etc/nginx/sites-available/gov-ai <<'EOF'
server {
    listen 80;
    server_name assistant.tharshan.lk;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/gov-ai /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

sudo certbot --nginx -d assistant.tharshan.lk
```

Live URL: **https://assistant.tharshan.lk**

---

## Step 6 — Add new documents in production

**Option A — Git (recommended)**

1. Add PDFs to `data_source/` on your PC
2. `git push`
3. On server: `git pull && docker compose restart app`

**Option B — Upload via SCP**

```bash
scp "MY_CIRCULAR.pdf" ubuntu@YOUR_SERVER_IP:~/gov-ai-assistant/data_source/
ssh ubuntu@YOUR_SERVER_IP "cd gov-ai-assistant && docker compose restart app"
```

Then in the app sidebar (Admin) → **Rebuild Knowledge Base**.

---

## Useful commands

```bash
# Status
docker compose ps

# Logs
docker compose logs -f app
docker compose logs -f ollama

# Restart after config change
docker compose restart app

# Stop
docker compose down

# Update after git pull
docker compose up -d --build
```

---

## Alternative: Streamlit Community Cloud (OpenAI only)

Streamlit Cloud **cannot** run Ollama. If you use Streamlit Cloud instead:

1. Set `AI_PROVIDER = "openai"` in Secrets
2. Add paid `OPENAI_API_KEY`
3. Deploy at [share.streamlit.io](https://share.streamlit.io)
4. Map CNAME to `your-app.streamlit.app`

This costs money (OpenAI API) but requires no VPS management.

---

## Summary

| Goal | Solution |
|------|----------|
| Free AI | Ollama on VPS |
| Public website | Docker + Nginx on VPS |
| Custom domain | DNS A record → VPS IP + Certbot HTTPS |
| No local PC needed | Server runs 24/7 in the cloud |

For **tharshan.lk + free AI**, use **VPS + Docker** — not Streamlit Cloud.
