import { cn } from "@/lib/utils";

export type HealthState = "ok" | "loading" | "error";

/** Presentational status pill for the API health check. */
export function HealthBadge({ state }: { state: HealthState }) {
  const label =
    state === "ok" ? "API healthy" : state === "loading" ? "Checking…" : "API unreachable";
  return (
    <span
      role="status"
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium",
        state === "ok" && "bg-muted text-foreground",
        state === "loading" && "bg-muted text-muted-foreground",
        state === "error" && "bg-destructive text-destructive-foreground",
      )}
    >
      <span
        className={cn(
          "h-2 w-2 rounded-full",
          state === "ok" && "bg-green-500",
          state === "loading" && "bg-yellow-500",
          state === "error" && "bg-red-500",
        )}
      />
      {label}
    </span>
  );
}
