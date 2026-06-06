"use client";

import { useQuery } from "@tanstack/react-query";

import { ExperimentTable } from "@/components/experiment-table";
import { HealthBadge, type HealthState } from "@/components/health-badge";
import { Card } from "@/components/ui";
import { API_BASE_URL, getHealth, listExperiments, WORKSPACE_ID } from "@/lib/api";

export default function Home() {
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth, retry: false });
  const experiments = useQuery({
    queryKey: ["experiments"],
    queryFn: listExperiments,
    retry: false,
    enabled: Boolean(WORKSPACE_ID),
  });
  const state: HealthState = health.isLoading ? "loading" : health.isError ? "error" : "ok";

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 p-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Mallard</h1>
          <p className="text-sm text-muted-foreground">Experiments</p>
        </div>
        <div className="flex items-center gap-2">
          <HealthBadge state={state} />
          {health.data ? (
            <span className="text-xs text-muted-foreground">v{health.data.version}</span>
          ) : null}
        </div>
      </header>

      {!WORKSPACE_ID ? (
        <Card>
          <p className="text-sm">
            Set <code className="rounded bg-muted px-1">NEXT_PUBLIC_WORKSPACE_ID</code> to a
            workspace id to load experiments from the API.
          </p>
        </Card>
      ) : experiments.isError ? (
        <Card>
          <p className="text-sm">
            Could not load experiments from{" "}
            <code className="rounded bg-muted px-1">{API_BASE_URL}</code>. Make sure the API is
            running.
          </p>
        </Card>
      ) : (
        <Card>
          {experiments.data ? (
            <ExperimentTable experiments={experiments.data} />
          ) : (
            <p className="text-sm text-muted-foreground">Loading…</p>
          )}
        </Card>
      )}
    </main>
  );
}
