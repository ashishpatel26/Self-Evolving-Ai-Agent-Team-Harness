'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { MailCheck, ShieldAlert, ShieldCheck, TriangleAlert } from 'lucide-react';
import { ScoreRing, TagPill } from './ui';
import Markdown from './Markdown';

function Shield({ detail }) {
  return (
    <motion.div className="guardrail" initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }}>
      <div className="shield-wrap">
        <motion.span className="shield-wave" animate={{ scale: [1, 1.9], opacity: [0.6, 0] }} transition={{ duration: 1.6, repeat: Infinity }} />
        <motion.span
          className="shield-wave"
          animate={{ scale: [1, 1.9], opacity: [0.6, 0] }}
          transition={{ duration: 1.6, repeat: Infinity, delay: 0.8 }}
        />
        <motion.div className="shield" initial={{ rotate: -20, scale: 0.4 }} animate={{ rotate: 0, scale: 1 }} transition={{ type: 'spring', stiffness: 300, damping: 14 }}>
          <ShieldAlert size={26} />
        </motion.div>
      </div>
      <div>
        <div className="guardrail-title">Guardrail engaged — prompt injection blocked</div>
        <div className="guardrail-sub">{detail}. No model was called; the customer receives a safe refusal.</div>
      </div>
    </motion.div>
  );
}

export default function ReplyCard({ run }) {
  if (!run) return null;
  const { reply, scored, guardrail, error } = run;
  return (
    <AnimatePresence>
      {(reply || error || guardrail) && (
        <motion.section
          className="card reply-card"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 260, damping: 28 }}
        >
          {guardrail && <Shield detail={guardrail} />}
          {error && (
            <div className="alert alert-err">
              <TriangleAlert size={15} /> {error}
            </div>
          )}
          {reply && (
            <div className="reply-grid">
              <div className="reply-main">
                <div className="card-head">
                  <div className="card-title">
                    <MailCheck size={15} /> Final reply
                  </div>
                  {reply.category && <span className={`cat-pill cat-${reply.category}`}>{reply.category}</span>}
                </div>
                {reply.issues?.length > 0 && (
                  <ul className="issues">
                    {reply.issues.map((iss, i) => (
                      <motion.li key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 * i }}>
                        {typeof iss === 'string' ? iss : JSON.stringify(iss)}
                      </motion.li>
                    ))}
                  </ul>
                )}
                <Markdown className="reply-text">{reply.reply}</Markdown>
              </div>
              {scored && (
                <motion.div className="reply-score" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
                  <ScoreRing score={scored.score} size={96} label="score" />
                  <div className="muted small">vs. benchmark {scored.sample}</div>
                  <div className="tags">
                    {scored.failures?.length ? (
                      scored.failures.map((f, i) => (
                        <div key={i} className="fail-row" title={f.detail}>
                          <TagPill tag={f.tag} />
                          <span className="muted small">{f.detail}</span>
                        </div>
                      ))
                    ) : (
                      <span className="ok-line">
                        <ShieldCheck size={14} /> No failure tags
                      </span>
                    )}
                  </div>
                </motion.div>
              )}
            </div>
          )}
        </motion.section>
      )}
    </AnimatePresence>
  );
}
