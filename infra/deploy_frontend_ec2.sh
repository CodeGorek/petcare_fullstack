#!/usr/bin/env bash
set -euo pipefail

# Script de despliegue para EC2 FRONTEND (React + Vite + Tailwind + Node/Nginx)
# Uso:
#   API_URL=https://tu-api-gateway.execute-api.us-east-1.amazonaws.com/prod/api \
#   S3_STATIC_URL=https://tu-bucket-petcare.s3.amazonaws.com \
#   bash infra/deploy_frontend_ec2.sh

PROJECT_PATH=$(pwd)
FRONTEND_DIR="$PROJECT_PATH/frontend"
API_URL=${API_URL:?"Debes definir API_URL apuntando al API Gateway o EC2 Backend (ej. http://IP_BACKEND/api)"}
S3_STATIC_URL=${S3_STATIC_URL:-""}

sudo apt-get update
sudo apt-get install -y curl nginx
if ! command -v node > /dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

cd "$FRONTEND_DIR"
cat << ENVEOF > "$FRONTEND_DIR/.env.production"
VITE_API_URL=$API_URL
VITE_S3_STATIC_URL=$S3_STATIC_URL
ENVEOF

npm ci
npm run build

sudo rm -rf /var/www/petcare-frontend
sudo mkdir -p /var/www/petcare-frontend
sudo cp -r "$FRONTEND_DIR/dist/"* /var/www/petcare-frontend/

sudo tee /etc/nginx/sites-available/petcare-frontend > /dev/null << 'NGXEOF'
server {
    listen 80;
    server_name _;

    root /var/www/petcare-frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGXEOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/petcare-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "===================================================="
echo "FRONTEND DESACOPLADO ACTIVO EN EL PUERTO 80"
echo "===================================================="
