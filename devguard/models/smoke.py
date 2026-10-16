"""Synthetic real-tool smoke test; no private input and no canned model answer."""

import asyncio
import json
import re
import time

from devguard.config import MODEL, Settings
from devguard.models.ollama import OllamaClient


async def run():
    client = OllamaClient(Settings(session_token="smoke-only-not-an-operator-token-0000"))
    try:
        runtime = await client.inspect()
        if not runtime["model_ready"]:
            state = runtime["reason_code"]
            print(json.dumps({"status": state, "runtime": runtime}))
            return 2
        tool = {"type": "function", "function": {
            "name": "multiply", "description": "Multiply two bounded integer inputs.",
            "parameters": {"type": "object", "properties": {
                "a": {"type": "integer"}, "b": {"type": "integer"}},
                "required": ["a", "b"], "additionalProperties": False}
        }}
        messages = [{"role": "user", "content":
                     "Use the multiply tool to calculate 37 times 19, then state the result."}]
        started = time.monotonic()
        first = await client.chat(messages, tools=[tool])
        message = first["message"]
        calls = message.get("tool_calls", [])
        if len(calls) != 1:
            raise ValueError("Expected one actual tool call")
        function = calls[0].get("function", {})
        args = function.get("arguments")
        if function.get("name") != "multiply" or not isinstance(args, dict):
            raise ValueError("Unknown or malformed tool")
        if set(args) != {"a", "b"} or any(type(v) is not int for v in args.values()):
            raise ValueError("Invalid tool arguments")
        if (args["a"], args["b"]) not in {(37, 19), (19, 37)}:
            raise ValueError("Arguments did not match the requested operation")
        result = args["a"] * args["b"]
        # Never propagate or display hidden reasoning.
        messages.append({"role": "assistant", "content": message.get("content", ""),
                         "tool_calls": calls})
        messages.append({"role": "tool", "tool_name": "multiply", "content": str(result)})
        final = await client.chat(messages, tools=[tool])
        if final["message"].get("tool_calls") or not re.search(
            r"(?<!\d)703(?!\d)", final["message"].get("content", "")
        ):
            raise ValueError("Final answer did not use the actual tool result")
        print(json.dumps({"status": "PASS", "model": MODEL, "runtime": runtime,
                          "actual_tool_calls": 1, "tool_result": result,
                          "elapsed_seconds": round(time.monotonic() - started, 2),
                          "scope": "Synthetic tool roundtrip only; not privacy/repair verification"}))
        return 0
    except Exception:
        print(json.dumps({"status": "FAILED", "reason": "Model tool roundtrip did not complete"}))
        return 1
    finally:
        await client.close()


def main():
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
