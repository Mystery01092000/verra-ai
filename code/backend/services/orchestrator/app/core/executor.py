"""L3 — run steps/tool calls: parallelism, timeouts, retries+backoff, breakers, idempotency."""


class Executor:
    async def execute(self, step: dict, route: dict) -> dict:
        # TODO: call model_gateway /v1/complete; deterministic calculators preferred for math-of-record.
        return {"step": step, "result": None, "citations": []}
