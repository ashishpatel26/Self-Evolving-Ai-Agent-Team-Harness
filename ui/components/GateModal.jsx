'use client';

import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Check, Loader2, UserCheck, X } from 'lucide-react';
import { useConsole } from '@/lib/store';
import { api } from '@/lib/api';
import { capMeta, roleNames } from '@/lib/format';
import { TeamGraph } from './ui';

export default function GateModal({ onOpenEvolution }) {
  const { ui, dispatch, refresh } = useConsole();
  const proposal = ui.gate;
  const [rationale, setRationale] = useState('');
  const [busy, setBusy] = useState(null);
  const [err, setErr] = useState(null);
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    setRationale(proposal?.rationale || '');
    setErr(null);
    setHidden(false);
  }, [proposal]);

  const base = ui.evo.launch?.design;
  const added = proposal && base ? new Set([...roleNames(proposal)].filter((n) => !roleNames(base).has(n))) : new Set();

  const decide = async (decision) => {
    setBusy(decision);
    setErr(null);
    try {
      const edited = rationale.trim() !== (proposal?.rationale || '').trim() ? rationale.trim() : '';
      await api.gate(decision, edited);
      dispatch({ type: 'clearGate' });
      refresh();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <AnimatePresence>
      {proposal && !hidden && (
        <motion.div className="modal-scrim" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <motion.div
            className="modal"
            role="dialog"
            aria-modal="true"
            initial={{ opacity: 0, y: 30, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 300, damping: 28 }}
          >
            <div className="modal-head">
              <div className="gate-icon">
                <UserCheck size={18} />
              </div>
              <div>
                <div className="modal-title">Human gate · approve team v{proposal.version}?</div>
                <div className="muted small">The supervisor proposes a new team design. Nothing launches until you decide.</div>
              </div>
              <button className="icon-btn" onClick={() => setHidden(true)} aria-label="Hide">
                <X size={16} />
              </button>
            </div>

            <div className="modal-body">
              <div className="gate-graph">
                <TeamGraph design={proposal} added={added} />
              </div>
              {added.size > 0 && (
                <div className="badges">
                  {[...added].map((n) => (
                    <motion.span key={n} className="add-badge" initial={{ scale: 0 }} animate={{ scale: 1 }}>
                      + {n}
                    </motion.span>
                  ))}
                </div>
              )}
              <div className="gate-roles">
                {proposal.roles?.map((r) => (
                  <div key={r.name} className={`gate-role ${added.has(r.name) ? 'is-new' : ''}`}>
                    <div className="gate-role-name">
                      {r.name}
                      {added.has(r.name) && <span className="new-tag">new</span>}
                    </div>
                    <div className="muted small">{r.mandate}</div>
                    <div className="role-caps">
                      {r.tools?.map((c) => {
                        const m = capMeta(c);
                        return (
                          <span key={c} className={`cap tone-${m.tone}`}>
                            <m.Icon size={10} /> {m.label}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
              <label className="field-label">Rationale (editable)</label>
              <textarea value={rationale} onChange={(e) => setRationale(e.target.value)} rows={4} />
              {err && <div className="alert alert-err">{err}</div>}
            </div>

            <div className="modal-foot">
              <button className="btn btn-ghost" onClick={() => { setHidden(true); onOpenEvolution?.(); }}>
                Review in Evolution
              </button>
              <div className="spacer" />
              <button className="btn btn-danger" disabled={!!busy} onClick={() => decide('reject')}>
                {busy === 'reject' ? <Loader2 size={15} className="spin" /> : <X size={15} />} Reject
              </button>
              <button className="btn btn-primary" disabled={!!busy} onClick={() => decide('approve')}>
                {busy === 'approve' ? <Loader2 size={15} className="spin" /> : <Check size={15} />} Approve & launch
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
      {proposal && hidden && (
        <motion.button className="gate-fab" initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 40, opacity: 0 }} onClick={() => setHidden(false)}>
          <span className="dot dot-warn" /> Proposal v{proposal.version} awaiting approval
        </motion.button>
      )}
    </AnimatePresence>
  );
}
