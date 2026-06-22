import type { MetricResult } from "@/lib/types";

import { Badge } from "@/components/ui";

function pct(x: number | null, digits = 2): string {
  return x == null ? "—" : `${(x * 100).toFixed(digits)}%`;
}

function signed(x: number | null, digits = 2): string {
  return x == null ? "—" : `${x >= 0 ? "+" : ""}${(x * 100).toFixed(digits)}%`;
}

/** Per-metric × per-variant results. Leads with the confidence interval, not the p-value. */
export function ResultsTable({ results }: { results: MetricResult[] }) {
  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
          <th className="py-2 pr-3">Metric</th>
          <th className="py-2 pr-3">Variant</th>
          <th className="py-2 pr-3">Rate (n)</th>
          <th className="py-2 pr-3">Effect (95% CI)</th>
          <th className="py-2 pr-3">Rel. lift</th>
          <th className="py-2 pr-3">P(better)</th>
          <th className="py-2 pr-3">Verdict</th>
        </tr>
      </thead>
      <tbody>
        {results.map((r, i) => (
          <tr key={`${r.metric_key}-${r.variant_key}-${i}`} className="border-b border-border">
            <td className="py-2 pr-3 font-medium">{r.metric_key}</td>
            <td className="py-2 pr-3">
              {r.variant_key}
              {r.is_control ? " (control)" : ""}
            </td>
            <td className="py-2 pr-3">
              {pct(r.estimate)} <span className="text-muted-foreground">n={r.n.toLocaleString()}</span>
            </td>
            <td className="py-2 pr-3">
              {r.is_control ? (
                "—"
              ) : (
                <span>
                  {signed(r.abs_effect)}{" "}
                  <span className="text-muted-foreground">
                    [{signed(r.ci_lower)}, {signed(r.ci_upper)}]
                  </span>
                </span>
              )}
            </td>
            <td className="py-2 pr-3">{r.is_control ? "—" : signed(r.rel_effect, 1)}</td>
            <td className="py-2 pr-3">
              {r.is_control || r.prob_to_beat_control == null
                ? "—"
                : pct(r.prob_to_beat_control, 0)}
            </td>
            <td className="py-2 pr-3">
              {r.is_control ? (
                <Badge>control</Badge>
              ) : r.is_significant ? (
                <Badge tone="green">significant</Badge>
              ) : (
                <Badge>not significant</Badge>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
