// Thin client for the Mallard /v1 API.
// The workspace is selected via NEXT_PUBLIC_WORKSPACE_ID (sent as X-Workspace-Id);
// real auth replaces this in P15.

import type { AnalysisRun, Experiment } from "@/lib/types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export const WORKSPACE_ID = process.env.NEXT_PUBLIC_WORKSPACE_ID ?? "";

export interface Health {
  status: string;
  version: string;
}

function headers(): HeadersInit {
  return WORKSPACE_ID ? { "X-Workspace-Id": WORKSPACE_ID } : {};
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { headers: headers(), cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

export const getHealth = () => getJSON<Health>("/v1/health");
export const listExperiments = () => getJSON<Experiment[]>("/v1/experiments");
export const getExperiment = (key: string) => getJSON<Experiment>(`/v1/experiments/${key}`);
export const getResults = (key: string) => getJSON<AnalysisRun>(`/v1/experiments/${key}/results`);
