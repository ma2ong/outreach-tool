import type { Lead, Stats, SendJob } from "./types";

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

export async function startEmailSend(body: { lead_nos: number[]; subject: string; body: string }): Promise<{ job_id: string; eligible: number; selected: number }> {
  const r = await fetch("/api/send/email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`send ${r.status}`);
  return r.json();
}

export async function fetchJob(id: string): Promise<SendJob> {
  const r = await fetch(`/api/send/jobs/${id}`);
  if (!r.ok) throw new Error(`job ${r.status}`);
  return r.json();
}
