#!/usr/bin/env bash
set -euo pipefail

# Script de despliegue para EC2 BACKEND (Django DRF Modular conectado a RDS PostgreSQL)
# Uso:
#   RDS_HOST=tu-rds.xxxx.us-east-1.rds.amazonaws.com \
#   RDS_PASSWORD=TuPasswordSegura \
#   FRONTEND_URL=http://IP_O_DOMINIO_FRONTEND \
#   BACKEND_HOST=IP_O_DOMINIO_BACKEND \
#   bash infra/deploy_backend_ec2.sh

PROJECT_PATH=$(pwd)
RDS_HOST=${RDS_HOST:?"Debes definir RDS_HOST con el endpoint de Amazon RDS PostgreSQL"}
RDS_DB=${RDS_DB:-petcare_db}
RDS_USER=${RDS_USER:-petcare_user}
RDS_PASSWORD=${RDS_PASSWORD:?"Debes definir RDS_PASSWORD"}
RDS_PORT=${RDS_PORT:-5432}
BACKEND_HOST=${BACKEND_HOST:-127.0.0.1}
FRONTEND_URL=${FRONTEND_URL:-http://localhost:3000}
APIGW_URL=${APIGW_URL:-$FRONTEND_URL}
STATIC_URL=${STATIC_URL:-/static/}
SECRET_KEY=${SECRET_KEY:-$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')}

sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-dev libpq-dev nginx curl

cat << ENVEOF > "$PROJECT_PATH/.env"
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=127.0.0.1,localhost,$BACKEND_HOST,*
DB_ENGINE=postgresql
DB_NAME=$RDS_DB
DB_USER=$RDS_USER
DB_PASSWORD=$RDS_PASSWORD
DB_HOST=$RDS_HOST
DB_PORT=$RDS_PORT
CSRF_TRUSTED_ORIGINS=http://$BACKEND_HOST,$FRONTEND_URL,$APIGW_URL
CORS_ALLOWED_ORIGINS=$FRONTEND_URL,$APIGW_URL
STATIC_URL=$STATIC_URL
USE_X_FORWARDED_HOST=True
WEBPAY_AMBIENTE=INTEGRACION
WEBPAY_BASE_URL=http://$BACKEND_HOST
ENVEOF

python3 -m venv "$PROJECT_PATH/venv"
source "$PROJECT_PATH/venv/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_PATH/requirements.txt"

mkdir -p "$PROJECT_PATH/static" "$PROJECT_PATH/staticfiles"
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_petcare
python manage.py seed_precios_demo

sudo tee /etc/systemd/system/petcare-backend.service > /dev/null << SYSEOF
[Unit]
Description=Gunicorn daemon for PetCare Modular Backend
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_PATH
ExecStart=$PROJECT_PATH/venv/bin/gunicorn --workers 3 --bind unix:$PROJECT_PATH/petcare.sock petcare.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
SYSEOF

sudo systemctl daemon-reload
sudo systemctl enable --now petcare-backend
sudo systemctl restart petcare-backend

sudo tee /etc/nginx/sites-available/petcare-backend > /dev/null << NGXEOF
server {
    listen 80;
    server_name $BACKEND_HOST _;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        alias $PROJECT_PATH/staticfiles/;
    }
    location / {
        include proxy_params;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_pass http://unix:$PROJECT_PATH/petcare.sock;
    }
}
NGXEOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/petcare-backend /etc/nginx/sites-enabled/
sudo usermod -aG "$USER" www-data
chmod 755 "$HOME"
sudo nginx -t
sudo systemctl restart nginx

echo "===================================================="
echo "BACKEND MODULAR ACTIVO EN: http://$BACKEND_HOST/api/health/"
echo "===================================================="
