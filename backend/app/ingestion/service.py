"""Event ingestion: workspace allow-list + PII guard + idempotent write to the store.

Items that fail validation or the PII guard are **rejected with a reason** (never silently
dropped). Writes are idempotent on the row id (client-supplied ``event_id``), so re-sending
a batch doesn't double-count. See docs/06-api-and-sdk.md §Ingestion.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.analytics.store import DuckStore, EventRow, ExposureRow, new_id
from app.ingestion.pii import pii_reason
from app.models.base import utcnow
from app.schemas.events import EventIn, EventsRequest, RejectedItem


@dataclass
class IngestResult:
    accepted: int = 0
    rejected: list[RejectedItem] = field(default_factory=list)


def _allowed_events(event_schema: dict[str, Any] | None) -> Any:
    """The workspace allow-list: ``None``/empty = allow all; list of names; or name→props."""
    return (event_schema or {}).get("events")


def _validate_event(event: EventIn, allowed: Any) -> str | None:
    if allowed:
        names = set(allowed) if isinstance(allowed, list) else set(allowed.keys())
        if event.name not in names:
            return f"event '{event.name}' is not in the workspace allow-list"
        if isinstance(allowed, dict):
            props_allowed = allowed.get(event.name)
            if isinstance(props_allowed, list):
                for key in event.props:
                    if key not in props_allowed:
                        return f"property '{key}' is not allowed for event '{event.name}'"
    return pii_reason(event.unit_id, event.props)


def _json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, separators=(",", ":"))


def ingest_events(
    store: DuckStore,
    workspace_id: uuid.UUID,
    event_schema: dict[str, Any] | None,
    payload: EventsRequest,
) -> IngestResult:
    result = IngestResult()
    allowed = _allowed_events(event_schema)
    ws = str(workspace_id)

    event_rows: list[EventRow] = []
    for index, event in enumerate(payload.events):
        reason = _validate_event(event, allowed)
        if reason is not None:
            result.rejected.append(RejectedItem(index=index, kind="event", reason=reason))
            continue
        event_rows.append(
            (
                event.event_id or new_id(),
                ws,
                event.unit_id,
                event.name,
                event.ts or utcnow(),
                event.value,
                _json(event.props),
            )
        )
        result.accepted += 1

    exposure_rows: list[ExposureRow] = []
    for index, exposure in enumerate(payload.exposures):
        reason = pii_reason(exposure.unit_id, exposure.attrs)
        if reason is not None:
            result.rejected.append(RejectedItem(index=index, kind="exposure", reason=reason))
            continue
        exposure_rows.append(
            (
                new_id(),
                ws,
                exposure.experiment_key,
                exposure.variant_key,
                exposure.unit_id,
                exposure.ts or utcnow(),
                _json(exposure.attrs),
            )
        )
        result.accepted += 1

    store.insert_events(event_rows)
    store.insert_exposures(exposure_rows)
    return result
