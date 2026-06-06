"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { useQuery } from "@tanstack/react-query";

import { ResultsTable } from "@/components/results-table";
import { SrmBanner } from "@/components/srm-banner";
import { Badge, Card } from "@/components/ui";
import { getExperiment, getResults } from "@/lib/api";

export default function ExperimentDetail() {
  const params = useParams<{ key: string }>();
  const key = params.key;
  const experiment = useQuery({
    queryKey: ["experiment", key],
    queryFn: () => getExperiment(key),
    retry: false,
  });
  const results = useQuery({
    queryKey: ["results", key],
    queryFn: () => getResults(key),
    retry: false,
  });

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 p-8">
      <Link href="/" className="text-sm text-primary underline">
        ← Experiments
      </Link>

      {experiment.data ? (
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{experiment.data.name}</h1>
            <Badge>{experiment.data.status}</Badge>
          </div>
          <p className="text-sm text-muted-foreground">{experiment.data.hypothesis}</p>
        </div>
      ) : experiment.isError ? (
        <Card>
          <p className="text-sm">Could not load this experiment.</p>
        </Card>
      ) : (
        <p className="text-sm text-muted-foreground">Loading…</p>
      )}

      {experiment.data ? (
        <Card>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Variants
          </h2>
          <ul className="text-sm">
            {experiment.data.variants.map((v) => (
              <li key={v.id}>
                {v.key}
                {v.is_control ? " (control)" : ""} — {v.allocation_pct}%
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Results
        </h2>
        {results.data ? (
          <>
            <SrmBanner srm={results.data.srm} />
            <Card>
              <ResultsTable results={results.data.results} />
            </Card>
          </>
        ) : results.isError ? (
          <Card>
            <p className="text-sm text-muted-foreground">
              No analysis has been run yet. POST to{" "}
              <code className="rounded bg-muted px-1">/v1/experiments/{key}/analyze</code> to
              compute results.
            </p>
          </Card>
        ) : (
          <p className="text-sm text-muted-foreground">Loading…</p>
        )}
      </section>
    </main>
  );
}
