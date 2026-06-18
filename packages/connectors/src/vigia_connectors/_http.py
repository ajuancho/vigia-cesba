from __future__ import annotations

import json
import ssl
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter


def make_client(
    *,
    base_url: str,
    timeout: float = 15.0,
    verify_ssl: bool = True,
    headers: dict[str, str] | None = None,
) -> httpx.AsyncClient:
    verify: bool | ssl.SSLContext = True
    if not verify_ssl:
        verify = False
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=timeout,
        verify=verify,
        headers=headers or {"User-Agent": "vigia/0.1 (+https://vigia.legal)"},
        follow_redirects=True,
    )


async def get_json(client: httpx.AsyncClient, path: str, **kwargs: Any) -> Any:
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.5, max=4),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        reraise=True,
    ):
        with attempt:
            resp = await client.get(path, **kwargs)
            resp.raise_for_status()
            return json.loads(resp.content)
    raise RuntimeError("unreachable")


async def get_text(client: httpx.AsyncClient, path: str, **kwargs: Any) -> str:
    """GET con el mismo retry que get_json, devolviendo el body como texto (HTML)."""
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.5, max=4),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        reraise=True,
    ):
        with attempt:
            resp = await client.get(path, **kwargs)
            resp.raise_for_status()
            return resp.text
    raise RuntimeError("unreachable")
