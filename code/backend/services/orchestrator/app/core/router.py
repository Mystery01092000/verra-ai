"""L2 — select agent + model tier + tools by capability and cost/latency/quality policy."""


class Router:
    async def route(self, step: dict) -> dict:
        # TODO: capability match via registry; smallest sufficient model first.
        return {"agent": f"{step['kind']}-agent@latest", "model_tier": "small",
                "tools": [], "reason": "policy:cheapest-sufficient"}
