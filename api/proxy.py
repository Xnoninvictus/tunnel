# api/proxy.py
import json
import requests
import base64
from http.client import responses

def handler(request):
    """
    Vercel serverless function entry point.
    Receives a JSON object with: url, method, headers, body, body_encoding.
    Returns a JSON object with: status, headers, body, body_encoding.
    """
    # Only accept POST requests
    if request.method != "POST":
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"})
        }

    try:
        data = request.json or {}
        target_url = data.get("url")
        method = data.get("method", "GET").upper()
        headers = data.get("headers", {})
        body = data.get("body")
        encoding = data.get("body_encoding")

        # Decode body if necessary
        if body and encoding == "base64":
            body = base64.b64decode(body)
        elif body and isinstance(body, str):
            body = body.encode("utf-8")

        # Forward the request to the real target
        resp = requests.request(
            method=method,
            url=target_url,
            headers=headers,
            data=body,
            timeout=30,
            allow_redirects=False  # Let the client handle redirects
        )

        # Prepare response for the local proxy
        response_headers = dict(resp.headers)
        response_body = resp.content

        # Encode binary response body as base64
        body_b64 = None
        body_encoding = None
        try:
            # Try to decode as UTF-8 for easier handling in the local proxy
            response_body.decode("utf-8")
            body_b64 = response_body.decode("utf-8")
        except UnicodeDecodeError:
            body_b64 = base64.b64encode(response_body).decode("ascii")
            body_encoding = "base64"

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": resp.status_code,
                "headers": response_headers,
                "body": body_b64,
                "body_encoding": body_encoding
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

