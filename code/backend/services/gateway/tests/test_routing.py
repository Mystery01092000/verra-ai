from app.config import settings
from app.main import _resolve_upstream


def test_default_routes_to_orchestrator() -> None:
    assert _resolve_upstream("runs") == f"{settings.ORCHESTRATOR_URL}/internal/runs"
    assert (
        _resolve_upstream("runs/abc/approve")
        == f"{settings.ORCHESTRATOR_URL}/internal/runs/abc/approve"
    )
    assert (
        _resolve_upstream("tools/tax/compute-liability")
        == f"{settings.ORCHESTRATOR_URL}/internal/tools/tax/compute-liability"
    )


def test_ingest_routes_to_ingestion() -> None:
    assert _resolve_upstream("ingest") == f"{settings.INGESTION_URL}/internal/ingest"


def test_audit_routes_to_audit_service() -> None:
    assert _resolve_upstream("audit/events") == f"{settings.AUDIT_URL}/internal/events"
    assert _resolve_upstream("audit/verify") == f"{settings.AUDIT_URL}/internal/verify"


def test_holdings_routes_preserve_full_path() -> None:
    # keep_prefix=True: the holdings service serves everything under /internal/holdings/...
    assert _resolve_upstream("holdings") == f"{settings.HOLDINGS_URL}/internal/holdings"
    assert (
        _resolve_upstream("holdings/consolidation")
        == f"{settings.HOLDINGS_URL}/internal/holdings/consolidation"
    )
    assert (
        _resolve_upstream("holdings/some-holding-id")
        == f"{settings.HOLDINGS_URL}/internal/holdings/some-holding-id"
    )


def test_prefix_must_match_whole_segment() -> None:
    # "auditor" must not be captured by the "audit" prefix.
    assert _resolve_upstream("auditor/x") == f"{settings.ORCHESTRATOR_URL}/internal/auditor/x"
    assert _resolve_upstream("ingestion") == f"{settings.ORCHESTRATOR_URL}/internal/ingestion"
    assert _resolve_upstream("holdingsx/y") == f"{settings.ORCHESTRATOR_URL}/internal/holdingsx/y"
