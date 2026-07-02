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
  business: string | null;
  outreach: OutreachStatus[];
}
export interface Stats {
  total: number;
  by_country: Record<string, number>;
  by_channel_status: Record<string, Record<string, number>>;
}
