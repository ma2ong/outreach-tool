import type { Lead, Stats } from "./types";

export async function fetchLeads(params: Record<string, string> = {}): Promise<Lead[]> {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
  const r = await fetch(`/api/leads${qs ? "?" + qs : ""}`);
  if (!r.ok) throw new Error(`leads ${r.status}`);
  return r.json();
}

export async function fetchStats(): Promise<Stats> {
  const r = await fetch("/api/stats");
  if (!r.ok) throw new Error(`stats ${r.status}`);
  return r.json();
}
