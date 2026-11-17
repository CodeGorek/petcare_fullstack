# Guía de Despliegue Modular en AWS (Evaluación 4 - PetCare)

Esta guía resume el mapa completo de tus pizarras y cómo desplegar cada parte del repositorio desde GitHub hacia AWS.

## 1. Estructura del repositorio para GitHub

- **Backend Django modular (raíz del proyecto):** dividido en 6 apps (`nucleo`, `usuarios`, `pacientes`, `farmacia`, `agenda`, `cobros`), más el agregador de API REST en `petcare/api_urls.py`.
- **`frontend/`:** aplicación React + Vite + Tailwind CSS desacoplada que se comunica por token DRF con `VITE_API_URL` y carga imágenes/estáticos desde `VITE_S3_STATIC_URL`.
- **`lambda/`:** función serverless Python (`backup_rds_s3.py`) para respaldos RDS → S3, eventos de imágenes S3, tareas pesadas desde API Gateway y alertas SNS.
- **`infra/`:** scripts de despliegue independientes para `EC2 Backend` y `EC2 Frontend`.

---

## 2. Red y Security Groups (`VPC` + `SG ↔ SG`)

1. **`sg-frontend`** (EC2 Frontend):
   - **Inbound:** HTTP (`80`) y HTTPS (`443`) desde `0.0.0.0/0`; SSH (`22`) solo desde tu IP.
2. **`sg-backend`** (EC2 Backend):
   - **Inbound:** HTTP (`80`) o puerto de Gunicorn **únicamente desde `sg-frontend` / API Gateway** (evita dejar el backend abierto a `0.0.0.0/0` salvo para pruebas controladas); SSH (`22`) solo desde tu IP.
3. **`sg-rds`** (RDS PostgreSQL):
   - **Inbound:** PostgreSQL (`5432`) **únicamente desde `sg-backend` y `sg-lambda`**. Nunca abrir `0.0.0.0/0`.
4. **`sg-lambda`** (si conectas Lambda dentro de la VPC para acceder a RDS privado):
   - **Outbound:** hacia `sg-rds` en puerto `5432` y salida HTTPS (`443`) mediante NAT/VPC Endpoint para S3 y SNS.

---

## 3. Base de datos (`RDS PostgreSQL`) y Estáticos (`S3` + `CDN` + `Glacier`)

1. Crear instancia **Amazon RDS PostgreSQL** (`petcare_db`, usuario `petcare_user`), desactivar acceso público si usas VPC privada y anotar el **Endpoint**.
2. Crear bucket **Amazon S3** (ej. `petcare-estaticos-respaldos`) con carpetas:
   - `fotos/` (estáticos e imágenes públicas servidas detrás de **CloudFront / CDN**).
   - `respaldos/` (backups generados por Lambda).
3. En **S3 → Management → Lifecycle rules**, crear una regla para `respaldos/` que mueva objetos antiguos a **S3 Glacier** (por ejemplo, transición a Glacier Flexible Retrieval después de 30 días) para optimizar costos de almacenamiento en frío.

---

## 4. Máquinas Virtuales (`EC2 Backend` y `EC2 Frontend`)

### En `EC2 Backend` (Ubuntu)
```bash
git clone <URL_DE_TU_REPO_GITHUB>
cd petcare_fullstack
RDS_HOST="<endpoint-rds>" \
RDS_PASSWORD="<tu-clave-rds>" \
BACKEND_HOST="<ip-publica-backend>" \
FRONTEND_URL="http://<ip-o-dominio-frontend>" \
bash infra/deploy_backend_ec2.sh
```
Verifica que responda `{"status": "ok"}` en `http://<ip-publica-backend>/api/health/`.

### En `EC2 Frontend` (Ubuntu)
```bash
git clone <URL_DE_TU_REPO_GITHUB>
cd petcare_fullstack
API_URL="http://<ip-o-api-gateway>/api" \
S3_STATIC_URL="https://<tu-cloudfront-o-bucket-s3>" \
bash infra/deploy_frontend_ec2.sh
```

---

## 5. `API Gateway` (Rate Limit / Mitigación DDoS)

1. Crear una **HTTP API** o **REST API** en **Amazon API Gateway** apuntando al `EC2 Backend` (por ejemplo `/api/{proxy+}`) y una ruta pesada (por ejemplo `POST /backup`) apuntando a tu función Lambda.
2. En **Throttling / Stage Settings**, configurar **Rate Limit** y **Burst Limit** (ej. 50 req/s y burst 100) para mitigar picos DoS/DDoS antes de que alcancen tu instancia EC2.

---

## 6. `Lambda` + `Trigger` + `SNS`

1. Crear un **Topic en Amazon SNS** (ej. `petcare-backups-alertas`) y suscribir tu correo electrónico (confirmar el correo de suscripción).
2. En AWS Academy (`voclabs`), usa el rol `LabRole` para la Lambda. Tienes dos modos listos en `lambda/backup_rds_s3.py`:
   - **Modo directo en el editor web (sin subir ZIP y sin NAT Gateway):** pega el contenido de `lambda/backup_rds_s3.py` en la consola de AWS Lambda (handler `lambda_function.lambda_handler` si conservas el archivo por defecto o `backup_rds_s3.lambda_handler`) y configura `BACKEND_API_URL=http://<IP_BACKEND>/api`, `BACKEND_API_TOKEN=<tu_token>`, `S3_BUCKET=<tu-bucket>`, `S3_STORAGE_CLASS=GLACIER_IR`, `SNS_TOPIC_ARN=<arn-sns>`.
   - **Modo directo a RDS dentro de la VPC:** empaqueta con `bash lambda/build_lambda_zip.sh` y configura `DB_HOST`, `DB_PORT=5432`, `DB_NAME=petcare_db`, `DB_USER`, `DB_PASSWORD`, `S3_BUCKET` y `SNS_TOPIC_ARN` (requiere S3 Gateway Endpoint / acceso a SNS).
3. Agregar un **Trigger de EventBridge** (ej. `cron(0 3 * * ? *)` para respaldo diario) y un evento S3 en `fotos/` si deseas notificar nuevas imágenes.
