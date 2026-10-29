'use client';

import { Fragment } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Check, Inbox, Loader2, MessageSquareReply, ShieldAlert, X } from 'lucide-react';
import { capMeta, initials, toolMeta } from '@/lib/format';

function Edge({ state }) {
  return (
    <div className={`edge edge-${state}`} aria-hidden>
      <div className="edge-line" />
      {state === 'flowing' && (
        <>
          <span className="particle" style={{ animationDelay: '0s' }} />
          <span className="particle" style={{ animationDelay: '0.35s' }} />
          <span className="particle" style={{ animationDelay: '0.7s' }} />
        </>
      )}
      <div className="edge-head" />
    </div>
  );
}

function StatusIcon({ status }) {
  if (status === 'active') return <Loader2 size={13} className="spin" />;
  if (status === 'done') return <Check size={13} />;
  if (status === 'error') return <X size={13} />;
  return null;
}

function IoNode({ icon: Icon, label, sub, status }) {
  return (
    <motion.div layout className={`io-node io-${status}`}>
      <div className="io-icon">
        <Icon size={16} />
      </div>
      <div className="io-text">
        <div className="io-label">{label}</div>
        {sub && <div className="io-sub">{sub}</div>}
      </div>
    </motion.div>
  );
}

function ToolChip({ t }) {
  const m = toolMeta(t.tool);
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.6, y: -6 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 500, damping: 26 }}
      className={`tool-chip tone-${m.tone} st-${t.status}`}
      title={`${m.label}\n${JSON.stringify(t.args || {})}`}
    >
      <m.Icon size={11} />
      <span>{m.label}</span>
      {t.status === 'running' ? <Loader2 size={10} className="spin" /> : t.status === 'error' ? <X size={10} /> : <Check size={10} />}
    </motion.div>
  );
}

function RoleNode({ name, role, status, tools, compact }) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: status === 'skipped' ? 0.35 : 1, y: 0 }}
      className={`role-node rs-${status}`}
    >
      {status === 'active' && (
        <motion.span
          className="role-glow"
          animate={{ opacity: [0.35, 0.9, 0.35], scale: [1, 1.03, 1] }}
          transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
        />
      )}
      <div className="role-head">
        <div className="avatar">{initials(name)}</div>
        <div className="role-title">
          <div className="role-name">{name}</div>
          {!compact && role?.mandate && <div className="role-mandate">{role.mandate}</div>}
        </div>
        <span className={`role-status rs-badge-${status}`}>
          <StatusIcon status={status} />
        </span>
      </div>
      {!compact && role?.tools?.length > 0 && (
        <div className="role-caps">
          {role.tools.map((c) => {
            const m = capMeta(c);
            return (
              <span key={c} className={`cap tone-${m.tone}`}>
                <m.Icon size={10} /> {m.label}
              </span>
            );
          })}
        </div>
      )}
      <AnimatePresence initial={false}>
        {tools?.length > 0 && (
          <motion.div className="tool-chips" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}>
            {tools.slice(-6).map((t) => (
              <ToolChip key={t.id} t={t} />
            ))}
            {tools.length > 6 && <span className="tool-more">+{tools.length - 6}</span>}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function PipelineGraph({ design, run, compact = false }) {
  const stages = run?.stages?.length ? run.stages : design?.stages || [];
  const roles = Object.fromEntries((design?.roles || []).map((r) => [r.name, r]));
  const st = run?.stageStatus || [];
  const running = run?.status === 'running';
  const allDone = st.length > 0 && st.every((s) => s === 'done' || s === 'error' || s === 'skipped');

  const edgeInto = (i) => {
    if (!run) return 'idle';
    if (st[i] === 'active') return 'flowing';
    if (st[i] === 'done' || st[i] === 'error') return 'done';
    return 'idle';
  };
  const lastEdge = !run ? 'idle' : run.reply || run.status === 'error' ? 'done' : running && allDone ? 'flowing' : 'idle';
  const blocked = run?.status === 'blocked';

  return (
    <div className={`pipe ${compact ? 'pipe-compact' : ''}`}>
      <IoNode
        icon={blocked ? ShieldAlert : Inbox}
        label={blocked ? 'Blocked' : 'Ticket'}
        sub={run ? run.ticket : 'waiting'}
        status={blocked ? 'blocked' : run ? 'done' : 'idle'}
      />
      {stages.map((names, i) => (
        <Fragment key={i}>
          <Edge state={blocked ? 'idle' : edgeInto(i)} />
          <div className={`pipe-stage ss-${st[i] || 'pending'}`}>
            <div className="stage-label">
              <span>Stage {i + 1}</span>
              {names.length > 1 && <span className="stage-par">parallel ×{names.length}</span>}
            </div>
            <div className="stage-roles">
              {names.map((n) => (
                <RoleNode
                  key={n}
                  name={n}
                  role={roles[n]}
                  compact={compact}
                  status={run?.roleStatus?.[n] || (st[i] === 'skipped' ? 'skipped' : 'pending')}
                  tools={run?.tools?.[n]}
                />
              ))}
            </div>
          </div>
        </Fragment>
      ))}
      <Edge state={blocked ? 'idle' : lastEdge} />
      <IoNode
        icon={MessageSquareReply}
        label="Reply"
        sub={run?.reply ? run.reply.category : run?.status === 'error' ? 'error' : running ? 'drafting…' : 'pending'}
        status={run?.reply ? (blocked ? 'blocked' : 'done') : run?.status === 'error' ? 'error' : 'idle'}
      />
    </div>
  );
}
