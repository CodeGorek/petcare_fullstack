"""AWS Lambda serverless handler for PetCare RDS backups to S3, S3 image events, and SNS alerts."""
import gzip
import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TABLAS_RESPALDO = (
    'pacientes_tutor',
    'pacientes_mascota',
    'agenda_veterinario',
    'agenda_citamedica',
    'agenda_fichaclinica',
    'agenda_recordatoriovacuna',
    'farmacia_lotemedicamento',
    'cobros_servicioclinico',
    'cobros_cuentaatencion',
    'cobros_pagowebpay',
)


def _exportar_resumen_rds(db_connect=None):
    """Collect row counts and snapshot metadata from PostgreSQL RDS."""
    if db_connect is None:
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            port=int(os.environ.get('DB_PORT', '5432')),
            dbname=os.environ.get('DB_NAME', 'petcare_db'),
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            connect_timeout=5,
        )
    else:
        conn = db_connect()

    tablas = {}
    try:
        with conn.cursor() as cur:
            for tabla in TABLAS_RESPALDO:
                cur.execute(f'SELECT COUNT(*) FROM {tabla};')
                tablas[tabla] = cur.fetchone()[0]
    finally:
        conn.close()
    return tablas


def _publicar_sns(sns_client, topic_arn, subject, payload):
    if not topic_arn:
        return None
    return sns_client.publish(
        TopicArn=topic_arn,
        Subject=subject[:100],
        Message=json.dumps(payload, ensure_ascii=False, indent=2),
    )


def _aws_clients():
    import boto3
    return boto3.client('s3'), boto3.client('sns')


def lambda_handler(event, context=None, s3_client=None, sns_client=None, db_connect=None):
    """Handle EventBridge backup triggers, S3 image upload triggers, and API Gateway heavy tasks."""
    event = event or {}
    if s3_client is None or sns_client is None:
        default_s3, default_sns = _aws_clients()
        s3_client = s3_client or default_s3
        sns_client = sns_client or default_sns

    bucket = os.environ.get('S3_BUCKET', '')
    topic_arn = os.environ.get('SNS_TOPIC_ARN', '')
    storage_class = os.environ.get('S3_STORAGE_CLASS', 'STANDARD_IA')
    ahora = datetime.now(timezone.utc)

    # Mode 1: S3 trigger when new image/photo arrives under estaticos/fotos/
    if 'Records' in event and event['Records'] and 's3' in event['Records'][0]:
        record = event['Records'][0]['s3']
        key = record['object']['key']
        size = record['object'].get('size', 0)
        resumen = {'evento': 's3_imagen_recibida', 'bucket': record['bucket']['name'], 'archivo': key, 'bytes': size}
        _publicar_sns(sns_client, topic_arn, 'PetCare S3: Nueva imagen procesada', resumen)
        return {'statusCode': 200, 'body': json.dumps(resumen)}

    # Mode 2: API Gateway HTTP heavy-task invocation
    is_http = 'httpMethod' in event or 'requestContext' in event

    try:
        tablas = _exportar_resumen_rds(db_connect=db_connect)
        snapshot = {
            'proyecto': 'PetCare',
            'generado_en': ahora.isoformat(),
            'origen': 'api_gateway' if is_http else 'eventbridge_trigger',
            'tablas': tablas,
        }
        body_gz = gzip.compress(json.dumps(snapshot, ensure_ascii=False).encode('utf-8'))
        s3_key = f"respaldos/petcare_backup_{ahora.strftime('%Y%m%d_%H%M%S')}.json.gz"

        if bucket:
            s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=body_gz,
                ContentType='application/gzip',
                StorageClass=storage_class,
            )

        resultado = {
            'status': 'ok',
            's3_bucket': bucket,
            's3_key': s3_key,
            'storage_class': storage_class,
            'bytes_comprimidos': len(body_gz),
            'tablas': tablas,
        }
        _publicar_sns(sns_client, topic_arn, 'PetCare Backup RDS -> S3 completado', resultado)

        if is_http:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(resultado, ensure_ascii=False),
            }
        return resultado
    except Exception as exc:
        logger.exception('Error ejecutando Lambda PetCare')
        _publicar_sns(sns_client, topic_arn, 'PetCare ALERTA: Error en respaldo Lambda', {'error': str(exc)})
        if is_http:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'status': 'error', 'detail': str(exc)}),
            }
        raise
