"""Real native tool-continuation probe; public synthetic data, no repair claim."""

import asyncio
import json
import secrets
import time

from devguard.agent.mac1_bridge import Mac1ModelBridge
from devguard.agent.tool_messages import append_tool_exchange
from devguard.config import Settings
from devguard.models.ollama import OllamaClient

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_probe",
            "description": "Read the two synthetic integers to add.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "report_probe",
            "description": "Report the exact sum returned by adding the two read integers.",
            "parameters": {
                "type": "object",
                "properties": {"total": {"type": "integer"}},
                "required": ["total"],
                "additionalProperties": False,
            },
        },
    },
]


async def run() -> int:
    client = OllamaClient(Settings(session_token=secrets.token_urlsafe(32)))
    started = time.monotonic()
    try:
        runtime = await client.inspect()
        if not runtime.get("model_ready"):
            print(json.dumps({"status": "UNAVAILABLE", "runtime": runtime}))
            return 2
        bridge = Mac1ModelBridge(client, asyncio.get_running_loop(), runtime)
        messages = [
            {
                "role": "user",
                "content": (
                    "First call read_probe to obtain the inputs. Then add its two integers and call "
                    "report_probe with their exact total. The inputs are unknown until read_probe returns. "
                    "Use one tool per response; do not invent inputs or return prose."
                ),
            }
        ]
        action = await asyncio.to_thread(bridge.next_action, messages, TOOLS)
        if action != {"tool": "read_probe", "arguments": {}}:
            raise ValueError("Invalid probe order")
        # Generated only after the first real call. No fixture answer is returned by the model adapter.
        numbers = [10 + secrets.randbelow(90), 10 + secrets.randbelow(90)]
        result = json.dumps({"integers": numbers})
        # This isolated transport probe supplies declared non-sensitive random integers,
        # not a substitute guard port or a privacy/repair workflow.
        append_tool_exchange(messages, name="read_probe", arguments={}, result=result)
        report = await asyncio.to_thread(bridge.next_action, messages, TOOLS)
        args = report.get("arguments", {})
        if (
            report.get("tool") != "report_probe"
            or set(args) != {"total"}
            or type(args["total"]) is not int
            or args["total"] != sum(numbers)
        ):
            raise ValueError("Probe did not use its actual result")
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "runtime": runtime,
                    "actual_tool_calls": 2,
                    "tool_result_used": True,
                    "reported_total": args["total"],
                    "elapsed_seconds": round(time.monotonic() - started, 2),
                    "scope": "Native tool continuation only; not privacy or bug-repair verification",
                }
            )
        )
        return 0
    except Exception:
        print(
            json.dumps({"status": "FAILED", "reason_code": "TOOL_CONTINUATION_FAILED"})
        )
        return 1
    finally:
        await client.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
