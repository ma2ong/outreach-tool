export interface OutreachStatus {
  channel: string;
  status: string;
  touch_count: number;
  message_sent_date: string | null;
  reply_received: boolean;
  exclude_reason: string | null;
}
export interface Lead {
  no: number;
  company_en: string;
  country: string | null;
  city: string | null;
  email: string | null;
  phone: string | null;
  website: string | null;
  instagram: string | null;
  facebook: string | null;
  linkedin: string | null;
  whatsapp_verified: boolean;
  business: string | null;
  outreach: OutreachStatus[];
}
export interface ChannelReach {
  have: number;
  messaged: number;
  replied: number;
  untouched: number;
}
export interface Stats {
  total: number;
  by_country: Record<string, number>;
  by_channel_status: Record<string, Record<string, number>>;
  reach: Record<string, ChannelReach>;
  funnel: { total: number; with_contact: number; touched: number; replied: number };
}
export interface SendJob {
  id: string;
  status: string;
  done: number;
  total: number;
  result:
    | { sent: number; failed: number; skipped: number; deferred?: number; errors: { no: number; error: string }[] }
    | { error: string }
    | null;
}
export interface Candidate {
  domain: string;
  title: string;
  email: string | null;
  emails: string[];
  phone: string | null;
  instagram: string | null;
  facebook: string | null;
  linkedin: string | null;
  duplicate_of: number | null;
}
export interface DiscoverJob {
  id: string;
  status: string;
  done: number;
  total: number;
  result: { candidates: Candidate[] } | { error: string } | null;
}
