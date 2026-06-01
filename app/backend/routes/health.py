from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json
import os
import socket
import requests
from requests.exceptions import RequestException

router = APIRouter()


def _requests_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def _check_service(host: str) -> dict:
    result = {
        "host": host,
        "dns_resolved": False,
        "http_reachable": False,
        "status_code": None,
        "content_type": None,
        "error": None,
    }

    try:
        socket.getaddrinfo(host, 443)
        result["dns_resolved"] = True
    except Exception as exc:
        result["error"] = f"DNS resolution failed: {exc}"
        return result

    try:
        session = _requests_session()
        response = session.get(f"https://{host}", timeout=10)
        result["http_reachable"] = True
        result["status_code"] = response.status_code
        result["content_type"] = response.headers.get("Content-Type")
        if response.status_code >= 400:
            result["error"] = f"HTTP status {response.status_code}"
    except RequestException as exc:
        result["error"] = f"HTTP request failed: {exc}"

    return result


@router.get("/")
async def root():
    return {"message": "Welcome to AI Hedge Fund API"}


@router.get("/status")
def status():
    services = [
        _check_service("api.twelvedata.com"),
        _check_service("api.financialdatasets.ai"),
    ]
    healthy = all(service["dns_resolved"] and service["http_reachable"] for service in services)
    return {
        "status": "ok" if healthy else "degraded",
        "services": services,
    }


@router.get("/ping")
async def ping():
    async def event_generator():
        for i in range(5):
            # Create a JSON object for each ping
            data = {"ping": f"ping {i+1}/5", "timestamp": i + 1}

            # Format as SSE
            yield f"data: {json.dumps(data)}\n\n"

            # Wait 1 second
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
