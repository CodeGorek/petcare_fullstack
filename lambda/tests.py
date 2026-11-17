import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

LAMBDA_PATH = Path(__file__).resolve().parent / 'backup_rds_s3.py'
SPEC = importlib.util.spec_from_file_location('petcare_lambda_backup', LAMBDA_PATH)
backup_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup_mod)


class _FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql):
        self.last_sql = sql

    def fetchone(self):
        return (5,)


class _FakeConn:
    def cursor(self):
        return _FakeCursor()

    def close(self):
        pass


class LambdaBackupTests(unittest.TestCase):
    @patch.dict(os.environ, {'S3_BUCKET': 'petcare-respaldos', 'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123:backup', 'S3_STORAGE_CLASS': 'GLACIER_IR'})
    def test_trigger_eventbridge_respalda_a_s3_y_notifica_sns(self):
        s3 = MagicMock()
        sns = MagicMock()
        res = backup_mod.lambda_handler(
            {'source': 'aws.events'},
            s3_client=s3,
            sns_client=sns,
            db_connect=_FakeConn,
        )
        self.assertEqual(res['status'], 'ok')
        self.assertEqual(res['storage_class'], 'GLACIER_IR')
        self.assertEqual(res['fuente'], 'rds_postgresql')
        s3.put_object.assert_called_once()
        self.assertEqual(s3.put_object.call_args.kwargs['Bucket'], 'petcare-respaldos')
        sns.publish.assert_called_once()

    @patch.dict(os.environ, {'DB_HOST': '', 'S3_BUCKET': 'petcare-respaldos', 'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123:backup', 'BACKEND_API_URL': 'http://100.63.46.73/api', 'BACKEND_API_TOKEN': 'tok-demo'})
    def test_respaldo_via_api_sin_vpc(self):
        s3 = MagicMock()
        sns = MagicMock()
        fake_fetch = MagicMock(return_value={'status': 'ok'})
        res = backup_mod.lambda_handler(
            {'source': 'aws.events'},
            s3_client=s3,
            sns_client=sns,
            http_fetcher=fake_fetch,
        )
        self.assertEqual(res['status'], 'ok')
        self.assertEqual(res['fuente'], 'backend_api')
        self.assertGreaterEqual(fake_fetch.call_count, 2)
        s3.put_object.assert_called_once()
        sns.publish.assert_called_once()

    @patch.dict(os.environ, {'S3_BUCKET': 'petcare-respaldos', 'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123:backup'})
    def test_api_gateway_responde_json_200(self):
        s3 = MagicMock()
        sns = MagicMock()
        res = backup_mod.lambda_handler(
            {'httpMethod': 'POST', 'path': '/backup'},
            s3_client=s3,
            sns_client=sns,
            db_connect=_FakeConn,
        )
        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        self.assertEqual(body['status'], 'ok')

    @patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123:backup'})
    def test_s3_image_trigger(self):
        s3 = MagicMock()
        sns = MagicMock()
        res = backup_mod.lambda_handler(
            {'Records': [{'s3': {'bucket': {'name': 'petcare-static'}, 'object': {'key': 'fotos/thor.jpg', 'size': 2048}}}]},
            s3_client=s3,
            sns_client=sns,
        )
        self.assertEqual(res['statusCode'], 200)
        sns.publish.assert_called_once()


if __name__ == '__main__':
    unittest.main()
