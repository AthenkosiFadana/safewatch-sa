"""AWS Lambda Function URL adapter for the full Flask API.

Used when ApiMode=functionurl (environments where API Gateway is unavailable,
e.g. restricted lab accounts). Converts a Lambda Function URL event into a
WSGI request and runs the same Flask application the local dev server uses.
"""

import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

application = create_app()
STATUS_MESSAGES = {200: "200 OK", 201: "201 Created", 204: "204 No Content", 400: "400 Bad Request",
                   401: "401 Unauthorized", 403: "403 Forbidden", 404: "404 Not Found",
                   405: "405 Method Not Allowed", 409: "409 Conflict", 429: "429 Too Many Requests",
                   500: "500 Internal Server Error"}


def _environ(event: dict) -> dict:
    ctx = (event.get("requestContext") or {}).get("http") or {}
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body)
    elif isinstance(body, str):
        body = body.encode("utf-8")

    query = event.get("rawQueryString") or ""
    environ = {
        "REQUEST_METHOD": ctx.get("method", "GET"),
        "PATH_INFO": event.get("rawPath") or "/",
        "QUERY_STRING": query,
        "SERVER_NAME": headers.get("host", "localhost"),
        "SERVER_PORT": "443",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "https",
        "wsgi.input": __import__("io").BytesIO(body),
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "CONTENT_LENGTH": str(len(body)),
    }
    for key, value in headers.items():
        if key not in ("content-length", "content-type", "host"):
            environ["HTTP_" + key.upper().replace("-", "_")] = value
    if "content-type" in headers:
        environ["CONTENT_TYPE"] = headers["content-type"]
    return environ


def handler(event, context):
    captured = {}

    def start_response(status, response_headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = response_headers
        return lambda data: None

    chunks = application(_environ(event), start_response)
    body = b"".join(chunks)
    is_text = any("text" in v or "json" in v for k, v in captured["headers"] if k.lower() == "content-type")
    if is_text and isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    elif isinstance(body, bytes):
        body = base64.b64encode(body).decode("ascii")

    status_code = int(captured.get("status", "500").split(" ")[0])
    return {
        "statusCode": status_code,
        "headers": dict(captured.get("headers", [])),
        "body": body,
        "isBase64Encoded": not is_text,
    }
