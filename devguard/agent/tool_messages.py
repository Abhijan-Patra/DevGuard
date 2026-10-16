"""Native in-memory tool history; never serialize this conversation to audit/logs."""

from copy import deepcopy
from typing import Any


def append_tool_exchange(
    messages: list[dict[str, Any]],
    *,
    name: str,
    arguments: dict,
    result: str,
) -> None:
    """Append a validated model call and its already guarded result.

    The caller enforces the tool registry, argument schema and privacy checks.
    Only normalized function fields are replayed, never model prose/thinking.
    Arguments are the model's own validated call, retained only in this local
    conversation. Tool results must pass the guard before reaching this helper.
    """
    messages.extend(
        [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": name, "arguments": deepcopy(arguments)}}
                ],
            },
            {"role": "tool", "tool_name": name, "content": result},
        ]
    )
