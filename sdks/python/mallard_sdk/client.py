"""Mallard client: local assignment + batched, resilient event tracking.

Design goals (see docs/06-api-and-sdk.md §SDK):
- assignment is computed **locally** (same hashing as the server) — no network on the hot path;
- ``track`` batches and never throws into the host app, even when the service is unreachable;
- privacy guards reject obvious PII client-side.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from mallard_sdk.engine import assign
from mallard_sdk.privacy import assert_no_pii, assert_pseudonymous_unit
from mallard_sdk.spec import Assignment, ExperimentSpec


class Mallard:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "http://localhost:8000",
        flush_at: int = 20,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._flush_at = flush_at
        self._specs: dict[str, ExperimentSpec] = {}
        self._queue: list[dict[str, Any]] = []

    def load_specs(self, specs: list[ExperimentSpec]) -> None:
        """Load experiment configs for local assignment."""
        self._specs = {spec.key: spec for spec in specs}

    def get_variant(
        self,
        experiment_key: str,
        unit_id: str,
        attributes: dict[str, Any] | None = None,
        *,
        log_exposure: bool = True,
    ) -> Assignment:
        assert_pseudonymous_unit(unit_id)
        spec = self._specs.get(experiment_key)
        if spec is None:
            return Assignment(experiment_key, False, False, None, "unknown_experiment")
        result = assign(spec, unit_id, attributes)
        if log_exposure and result.in_experiment and result.variant_key is not None:
            self._queue.append(
                {
                    "exposure": {
                        "experiment_key": result.experiment_key,
                        "variant_key": result.variant_key,
                        "unit_id": unit_id,
                    }
                }
            )
            self._maybe_flush()
        return result

    def peek_variant(
        self, experiment_key: str, unit_id: str, attributes: dict[str, Any] | None = None
    ) -> Assignment:
        """Assign without logging an exposure (for triggered analysis)."""
        return self.get_variant(experiment_key, unit_id, attributes, log_exposure=False)

    def track(
        self,
        unit_id: str,
        name: str,
        value: float | None = None,
        props: dict[str, Any] | None = None,
    ) -> None:
        assert_pseudonymous_unit(unit_id)
        properties = props or {}
        assert_no_pii(properties)
        event: dict[str, Any] = {"unit_id": unit_id, "name": name, "props": properties}
        if value is not None:
            event["value"] = value
        self._queue.append({"event": event})
        self._maybe_flush()

    def _maybe_flush(self) -> None:
        if len(self._queue) >= self._flush_at:
            self.flush()

    def flush(self) -> None:
        """Best-effort send of queued events/exposures. Never raises into the host app."""
        if not self._queue:
            return
        payload = json.dumps(
            {
                "events": [q["event"] for q in self._queue if "event" in q],
                "exposures": [q["exposure"] for q in self._queue if "exposure" in q],
            }
        ).encode()
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        request = urllib.request.Request(
            f"{self._base_url}/v1/events", data=payload, headers=headers, method="POST"
        )
        try:
            urllib.request.urlopen(request, timeout=2)  # noqa: S310
            self._queue.clear()
        except (urllib.error.URLError, OSError):
            return  # keep the queue; retry on the next flush
