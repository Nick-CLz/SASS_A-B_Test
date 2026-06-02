"use client";

import { useQuery } from "@tanstack/react-query";

import { HealthBadge, type HealthState } from "@/components/health-badge";
import { getHealth } from "@/lib/api";

export default function Home() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: false,
  });

  const state: HealthState = isLoading ? "loading" : isError ? "error" : "ok";

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 p-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Mallard</h1>
        <p className="text-muted-foreground">
          AI-native, privacy-first A/B testing platform.
        </p>
      </div>
      <div className="flex items-center gap-3">
        <HealthBadge state={state} />
        {data ? (
          <span className="text-sm text-muted-foreground">v{data.version}</span>
        ) : null}
      </div>
      <p className="text-sm text-muted-foreground">
        Scaffold (P01). The dashboard is built in P10 — see{" "}
        <code className="rounded bg-muted px-1 py-0.5">prompts/P10-dashboard.md</code>.
      </p>
    </main>
  );
}
