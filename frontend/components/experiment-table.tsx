import Link from "next/link";

import type { Experiment } from "@/lib/types";

import { Badge } from "@/components/ui";

type Tone = "muted" | "green" | "red" | "amber";

function statusTone(status: string): Tone {
  if (status === "running") return "green";
  if (status === "concluded") return "amber";
  if (status === "archived") return "red";
  return "muted";
}

export function ExperimentTable({ experiments }: { experiments: Experiment[] }) {
  if (experiments.length === 0) {
    return <p className="text-sm text-muted-foreground">No experiments yet.</p>;
  }
  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
          <th className="py-2 pr-3">Key</th>
          <th className="py-2 pr-3">Name</th>
          <th className="py-2 pr-3">Status</th>
          <th className="py-2 pr-3">Variants</th>
          <th className="py-2 pr-3">Metrics</th>
        </tr>
      </thead>
      <tbody>
        {experiments.map((exp) => (
          <tr key={exp.id} className="border-b border-border">
            <td className="py-2 pr-3">
              <Link href={`/experiments/${exp.key}`} className="font-medium text-primary underline">
                {exp.key}
              </Link>
            </td>
            <td className="py-2 pr-3">{exp.name}</td>
            <td className="py-2 pr-3">
              <Badge tone={statusTone(exp.status)}>{exp.status}</Badge>
            </td>
            <td className="py-2 pr-3">{exp.variants.length}</td>
            <td className="py-2 pr-3">{exp.metrics.length}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
