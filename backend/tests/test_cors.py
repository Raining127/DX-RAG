"""SPEC 8.1 / 10.3: CORS configuration is consumed at application startup."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CorsConfigurationTests(unittest.TestCase):
    def test_configured_origins_and_default(self) -> None:
        backend = Path(__file__).resolve().parents[1]
        probe = """
import json
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    observations = []
    for origin in ('https://allowed.example', 'https://denied.example'):
        r = client.options('/api/health', headers={
            'Origin': origin, 'Access-Control-Request-Method': 'GET'
        })
        observations.append([r.status_code, r.headers.get('access-control-allow-origin')])
    print(json.dumps(observations))
"""
        for origins, expected in (
            ('["https://allowed.example"]', [[200, 'https://allowed.example'], [400, None]]),
            (None, [[200, 'https://allowed.example'], [200, 'https://denied.example']]),
        ):
            with self.subTest(origins=origins), tempfile.TemporaryDirectory() as cwd:
                env = {**os.environ, 'PYTHONPATH': str(backend), 'PYTHONIOENCODING': 'utf-8'}
                env.pop('CORS_ORIGINS', None)
                if origins is not None:
                    env['CORS_ORIGINS'] = origins
                result = subprocess.run(
                    [sys.executable, '-c', probe], cwd=cwd, env=env,
                    capture_output=True, text=True, encoding='utf-8', timeout=60,
                )
                self.assertEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stdout), expected)


if __name__ == '__main__':
    unittest.main()
