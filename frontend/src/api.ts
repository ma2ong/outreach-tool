import type { Lead, Stats, SendJob, DiscoverJob } from "./types";

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

export async function startDiscover(query: string, limit = 10): Promise<{ job_id: string }> {
  const r = await fetch("/api/discover", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
  });
  if (!r.ok) throw new Error(`discover ${r.status}`);
  return r.json();
}

export async function fetchDiscoverJob(id: string): Promise<DiscoverJob> {
  const r = await fetch(`/api/discover/jobs/${id}`);
  if (!r.ok) throw new Error(`discover job ${r.status}`);
  return r.json();
}

export async function importLeads(country: string, candidates: { company_en: string; website: string; email: string | null }[]): Promise<{ imported: number }> {
  const r = await fetch("/api/leads/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ country, candidates }),
  });
  if (!r.ok) throw new Error(`import ${r.status}`);
  return r.json();
}

export async function startChannelSend(channel: string, lead_nos: number[], message: string): Promise<{ job_id: string; eligible: number; selected: number }> {
  const r = await fetch("/api/send/channel", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ channel, lead_nos, message }),
  });
  if (!r.ok) throw new Error(`send ${r.status}`);
  return r.json();
}

export async function fetchChannels(): Promise<Record<string, string>> {
  const r = await fetch("/api/channels");
  if (!r.ok) throw new Error(`channels ${r.status}`);
  return r.json();
}

export async function connectChannel(ch: string): Promise<void> {
  const r = await fetch(`/api/channels/${ch}/connect`, { method: "POST" });
  if (!r.ok) throw new Error(`connect ${r.status}`);
}

export async function channelStatus(ch: string): Promise<string> {
  const r = await fetch(`/api/channels/${ch}/status`);
  if (!r.ok) throw new Error(`status ${r.status}`);
  return (await r.json()).status;
}
