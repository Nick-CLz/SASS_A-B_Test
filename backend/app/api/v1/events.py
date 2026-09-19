"""Event ingestion endpoint: POST /v1/events (see docs/06-api-and-sdk.md §Ingestion)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import SessionDep, StoreDep, TenantDep
from app.ingestion import ingest_events
from app.models.org import Workspace
from app.schemas.events import EventsRequest, EventsResponse

router = APIRouter(tags=["ingestion"])


@router.post("/events", response_model=EventsResponse)
def ingest(
    payload: EventsRequest, session: SessionDep, ctx: TenantDep, store: StoreDep
) -> EventsResponse:
    workspace = session.get(Workspace, ctx.workspace_id)
    event_schema = workspace.event_schema if workspace is not None else {}
    result = ingest_events(store, ctx.workspace_id, event_schema, payload)
    return EventsResponse(accepted=result.accepted, rejected=result.rejected)
