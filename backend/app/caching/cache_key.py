"""
Deterministic cache key calculation with strict tenant isolation.
Every key incorporates the organization ID and project ID to prevent any cross-tenant data leakage.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional


def compute_cache_fingerprint(
    organization_id: str,
    project_id: Optional[str],
    model: str,
    messages: list[dict[str, Any]],
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    stop: Optional[list[str]] = None,
    tools: Optional[list[dict[str, Any]]] = None,
    tool_choice: Optional[Any] = None,
    response_format: Optional[dict[str, Any]] = None,
) -> str:
    """
    Computes a canonical SHA-256 fingerprint representing the deterministic request parameters.
    Format: cache:{org_id[:8]}:{sha256[:32]}
    """
    # Normalize messages to ensure deterministic serialization
    normalized_messages = []
    for msg in messages:
        normalized_messages.append({
            "role": str(msg.get("role", "")).strip().lower(),
            "content": msg.get("content"),
            "name": msg.get("name"),
            "tool_calls": msg.get("tool_calls"),
            "tool_call_id": msg.get("tool_call_id"),
        })

    canonical_data = {
        "org": str(organization_id),
        "proj": str(project_id) if project_id else None,
        "model": str(model).strip().lower(),
        "messages": normalized_messages,
        "temperature": round(float(temperature), 4) if temperature is not None else None,
        "top_p": round(float(top_p), 4) if top_p is not None else None,
        "max_tokens": max_tokens,
        "stop": sorted(stop) if stop else None,
        "tools": tools,
        "tool_choice": tool_choice,
        "response_format": response_format,
    }

    serialized = json.dumps(canonical_data, sort_keys=True, ensure_ascii=True, default=str)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    org_prefix = str(organization_id).replace("-", "")[:8]
    return f"cache:{org_prefix}:{digest[:32]}"

