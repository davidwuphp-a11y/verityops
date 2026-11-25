"""Minimal integration seam. The collector owns readback; actor output is diagnostic."""
from .contract import judge, supported_start


def observe(task, read_state, invoke, deliveries=1):
    if deliveries < 1:
        raise ValueError("At least one delivery is required")

    def read(phase):
        try:
            return read_state(phase)
        except (OSError, TimeoutError, ValueError) as exc:
            return {"unavailable": type(exc).__name__}

    before = read("before")
    replies = []
    if not supported_start(task, before):
        return dict(before=before, after=None, replies=[], decision=judge(task, before, before))
    for attempt in range(1, deliveries + 1):
        try:
            replies.append(invoke(attempt, task))
        except Exception as exc:
            # Preserve evidence after a failed invocation; never automatically retry an exception.
            replies.append("execution_error:" + type(exc).__name__)
            break
    after = read("after")
    return dict(before=before, after=after, replies=replies, decision=judge(task, before, after))
