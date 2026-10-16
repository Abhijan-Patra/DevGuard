"""Use Mac 1's actual async OllamaClient, not a second HTTP client/model server.

Aligned with merged main commit 831e008. Construct on the running app loop,
then invoke from the repair worker thread. Privacy remains a separate required port.
"""

import asyncio
from concurrent.futures import TimeoutError as FutureTimeout

from devguard.repair.contracts import SELECTED_MODEL, RepairError


class Mac1ModelBridge:
    def __init__(
        self,
        client,
        loop: asyncio.AbstractEventLoop,
        runtime: dict,
        timeout: float = 130,
    ):
        if (
            not runtime.get("model_ready")
            or runtime.get("model") != SELECTED_MODEL
            or not runtime.get("model_digest")
        ):
            raise RepairError("MODEL_NOT_PINNED")
        self.client, self.loop, self.timeout = client, loop, timeout
        self._metadata = {"name": SELECTED_MODEL, "digest": runtime["model_digest"]}

    @property
    def metadata(self) -> dict[str, str]:
        return dict(self._metadata)

    def next_action(self, messages: list[dict[str, str]], tools: list[dict]) -> dict:
        try:
            if asyncio.get_running_loop() is self.loop:
                raise RepairError("MODEL_CALL_REQUIRES_WORKER_THREAD")
        except RuntimeError:
            pass
        if not self.loop.is_running():
            raise RepairError("MODEL_LOOP_UNAVAILABLE")

        async def call():
            runtime = await self.client.inspect()
            if (
                not runtime.get("model_ready")
                or runtime.get("model") != SELECTED_MODEL
                or runtime.get("model_digest") != self._metadata["digest"]
            ):
                raise RepairError("MODEL_CHANGED")
            response = await self.client.chat(messages, tools=tools)
            if response.get("done_reason") == "length":
                raise RepairError("INVALID_MODEL_ACTION")
            calls = response.get("message", {}).get("tool_calls", [])
            if not isinstance(calls, list) or len(calls) != 1:
                raise RepairError("INVALID_MODEL_ACTION")
            function = calls[0].get("function", {})
            if not isinstance(function, dict) or not isinstance(
                function.get("arguments"), dict
            ):
                raise RepairError("INVALID_MODEL_ACTION")
            return {"tool": function.get("name"), "arguments": function["arguments"]}

        future = asyncio.run_coroutine_threadsafe(call(), self.loop)
        try:
            return future.result(timeout=self.timeout)
        except FutureTimeout:
            future.cancel()
            raise RepairError("MODEL_TIMEOUT") from None
        except RepairError:
            raise
        except Exception:
            raise RepairError("MODEL_UNAVAILABLE") from None


class DeferredMac1ModelBridge:
    """Keep the privacy server startable before weights finish downloading."""

    def __init__(self, client, loop: asyncio.AbstractEventLoop):
        self.client, self.loop = client, loop
        self._bridge = None

    def _get(self) -> Mac1ModelBridge:
        if self._bridge is None:
            try:
                if asyncio.get_running_loop() is self.loop:
                    raise RepairError("MODEL_CALL_REQUIRES_WORKER_THREAD")
            except RuntimeError:
                pass
            if not self.loop.is_running():
                raise RepairError("MODEL_LOOP_UNAVAILABLE")
            coroutine = self.client.inspect()
            future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
            try:
                runtime = future.result(timeout=10)
            except FutureTimeout:
                future.cancel()
                raise RepairError("MODEL_TIMEOUT") from None
            except Exception:
                raise RepairError("MODEL_UNAVAILABLE") from None
            self._bridge = Mac1ModelBridge(self.client, self.loop, runtime)
        return self._bridge

    @property
    def metadata(self) -> dict[str, str]:
        return self._get().metadata

    def next_action(self, messages, tools):
        return self._get().next_action(messages, tools)
