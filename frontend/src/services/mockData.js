// Pre-packaged demo mock dataset matching 100% strictly with backend schemas.
// Explanation:   { modules: [{file, summary}], functions: [{file, name, summary, params, returns}] }
// DepGraph:      { nodes: [{id, label, file}], edges: [{source, target}] }
// TestResult:    { test_files: [{file, source}], coverage_percent, passed, failed, log }
// RefactorResult:{ files: [{original_file, refactored_source, breaking_changes: []}] }

export const MOCK_JOB_RESULT = {
  explanation: {
    modules: [
      {
        file: "src/auth/jwt_handler.py",
        summary: "Handles JSON Web Token generation, signature validation, RS256 algorithm verification, and token rotation workflows."
      },
      {
        file: "src/database/orm_session.py",
        summary: "Manages asynchronous PostgreSQL connection pooling, transactional scopes, and repository query abstractions."
      },
      {
        file: "src/api/routes_v1.py",
        summary: "Core RESTful router defining client authentication, data transformation pipelines, and rate-limiting middleware."
      },
      {
        file: "src/utils/crypto_vault.py",
        summary: "Encryption helper using AES-256-GCM for sensitive user payload storage and key rotation management."
      }
    ],
    functions: [
      {
        file: "src/auth/jwt_handler.py",
        name: "verify_jwt_token",
        summary: "Validates bearer token structure, checks expiration timestamp, and decrypts claim payload.",
        params: "token: str, secret_key: str, algorithms: list[str] = ['RS256']",
        returns: "dict[str, Any]"
      },
      {
        file: "src/auth/jwt_handler.py",
        name: "issue_refresh_token",
        summary: "Generates cryptographically safe 64-byte hex token with 30-day sliding expiry for session continuation.",
        params: "user_id: str, scope: str",
        returns: "str"
      },
      {
        file: "src/database/orm_session.py",
        name: "get_async_db_session",
        summary: "Yields scoped async SQLAlchemy session context manager with automatic rollback on unhandled exceptions.",
        params: "read_only: bool = False",
        returns: "AsyncGenerator[AsyncSession, None]"
      },
      {
        file: "src/api/routes_v1.py",
        name: "handle_user_login",
        summary: "Authenticates request credentials, rate limits IP attempts, and issues access + refresh token pair.",
        params: "payload: LoginDTO, db: AsyncSession",
        returns: "AuthTokenResponse"
      },
      {
        file: "src/utils/crypto_vault.py",
        name: "encrypt_payload",
        summary: "Encrypts raw byte sequence using AES-256-GCM with randomly generated 96-bit initialization vector.",
        params: "raw_data: bytes, master_key: bytes",
        returns: "bytes"
      }
    ]
  },
  dependency_graph: {
    nodes: [
      { id: "node-1", label: "routes_v1.py", file: "src/api/routes_v1.py" },
      { id: "node-2", label: "jwt_handler.py", file: "src/auth/jwt_handler.py" },
      { id: "node-3", label: "orm_session.py", file: "src/database/orm_session.py" },
      { id: "node-4", label: "crypto_vault.py", file: "src/utils/crypto_vault.py" },
      { id: "node-5", label: "config_loader.py", file: "src/config_loader.py" }
    ],
    edges: [
      { source: "node-1", target: "node-2" },
      { source: "node-1", target: "node-3" },
      { source: "node-2", target: "node-4" },
      { source: "node-2", target: "node-5" },
      { source: "node-3", target: "node-5" }
    ]
  },
  tests: {
    coverage_percent: 94.8,
    passed: 24,
    failed: 0,
    test_files: [
      {
        file: "tests/test_jwt_handler.py",
        source: `import pytest
from src.auth.jwt_handler import verify_jwt_token, issue_refresh_token

def test_verify_valid_jwt():
    raw_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
    claims = verify_jwt_token(raw_token, secret_key="test_secret")
    assert claims["user_id"] == "usr_8921"
    assert claims["role"] == "admin"

def test_issue_refresh_token():
    token = issue_refresh_token(user_id="usr_8921", scope="api_full")
    assert len(token) == 64
    assert isinstance(token, str)`
      },
      {
        file: "tests/test_crypto_vault.py",
        source: `import pytest
from src.utils.crypto_vault import encrypt_payload

def test_encrypt_payload_integrity():
    data = b"confidential_user_data"
    key = b"0" * 32
    encrypted = encrypt_payload(data, key)
    assert encrypted != data
    assert len(encrypted) > len(data)`
      }
    ],
    log: `============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-7.4.2, pluggy-1.3.0
rootdir: /app
plugins: asyncio-0.21.1, cov-4.1.0
collected 24 items

tests/test_jwt_handler.py .........................                      [ 62%]
tests/test_crypto_vault.py .........                                    [100%]

---------- coverage: platform win32, python 3.11.4-final-0 -----------
Name                             Stmts   Miss  Cover
----------------------------------------------------
src/api/routes_v1.py                42      2    95%
src/auth/jwt_handler.py             56      3    95%
src/database/orm_session.py          34      2    94%
src/utils/crypto_vault.py           28      1    96%
----------------------------------------------------
TOTAL                              160      8    94.8%

============================== 24 passed in 1.42s ==============================`
  },
  refactor: {
    files: [
      {
        original_file: "src/auth/jwt_handler.py",
        refactored_source: `# [Refactored by CodeOracle Vision-X]
# Modernized RS256 token validator with async public key caching and non-blocking verification.

import jwt
import aiocache
from typing import Dict, Any, List

@aiocache.cached(ttl=600)
async def fetch_public_key(kid: str) -> str:
    # Async JWKS retrieve logic
    return "-----BEGIN PUBLIC KEY-----\\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA..."

async def verify_jwt_token_async(token: str, key_id: str, algorithms: List[str] = ["RS256"]) -> Dict[str, Any]:
    """
    Refactored async verification method preventing event loop thread blocking.
    """
    public_key = await fetch_public_key(key_id)
    payload = jwt.decode(token, public_key, algorithms=algorithms)
    return payload`,
        breaking_changes: [
          "Signature changed from synchronous `verify_jwt_token` to `async def verify_jwt_token_async`",
          "Parameter `secret_key` replaced with mandatory `key_id` string for JWKS lookup"
        ]
      },
      {
        original_file: "src/utils/crypto_vault.py",
        refactored_source: `# [Refactored by CodeOracle Vision-X]
# Standardized cryptography implementation using Hazmat AESGCM primitive.

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class CryptoVault:
    def __init__(self, master_key: bytes):
        if len(master_key) not in (16, 24, 32):
            raise ValueError("Master key must be 128, 192, or 256 bits")
        self.aesgcm = AESGCM(master_key)

    def encrypt(self, raw_data: bytes, associated_data: bytes = None) -> bytes:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, raw_data, associated_data)
        return nonce + ciphertext`,
        breaking_changes: [
          "Functional helper `encrypt_payload` converted into object class `CryptoVault`",
          "Output payload now prepends 12-byte IV nonce to ciphertext buffer"
        ]
      }
    ]
  }
};
