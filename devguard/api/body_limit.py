"""Bound request bytes before JSON decoding, without recording input bodies."""

from fastapi.responses import JSONResponse


class BodyLimitMiddleware:
    def __init__(self, app, max_bytes=192 * 1024):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            block = message.get("body", b"")
            size += len(block)
            if size > self.max_bytes:
                response = JSONResponse(status_code=413, content={"error": {
                    "code": "BODY_TOO_LARGE", "message": "Request exceeds the inspection budget"
                }})
                return await response(scope, receive, send)
            chunks.append(block)
            if not message.get("more_body", False):
                break
        body, used = b"".join(chunks), False
        chunks.clear()

        async def buffered_receive():
            nonlocal used
            if used:
                return {"type": "http.disconnect"}
            used = True
            return {"type": "http.request", "body": body, "more_body": False}

        try:
            return await self.app(scope, buffered_receive, send)
        finally:
            body = b""
