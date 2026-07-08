#!/bin/bash
# Run on your Ubuntu VPS after cloning the repo:
#   chmod +x scripts/setup-vps.sh && ./scripts/setup-vps.sh
set -e

DOMAIN="${1:-assistant.tharshan.lk}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Government AI Assistant — VPS setup"
echo "    Domain: ${DOMAIN}"
echo "    Project: ${REPO_DIR}"

if [ ! -f "${REPO_DIR}/.env" ]; then
  cp "${REPO_DIR}/.env.production.example" "${REPO_DIR}/.env"
  echo ""
  echo "IMPORTANT: Edit .env and set a strong ADMIN_PASSWORD:"
  echo "  nano ${REPO_DIR}/.env"
  echo ""
  read -r -p "Press Enter after you have edited .env..."

fi

echo "==> Installing Docker (if needed)..."
if ! command -v docker >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y docker.io docker-compose-v2 git curl
  sudo usermod -aG docker "$USER"
  echo "Log out and back in, then re-run this script."
  exit 0
fi

echo "==> Starting Docker containers (first run: 15–30 min for AI models)..."
cd "${REPO_DIR}"
docker compose up -d --build

echo "==> Installing Nginx + Certbot (if needed)..."
if ! command -v nginx >/dev/null 2>&1; then
  sudo apt install -y nginx certbot python3-certbot-nginx
fi

echo "==> Configuring Nginx..."
sudo cp "${REPO_DIR}/deploy/nginx-gov-ai.conf" /etc/nginx/sites-available/gov-ai
sudo sed -i "s/assistant.tharshan.lk/${DOMAIN}/g" /etc/nginx/sites-available/gov-ai
sudo ln -sf /etc/nginx/sites-available/gov-ai /etc/nginx/sites-enabled/gov-ai
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

echo ""
echo "==> Setup complete (HTTP)."
echo "    Test: http://${DOMAIN}  (or http://$(curl -s ifconfig.me):8501 before DNS propagates)"
echo ""
echo "After DNS points to this server, run HTTPS:"
echo "  sudo certbot --nginx -d ${DOMAIN}"
echo ""
echo "Useful commands:"
echo "  docker compose logs -f app"
echo "  docker compose ps"
