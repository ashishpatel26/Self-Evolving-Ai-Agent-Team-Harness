'use client';

import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronRight, Flag, Layers, Loader2, Play, ShieldAlert, Sparkles, TriangleAlert, Check, X } from 'lucide-react';
import { pct, pretty, preview, timeAgo, toolMeta } from '@/lib/format';
import Markdown from './Markdown';

function Row({ icon: Icon, tone = 'slate', title, sub, right, children, ts }) {
  const [open, setOpen] = useState(false);
  return (
    <motion.li
      layout
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ type: 'spring', stiffness: 420, damping: 32 }}
      className="feed-row"
    >
      <div className={`feed-icon tone-${tone}`}>
        <Icon size={13} />
      </div>
      <div className="feed-body">
        <button className="feed-line" onClick={() => children && setOpen(!open)} disabled={!children}>
          <span className="feed-title">{title}</span>
          {right}
          {children && <ChevronRight size={13} className={`chev ${open ? 'open' : ''}`} />}
        </button>
        {sub && <div className="feed-sub">{sub}</div>}
        <AnimatePresence>
          {open && children && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="feed-detail">
              {children}
            </motion.div>
          )}
        </AnimatePresence>
        <div className="feed-ts">{timeAgo(ts)}</div>
      </div>
    </motion.li>
  );
}

function Item({ ev }) {
  switch (ev.kind) {
    case 'ticket_start':
      return <Row icon={Play} tone="violet" ts={ev.ts} title={`Ticket ${ev.ticket} received`} sub={`team v${ev.version} · ${ev.stages?.length || 0} stages`} />;
    case 'stage_start':
      return <Row icon={Layers} tone="cyan" ts={ev.ts} title={`Stage ${ev.stage + 1} started`} sub={ev.roles?.join(' ∥ ')} />;
    case 'tool_start': {
      const m = toolMeta(ev.tool);
      const st = ev.status;
      return (
        <Row
          icon={m.Icon}
          tone={m.tone}
          ts={ev.ts}
          title={m.label}
          sub={
            <>
              <span className="role-ref">{ev.role}</span> <span className="mono">{preview(ev.args, 90)}</span>
            </>
          }
          right={
            <span className={`mini-st st-${st}`}>
              {st === 'running' ? <Loader2 size={11} className="spin" /> : st === 'error' ? <X size={11} /> : <Check size={11} />}
            </span>
          }
        >
          <div className="kv">
            <div className="kv-k">args</div>
            <pre>{pretty(ev.args || {})}</pre>
            {ev.result != null && (
              <>
                <div className="kv-k">result</div>
                <pre>{pretty(ev.result)}</pre>
              </>
            )}
          </div>
        </Row>
      );
    }
    case 'stage_end':
      return (
        <Row
          icon={ev.ok ? Check : X}
          tone={ev.ok ? 'ok' : 'err'}
          ts={ev.ts}
          title={`Stage ${ev.stage + 1} ${ev.ok ? 'handed off' : 'failed'}`}
          sub={`${ev.roles?.join(', ')} · ${ev.tokens ?? 0} tok · ${preview(ev.output, 80)}`}
        >
          {typeof ev.output === 'string' ? <Markdown className="md-sm">{ev.output}</Markdown> : <pre>{pretty(ev.output)}</pre>}
        </Row>
      );
    case 'guardrail':
      return <Row icon={ShieldAlert} tone="err" ts={ev.ts} title="Guardrail blocked the ticket" sub={ev.detail} />;
    case 'ticket_end':
      return <Row icon={Flag} tone="ok" ts={ev.ts} title={`Reply ready · ${ev.reply?.category || '—'}`} sub={preview(ev.reply?.reply, 100)} />;
    case 'ticket_error':
      return <Row icon={TriangleAlert} tone="err" ts={ev.ts} title="Run error" sub={ev.error} />;
    case 'live_scored':
      return <Row icon={Sparkles} tone="violet" ts={ev.ts} title={`Scored against ${ev.sample}: ${pct(ev.score)}`} sub={`${ev.failures?.length || 0} failure tags`} />;
    default:
      return null;
  }
}

export default function ActivityFeed({ items }) {
  if (!items.length)
    return (
      <div className="empty">
        <div className="empty-orb" />
        <p>Submit a ticket to watch the team work.</p>
        <small>Tool calls, hand-offs and stage outputs stream here in real time.</small>
      </div>
    );
  return (
    <ul className="feed">
      <AnimatePresence initial={false}>
        {[...items].reverse().map((ev) => (
          <Item key={ev.id} ev={ev} />
        ))}
      </AnimatePresence>
    </ul>
  );
}
