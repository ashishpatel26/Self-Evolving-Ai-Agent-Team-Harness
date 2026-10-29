import { BookOpen, Package, Brain, Wrench } from 'lucide-react';

const TOOLS = {
  search_knowledge_base: { label: 'Knowledge search', Icon: BookOpen, tone: 'violet' },
  lookup_order: { label: 'Order lookup (MCP)', Icon: Package, tone: 'cyan' },
  think: { label: 'Reasoning · think', Icon: Brain, tone: 'pink' },
  analyze: { label: 'Reasoning · analyze', Icon: Brain, tone: 'pink' },
};

const CAPS = {
  knowledge: { label: 'Knowledge', Icon: BookOpen, tone: 'violet' },
  orders: { label: 'Orders', Icon: Package, tone: 'cyan' },
  reasoning: { label: 'Reasoning', Icon: Brain, tone: 'pink' },
};

export const toolMeta = (t) => TOOLS[t] || { label: t, Icon: Wrench, tone: 'slate' };
export const capMeta = (c) => CAPS[c] || { label: c, Icon: Wrench, tone: 'slate' };

export const TAGS = {
  wrong_category: 'Wrong category',
  missing_policy_facts: 'Missing policy facts',
  missing_order_facts: 'Missing order facts',
  blocked_wrongly: 'Blocked wrongly',
  run_error: 'Run error',
};
export const tagLabel = (t) => TAGS[t] || t;

export const pct = (v, d = 0) => (v == null || Number.isNaN(v) ? '—' : `${(v * 100).toFixed(d)}%`);
export const fmtNum = (n) => (n == null ? '—' : Number(n).toLocaleString());

export function scoreTone(s) {
  if (s == null) return 'muted';
  if (s >= 0.8) return 'ok';
  if (s >= 0.5) return 'warn';
  return 'err';
}

export function initials(name = '') {
  const parts = name.replace(/[_-]/g, ' ').split(/\s+/).filter(Boolean);
  return (parts.length > 1 ? parts[0][0] + parts[1][0] : name.slice(0, 2)).toUpperCase();
}

export function preview(v, n = 140) {
  if (v == null) return '';
  const s = typeof v === 'string' ? v : JSON.stringify(v);
  return s.length > n ? s.slice(0, n) + '…' : s;
}

export function pretty(v) {
  if (typeof v === 'string') {
    try {
      return JSON.stringify(JSON.parse(v), null, 2);
    } catch {
      return v;
    }
  }
  return JSON.stringify(v, null, 2);
}

export function timeAgo(ts) {
  if (!ts) return '';
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function roleNames(design) {
  return new Set((design?.roles || []).map((r) => r.name));
}
