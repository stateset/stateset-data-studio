import asyncio

from backend.api.logging_utils import log_call


class _State:
    request_id = "req-1"


class _Request:
    state = _State()


def test_log_call_does_not_copy_string_annotations():
    async def endpoint(request: "Request"):  # noqa: F821
        return {"ok": True}

    wrapped = log_call(endpoint)
    assert "request" not in wrapped.__annotations__
    assert asyncio.run(wrapped(request=_Request())) == {"ok": True}
