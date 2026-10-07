from __future__ import annotations

from typing import Any


def tool_policy(
    *,
    allowed_tools: list[str] | None = None,
    denied_tools: list[str] | None = None,
    allowed_actions: list[str] | None = None,
    max_amount_minor: int | None = None,
    currency: str | None = None,
    require_human_approval: bool | None = None,
    human_approved: bool | None = None,
    expires_at: str | None = None,
    review_on_unknown: bool | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    if allowed_tools is not None:
        policy["allowed_tools"] = allowed_tools
    if denied_tools is not None:
        policy["denied_actions"] = denied_tools
    if allowed_actions is not None:
        policy["allowed_actions"] = allowed_actions
    if max_amount_minor is not None:
        policy["max_amount_minor"] = max_amount_minor
    if currency is not None:
        policy["currency"] = currency
    if require_human_approval is not None:
        policy["require_human_approval"] = require_human_approval
    if human_approved is not None:
        policy["human_approved"] = human_approved
    if expires_at is not None:
        policy["expires_at"] = expires_at
    if review_on_unknown is not None:
        policy["review_on_unknown"] = review_on_unknown
    if extra:
        policy.update(extra)
    return policy
