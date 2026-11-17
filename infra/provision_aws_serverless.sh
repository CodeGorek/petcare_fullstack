#!/usr/bin/env bash
set -euo pipefail

# Script opcional para ejecutar en AWS CloudShell (o terminal con AWS CLI configurado)
# Crea: Bucket S3 (fotos/ + respaldos/ + ciclo de vida Glacier), Topic SNS y Funcion Lambda.
# Uso:
#   S3_BUCKET="petcare-cloud-2026-tunombre" \
#   ALERT_EMAIL="tu-correo@ejemplo.cl" \
#   BACKEND_API_URL="http://100.63.46.73/api" \
#   BACKEND_API_TOKEN="<token_admin>" \
#   bash infra/provision_aws_serverless.sh

REGION=${AWS_REGION:-us-east-1}
S3_BUCKET=${S3_BUCKET:?"Define S3_BUCKET con un nombre unico global en minusculas"}
ALERT_EMAIL=${ALERT_EMAIL:?"Define ALERT_EMAIL para recibir alertas de respaldo SNS"}
BACKEND_API_URL=${BACKEND_API_URL:?"Define BACKEND_API_URL (ej. http://100.63.46.73/api)"}
BACKEND_API_TOKEN=${BACKEND_API_TOKEN:?"Define BACKEND_API_TOKEN (obtenido en /api/auth/login/)"}
LAMBDA_NAME=${LAMBDA_NAME:-petcare-backup-s3}
SNS_TOPIC_NAME=${SNS_TOPIC_NAME:-petcare-backups-alertas}

echo "1/4 Creando bucket S3: $S3_BUCKET ($REGION)..."
if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$S3_BUCKET" --region "$REGION" || true
else
    aws s3api create-bucket --bucket "$S3_BUCKET" --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION" || true
fi
aws s3api put-object --bucket "$S3_BUCKET" --key "fotos/"
aws s3api put-object --bucket "$S3_BUCKET" --key "respaldos/"

cat << 'LCEOF' > /tmp/petcare-lifecycle.json
{
  "Rules": [
    {
      "ID": "respaldos-a-glacier",
      "Filter": { "Prefix": "respaldos/" },
      "Status": "Enabled",
      "Transitions": [
        { "Days": 30, "StorageClass": "GLACIER" }
      ]
    }
  ]
}
LCEOF
aws s3api put-bucket-lifecycle-configuration --bucket "$S3_BUCKET" --lifecycle-configuration file:///tmp/petcare-lifecycle.json

echo "2/4 Creando Topic SNS y suscripcion..."
TOPIC_ARN=$(aws sns create-topic --name "$SNS_TOPIC_NAME" --region "$REGION" --query 'TopicArn' --output text)
aws sns subscribe --topic-arn "$TOPIC_ARN" --protocol email --notification-endpoint "$ALERT_EMAIL" --region "$REGION"
echo "IMPORTANTE: Confirma el enlace que llego a $ALERT_EMAIL para activar alertas SNS."

echo "3/4 Empaquetando y creando Lambda $LAMBDA_NAME usando LabRole..."
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
ROLE_ARN=${LAMBDA_ROLE_ARN:-"arn:aws:iam::${ACCOUNT_ID}:role/LabRole"}

mkdir -p /tmp/petcare_lambda_pkg
cp lambda/backup_rds_s3.py /tmp/petcare_lambda_pkg/
(cd /tmp/petcare_lambda_pkg && zip -q -r /tmp/petcare_lambda.zip backup_rds_s3.py)

ENV_JSON="Variables={S3_BUCKET=$S3_BUCKET,S3_STORAGE_CLASS=GLACIER_IR,SNS_TOPIC_ARN=$TOPIC_ARN,BACKEND_API_URL=$BACKEND_API_URL,BACKEND_API_TOKEN=$BACKEND_API_TOKEN}"

if aws lambda get-function --function-name "$LAMBDA_NAME" --region "$REGION" >/dev/null 2>&1; then
    aws lambda update-function-code --function-name "$LAMBDA_NAME" --zip-file fileb:///tmp/petcare_lambda.zip --region "$REGION" >/dev/null
    aws lambda update-function-configuration --function-name "$LAMBDA_NAME" --environment "$ENV_JSON" --timeout 30 --region "$REGION" >/dev/null
else
    aws lambda create-function \
        --function-name "$LAMBDA_NAME" \
        --runtime python3.12 \
        --role "$ROLE_ARN" \
        --handler backup_rds_s3.lambda_handler \
        --zip-file fileb:///tmp/petcare_lambda.zip \
        --timeout 30 \
        --environment "$ENV_JSON" \
        --region "$REGION" >/dev/null
fi

echo "4/4 Creando Trigger diario en EventBridge..."
RULE_ARN=$(aws events put-rule --name "petcare-backup-diario" --schedule-expression "rate(1 day)" --state ENABLED --region "$REGION" --query 'RuleArn' --output text)
LAMBDA_ARN=$(aws lambda get-function --function-name "$LAMBDA_NAME" --region "$REGION" --query 'Configuration.FunctionArn' --output text)
aws lambda add-permission \
    --function-name "$LAMBDA_NAME" \
    --statement-id "petcare-eventbridge-diario" \
    --action "lambda:InvokeFunction" \
    --principal events.amazonaws.com \
    --source-arn "$RULE_ARN" \
    --region "$REGION" >/dev/null 2>&1 || true
aws events put-targets --rule "petcare-backup-diario" --targets "Id=1,Arn=$LAMBDA_ARN" --region "$REGION" >/dev/null

echo "===================================================="
echo "S3 + Glacier + SNS + Lambda + Trigger LISTOS"
echo "Bucket: $S3_BUCKET | Topic: $TOPIC_ARN | Lambda: $LAMBDA_NAME"
echo "===================================================="
