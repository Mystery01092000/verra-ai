"""L4 — verify: grounding/citations, schema, numeric checks, confidence; gate if consequential."""


class Critic:
    async def verify(self, out: dict) -> dict:
        grounded = len(out.get("citations", [])) > 0  # TODO real grounding check
        confidence = 0.92 if grounded else 0.4
        return {"ok": grounded, "confidence": confidence,
                "needs_approval": confidence < 0.7}
