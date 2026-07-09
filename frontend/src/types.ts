export interface OutreachStatus {
  channel: string;
  status: string;
  touch_count: number;
  message_sent_date: string | null;
  reply_received: boolean;
  exclude_reason: string | null;
}
export interface Note {
  id: number;
  created_at: string | null;
  text: string;
}
export interface Lead {
  no: number;
  company_en: string;
  company_local: string | null;
  country: string | null;
  region: string | null;
  city: string | null;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  website: string | null;
  instagram: string | null;
  facebook: string | null;
  linkedin: string | null;
  whatsapp_verified: boolean;
  business: string | null;
  stage: string;
  tags: string | null;
  follow_up_date: string | null;
  next_action: string | null;
  outreach: OutreachStatus[];
  notes: Note[];
}
export interface Template {
  id: number;
  name: string;
  channel: string;
  subject: string | null;
  body: string;
}
export interface SequenceStep {
  step_order: number;
  day_offset: number;
  subject: string | null;
  body: string;
  image: string | null;
}
export interface Sequence {
  id: number;
  name: string;
  channel: string;
  active: boolean;
  steps: SequenceStep[];
  enrolled: number;
}
export interface DueItem {
  enrollment_id: number;
  lead_no: number;
  company_en: string;
  channel: string;
  sequence_id: number;
  sequence_name: string;
  step_order: number;
  subject: string | null;
  body: string;
  image: string | null;
}
export const STAGES = ["new", "contacted", "replied", "negotiating", "won", "lost"] as const;
export const STAGE_LABEL: Record<string, string> = {
  new: "新客户", contacted: "已联系", replied: "已回复",
  negotiating: "洽谈中", won: "成交", lost: "无效",
};
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
  funnel: { total: number; with_contact: number; touched: number; replied: number; follow_up_due: number };
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
