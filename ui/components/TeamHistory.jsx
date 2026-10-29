'use client';

import { motion } from 'framer-motion';
import { Coins, TrendingDown, TrendingUp, GitCommitHorizontal } from 'lucide-react';
import { useConsole } from '@/lib/store';
import { fmtNum, pct, roleNames, scoreTone } from '@/lib/format';
import ScoreChart from './ScoreChart';
import { AnimatedNumber, Stat, TagPill, TeamGraph } from './ui';

function tagCounts(failures = []) {
  const c = {};
  failures.forEach((f) => (c[f.tag] = (c[f.tag] || 0) + 1));
  return Object.entries(c).sort((a, b) => b[1] - a[1]);
}

export default function TeamHistory() {
  const { server } = useConsole();
  const hist = [...(server?.history || [])].sort((a, b) => a.version - b.version);
  const points = hist.map((h) => ({ version: h.version, score: h.score, accuracy: h.evals?.accuracy ?? null }));
  const best = hist.reduce((m, h) => (h.score > (m?.score ?? -1) ? h : m), null);
  const first = hist[0];
  const last = hist[hist.length - 1];
  const delta = first && last ? last.score - first.score : 0;

  return (
    <div className="history">
      <div className="stats-row">
        <section className="card">
          <Stat label="Versions">{hist.length}</Stat>
        </section>
        <section className="card">
          <Stat label="Best score" sub={best ? `team v${best.version}` : ''}>
            <span className="grad-text">{best ? <AnimatedNumber value={best.score * 100} format={(v) => `${v.toFixed(0)}%`} /> : '—'}</span>
          </Stat>
        </section>
        <section className="card">
          <Stat label="Improvement" sub={first ? `v${first.version} → v${last.version}` : ''}>
            <span className={delta >= 0 ? 'ok-text' : 'err-text'}>
              {delta >= 0 ? <TrendingUp size={18} /> : <TrendingDown size={18} />}{' '}
              <AnimatedNumber value={delta * 100} format={(v) => `${v >= 0 ? '+' : ''}${v.toFixed(0)} pts`} />
            </span>
          </Stat>
        </section>
        <section className="card">
          <Stat label="Current team" sub={server?.current?.coordination}>
            v{server?.current?.version ?? '—'}
          </Stat>
        </section>
      </div>

      <section className="card">
        <div className="card-head">
          <div className="card-title">Score over versions</div>
          <div className="legend small muted">
            <span className="lg lg-score" /> harness score <span className="lg lg-acc" /> eval accuracy
          </div>
        </div>
        <ScoreChart points={points} />
      </section>

      <section className="card">
        <div className="card-head">
          <div className="card-title">
            <GitCommitHorizontal size={15} /> Team lineage
          </div>
          <span className="muted small">{hist.length} versions</span>
        </div>
        {!hist.length && <div className="muted small panel-empty">Run an evolution to build a lineage.</div>}
        <div className="lineage">
          {hist.map((h, i) => {
            const prev = hist[i - 1];
            const added = prev ? new Set([...roleNames(h.design)].filter((n) => !roleNames(prev.design).has(n))) : new Set();
            return (
              <motion.div
                key={h.version}
                className="lin-item"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
              >
                {i > 0 && <div className="lin-link" aria-hidden />}
                <div className={`card lin-card ${h.version === server?.current?.version ? 'lin-current' : ''}`}>
                  <div className="lin-head">
                    <span className="lin-ver">v{h.version}</span>
                    <span className={`score-badge sb-${scoreTone(h.score)}`}>{pct(h.score)}</span>
                  </div>
                  <div className="lin-meta small muted">
                    <span>{h.coordination}</span>
                    <span>
                      <Coins size={11} /> {fmtNum(h.tokens)}
                    </span>
                  </div>
                  {added.size > 0 && (
                    <div className="badges">
                      {[...added].map((n) => (
                        <span key={n} className="add-badge">
                          + {n}
                        </span>
                      ))}
                    </div>
                  )}
                  <TeamGraph design={h.design} added={added} small />
                  {h.evals ? (
                    <div className="evals">
                      <div>
                        <small>accuracy</small>
                        <b>{pct(h.evals.accuracy)}</b>
                      </div>
                      <div>
                        <small>judge</small>
                        <b>{h.evals.judge_avg == null ? '—' : h.evals.judge_avg <= 1 ? pct(h.evals.judge_avg) : Number(h.evals.judge_avg).toFixed(1)}</b>
                      </div>
                      <div>
                        <small>reliability</small>
                        <b>{pct(h.evals.reliability)}</b>
                      </div>
                    </div>
                  ) : (
                    <div className="muted small">evals pending</div>
                  )}
                  <div className="tags">
                    {tagCounts(h.failures).map(([t, c]) => (
                      <TagPill key={t} tag={t} count={c} />
                    ))}
                    {!h.failures?.length && <span className="ok-line small">no failures</span>}
                  </div>
                  {h.design?.rationale && <p className="lin-why">{h.design.rationale}</p>}
                </div>
              </motion.div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
