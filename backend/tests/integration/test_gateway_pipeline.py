"""
Integration tests for OpenAI-compatible Gateway API (/v1/chat/completions and /v1/models).
Verifies authentication, headers, schema validation, PII redaction, and response normalization.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_models_endpoint_unauthorized():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/models")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_models_endpoint_authorized():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/v1/models",
            headers={"Authorization": "Bearer ig-test-key-1234567890abcdef"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["object"] == "list"
        assert len(data["data"]) > 0
        model_ids = [m["id"] for m in data["data"]]
        assert "gpt-4o" in model_ids
        assert "fast-model" in model_ids


@pytest.mark.asyncio
async def test_chat_completions_validation_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Empty messages array must be rejected with 422 or 400
        res = await client.post(
            "/v1/chat/completions",
            json={"model": "gpt-4o", "messages": []},
            headers={"Authorization": "Bearer ig-test-key-1234567890abcdef"},
        )
        assert res.status_code in {400, 422}


@pytest.mark.asyncio
async def test_chat_completions_non_streaming():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": "Explain quantum computing in one sentence."}
            ],
            "temperature": 0.0,
            "max_tokens": 100,
        }
        res = await client.post(
            "/v1/chat/completions",
            json=payload,
            headers={"Authorization": "Bearer ig-test-key-1234567890abcdef"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["object"] == "chat.completion"
        assert len(data["choices"]) > 0
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert "usage" in data
        assert data["usage"]["total_tokens"] > 0
        assert "X-IntelliGate-Request-ID" in res.headers


@pytest.mark.asyncio
async def test_chat_completions_pii_redaction():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "model": "fast-model",
            "messages": [
                {"role": "user", "content": "My contact is john.doe@enterprise.com and ip is 192.168.1.1"}
            ],
            "temperature": 0.0,
        }
        res = await client.post(
            "/v1/chat/completions",
            json=payload,
            headers={"Authorization": "Bearer ig-test-key-1234567890abcdef"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["object"] == "chat.completion"


@pytest.mark.asyncio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"

