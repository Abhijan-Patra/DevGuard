"""Declared buggy hackathon fixture: line totals currently ignore quantity."""


def cart_total(items: list[dict] | None) -> int:
    return sum(item["unit_amount"] for item in items)
