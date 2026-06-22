// Mallard client: local assignment + batched, resilient event tracking.
// Mirrors sdks/python/mallard_sdk/client.py (see docs/06-api-and-sdk.md §SDK):
// - assignment is computed locally (same hashing as the server) — no network on the hot path;
// - track() batches and never throws into the host app, even when the service is unreachable;
// - privacy guards reject obvious PII client-side.

import { assign } from "./engine";
import { assertNoPii, assertPseudonymousUnit } from "./privacy";
import type { Assignment, Attributes, ExperimentSpec } from "./types";

export interface MallardOptions {
  apiKey?: string;
  baseUrl?: string;
  flushAt?: number;
}

interface Queued {
  event?: Record<string, unknown>;
  exposure?: Record<string, unknown>;
}

export class Mallard {
  private readonly apiKey?: string;
  private readonly baseUrl: string;
  private readonly flushAt: number;
  private specs = new Map<string, ExperimentSpec>();
  private queue: Queued[] = [];

  constructor(options: MallardOptions = {}) {
    this.apiKey = options.apiKey;
    this.baseUrl = (options.baseUrl ?? "http://localhost:8000").replace(/\/+$/, "");
    this.flushAt = options.flushAt ?? 20;
  }

  /** Load experiment configs for local assignment. */
  loadSpecs(specs: ExperimentSpec[]): void {
    this.specs = new Map(specs.map((spec) => [spec.key, spec]));
  }

  getVariant(
    experimentKey: string,
    unitId: string,
    attributes: Attributes = {},
    options: { logExposure?: boolean } = {},
  ): Assignment {
    assertPseudonymousUnit(unitId);
    const spec = this.specs.get(experimentKey);
    if (!spec) {
      return {
        experimentKey,
        eligible: false,
        inExperiment: false,
        variantKey: null,
        reason: "unknown_experiment",
      };
    }
    const result = assign(spec, unitId, attributes);
    const logExposure = options.logExposure ?? true;
    if (logExposure && result.inExperiment && result.variantKey !== null) {
      this.queue.push({
        exposure: {
          experiment_key: result.experimentKey,
          variant_key: result.variantKey,
          unit_id: unitId,
        },
      });
      this.maybeFlush();
    }
    return result;
  }

  /** Assign without logging an exposure (for triggered analysis). */
  peekVariant(experimentKey: string, unitId: string, attributes: Attributes = {}): Assignment {
    return this.getVariant(experimentKey, unitId, attributes, { logExposure: false });
  }

  track(unitId: string, name: string, value?: number, props: Attributes = {}): void {
    assertPseudonymousUnit(unitId);
    assertNoPii(props);
    const event: Record<string, unknown> = { unit_id: unitId, name, props };
    if (value !== undefined) {
      event.value = value;
    }
    this.queue.push({ event });
    this.maybeFlush();
  }

  /** Number of queued (un-flushed) items — for tests/observability. */
  get pending(): number {
    return this.queue.length;
  }

  private maybeFlush(): void {
    if (this.queue.length >= this.flushAt) {
      void this.flush();
    }
  }

  /** Best-effort send of queued events/exposures. Never throws into the host app. */
  async flush(): Promise<void> {
    if (this.queue.length === 0) {
      return;
    }
    const batch = this.queue;
    const payload = {
      events: batch.filter((q) => q.event).map((q) => q.event),
      exposures: batch.filter((q) => q.exposure).map((q) => q.exposure),
    };
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (this.apiKey) {
      headers.Authorization = `Bearer ${this.apiKey}`;
    }
    try {
      const res = await fetch(`${this.baseUrl}/v1/events`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        this.queue = [];
      }
    } catch {
      // keep the queue; retry on the next flush — never throw into the host app
    }
  }
}
