'use client';

import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Rocket, Gauge, LineChart, Lightbulb, Stethoscope, PenTool, UserCheck, CheckCircle2, Play, Loader2, RotateCw,
  TriangleAlert, Repeat,
} from 'lucide-react';
import { useConsole } from '@/lib/store';
import { api } from '@/lib/api';
import { pct, roleNames, scoreTone, tagLabel, timeAgo } from '@/lib/format';
import { AnimatedNumber, ScoreRing, TagPill, TeamGraph } from './ui';
import PipelineGraph from './PipelineGraph';

const STEPS = [
  { id: 'launch', label: 'Launch', Icon: Rocket },
  { id: 'score', label: 'Score', Icon: Gauge },
  { id: 'monitor', label: 'Monitor', Icon: LineChart },
  { id: 'reflect', label: 'Reflect', Icon: Lightbulb },
  { id: 'diagnose', label: 'Diagnose', Icon: Stethoscope },
  { id: 'redesign', label: 'Redesign', Icon: PenTool },
  { id: 'gate', label: 'Human gate', Icon: UserCheck },
  { id: 'adopt', label: 'Adopt', Icon: CheckCircle2 },
];

function Controls({ busy }) {
  const { dispatch, refresh } = useConsole();
  const [approve, setApprove] = useState('ui');
  const [iters, setIters] = useState(3);
  const [fresh, setFresh] = useState(true);
  const [err, setErr] = useState(null);
  const [starting, setStarting] = useState(false);

  const start = async () => {
    setErr(null);
    setStarting(true);
    try {
      await api.evolve({ approve, max_iterations: iters, fresh });
      dispatch({ type: 'evoStarting', approve, maxIter: iters });
      refresh();
    } catch (e) {
      setErr(e.message);
    } finally {
      setStarting(false);
    }
  };

  return (
    <section className="card controls">
      <div className="ctrl">
        <label>Approval</label>
        <div className="seg">
          {[
            ['ui', 'Human in UI'],
            ['auto', 'Auto'],
          ].map(([v, l]) => (
            <button key={v} className={approve === v ? 'on' : ''} onClick={() => setApprove(v)}>
              {approve === v && <motion.span layoutId="seg-on" className="seg-pill" />}
              <span>{l}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="ctrl">
        <label>
          Max iterations <b className="mono">{iters}</b>
        </label>
        <input type="range" min={1} max={8} value={iters} onChange={(e) => setIters(+e.target.value)} />
      </div>
      <div className="ctrl">
        <label>Fresh team from v1</label>
        <button className={`toggle ${fresh ? 'on' : ''}`} onClick={() => setFresh(!fresh)} aria-pressed={fresh}>
          <motion.span layout className="knob" transition={{ type: 'spring', stiffness: 600, damping: 32 }} />
        </button>
      </div>
      <button className="btn btn-primary ctrl-go" disabled={busy || starting} onClick={start}>
        {busy || starting ? <Loader2 size={15} className="spin" /> : <Play size={15} />}
        {busy ? 'Evolving…' : 'Start evolution'}
      </button>
      {err && <div className="alert alert-err full">{err}</div>}
    </section>
  );
}

function Cycle({ step, iteration, status }) {
  const idx = STEPS.findIndex((s) => s.id === step);
  return (
    <div className="cycle">
      <div className="cycle-track">
        <motion.div
          className="cycle-fill"
          animate={{ width: idx < 0 ? (status === 'done' ? '100%' : '0%') : `${(idx / (STEPS.length - 1)) * 100}%` }}
          transition={{ type: 'spring', stiffness: 120, damping: 22 }}
        />
      </div>
      {STEPS.map((s, i) => {
        const state = status === 'done' && idx < 0 ? 'done' : i < idx ? 'done' : i === idx ? 'active' : 'todo';
        return (
          <div key={s.id} className={`cyc-step cs-${state}`}>
            <div className="cyc-dot">
              {state === 'active' && status === 'running' && (
                <motion.span className="cyc-pulse" animate={{ scale: [1, 1.8], opacity: [0.7, 0] }} transition={{ duration: 1.4, repeat: Infinity }} />
              )}
              <s.Icon size={15} />
            </div>
            <span>{s.label}</span>
          </div>
        );
      })}
      <div className="cycle-loop">
        <Repeat size={13} /> iteration <b>{iteration || 0}</b>
      </div>
    </div>
  );
}

function ScoreGrid({ ids, scores, failures }) {
  return (
    <div className="score-grid">
      {ids.map((id) => {
        const s = scores[id];
        const has = s != null;
        return (
          <motion.div
            key={id}
            className={`score-cell ${has ? `sc-${scoreTone(s)}` : 'sc-empty'}`}
            initial={false}
            animate={has ? { scale: [0.85, 1.06, 1] } : { scale: 1 }}
            transition={{ duration: 0.45 }}
            title={(failures[id] || []).map((f) => `${tagLabel(f.tag)}: ${f.detail}`).join('\n')}
          >
            <span className="sc-id">{id}</span>
            <span className="sc-val">{has ? <AnimatedNumber value={s * 100} /> : '·'}</span>
            {has && failures[id]?.length > 0 && <span className="sc-fail">{failures[id].length}</span>}
          </motion.div>
        );
      })}
    </div>
  );
}

function Panel({ title, Icon, active, children, className = '' }) {
  return (
    <motion.section layout className={`card panel ${active ? 'panel-active' : ''} ${className}`}>
      <div className="card-head">
        <div className="card-title">
          <Icon size={15} /> {title}
        </div>
        {active && <span className="dot dot-live" />}
      </div>
      {children}
    </motion.section>
  );
}

const Empty = ({ children }) => <div className="muted small panel-empty">{children}</div>;

export default function Evolution() {
  const { ui, server } = useConsole();
  const e = ui.evo;
  const busy = e.status === 'running' || !!server?.evolving;
  const ids = (server?.tickets || []).map((t) => t.id);
  const gridIds = ids.length ? ids : Object.keys(e.scores);
  const losses = Object.entries(e.monitor?.losses || {}).sort((a, b) => b[1] - a[1]);
  const maxLoss = Math.max(0.0001, ...losses.map(([, v]) => v));
  const baseDesign = e.launch?.design || server?.current;
  const proposal = e.redesign?.proposal;
  const added = proposal ? new Set([...roleNames(proposal)].filter((n) => !roleNames(baseDesign).has(n))) : new Set();
  const evalRun = ui.runs.eval;

  return (
    <div className="evo">
      <Controls busy={busy} />

      <section className="card cycle-card">
        <div className="card-head">
          <div className="card-title">
            Supervisor loop
            <span className={`status-pill sp-${e.status}`}>{e.status}</span>
          </div>
          <div className="meta-row small muted">
            {e.namespace && <span className="mono">{e.namespace}</span>}
            {e.approve && <span>approve: {e.approve}</span>}
            {e.maxIter && <span>max {e.maxIter} iter</span>}
          </div>
        </div>
        <Cycle step={e.step} iteration={e.iteration} status={e.status} />
        {e.error && (
          <div className="alert alert-err">
            <TriangleAlert size={14} /> {e.error}
          </div>
        )}
        {e.status === 'done' && e.endScores && (
          <div className="end-scores">
            Run finished · scores {e.endScores.map((s, i) => <span key={i} className={`es es-${scoreTone(s)}`}>{pct(s)}</span>)}
          </div>
        )}
      </section>

      <div className="evo-grid">
        <Panel title={`Score · team v${e.evalVersion ?? e.launch?.version ?? '–'}`} Icon={Gauge} active={e.step === 'score'} className="span-2">
          <div className="score-wrap">
            <ScoreRing score={e.evalScore ?? 0} size={92} label={e.evalScore != null ? 'team score' : e.step === 'score' ? 'scoring' : 'idle'} />
            <div className="score-right">
              <ScoreGrid ids={gridIds} scores={e.scores} failures={e.failures} />
              {e.evalTokens != null && <div className="muted small">{e.evalTokens.toLocaleString()} tokens used</div>}
            </div>
          </div>
          {evalRun && evalRun.status === 'running' && (
            <div className="mini-pipe">
              <div className="mini-head small muted">
                Now solving <span className="mono">{evalRun.ticket}</span>
              </div>
              <div className="graph-scroll">
                <PipelineGraph design={baseDesign} run={evalRun} compact />
              </div>
            </div>
          )}
        </Panel>

        <Panel title="Monitor" Icon={LineChart} active={e.step === 'monitor'}>
          {e.monitor ? (
            <>
              <div className="flags">
                <span className="chip">score {pct(e.monitor.score)}</span>
                {e.monitor.focus_tag && <TagPill tag={e.monitor.focus_tag} />}
                {e.monitor.plateau && <span className="chip chip-warn">plateau</span>}
                {e.monitor.done && <span className="chip chip-ok">done</span>}
              </div>
              <div className="bars">
                {losses.length === 0 && <Empty>No losses — perfect run.</Empty>}
                {losses.map(([tag, v], i) => (
                  <div key={tag} className="bar-row">
                    <span className="bar-label">{tagLabel(tag)}</span>
                    <div className="bar-track">
                      <motion.div
                        className={`bar-fill ${tag === e.monitor.focus_tag ? 'focus' : ''}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${(v / maxLoss) * 100}%` }}
                        transition={{ delay: i * 0.08, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                      />
                    </div>
                    <span className="bar-val mono">{v.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <Empty>Loss by failure tag appears after scoring.</Empty>
          )}
        </Panel>

        <Panel title="Reflect" Icon={Lightbulb} active={e.step === 'reflect'}>
          {e.reflect ? (
            <div className="lists">
              <h4>Patterns</h4>
              <ul className="bullets">
                {e.reflect.patterns?.map((p, i) => (
                  <motion.li key={i} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }}>
                    {p}
                  </motion.li>
                ))}
              </ul>
              <h4>Lessons</h4>
              <ul className="bullets bullets-accent">
                {e.reflect.lessons?.map((p, i) => (
                  <motion.li key={i} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 + i * 0.06 }}>
                    {p}
                  </motion.li>
                ))}
              </ul>
            </div>
          ) : (
            <Empty>The supervisor reflects on failures here.</Empty>
          )}
        </Panel>

        <Panel title="Diagnose" Icon={Stethoscope} active={e.step === 'diagnose'}>
          {e.diagnose ? (
            <div className="diag">
              <div className="diag-cause">{String(e.diagnose.cause || '').replace(/_/g, ' ')}</div>
              {e.diagnose.focus_tag && <TagPill tag={e.diagnose.focus_tag} />}
              <p>{e.diagnose.summary}</p>
            </div>
          ) : (
            <Empty>Root cause of the dominant failure.</Empty>
          )}
        </Panel>

        <Panel title="Redesign" Icon={PenTool} active={e.step === 'redesign'} className="span-all">
          {e.retries.length > 0 && (
            <div className="retries">
              {e.retries.map((r, i) => (
                <div key={i} className="retry">
                  <RotateCw size={12} /> retry {i + 1}: {r}
                </div>
              ))}
            </div>
          )}
          {e.redesign?.failed && <div className="alert alert-err">No valid proposal: {e.redesign.error}</div>}
          {proposal ? (
            <div className="diff">
              <div className="diff-col">
                <div className="diff-label">Current · v{baseDesign?.version}</div>
                <TeamGraph design={baseDesign} />
              </div>
              <div className="diff-col">
                <div className="diff-label grad-text">
                  Proposed · v{proposal.version} · {e.redesign.coordination}
                </div>
                <TeamGraph design={proposal} added={added} />
                <div className="badges">
                  {[...added].map((n) => (
                    <motion.span key={n} className="add-badge" initial={{ scale: 0 }} animate={{ scale: 1 }}>
                      + {n}
                    </motion.span>
                  ))}
                </div>
                <p className="rationale">{proposal.rationale}</p>
              </div>
            </div>
          ) : (
            !e.redesign?.failed && <Empty>A new team design is proposed here.</Empty>
          )}
          {e.gateResult && (
            <div className={`gate-result ${e.gateResult.approved ? 'ok' : 'err'}`}>
              {e.gateResult.approved ? 'Approved' : 'Rejected'} ({e.gateResult.mode})
              {e.adopt && <> · team v{e.adopt.version} adopted</>}
            </div>
          )}
          {e.step === 'gate' && ui.gate && <div className="gate-wait">Waiting for your decision…</div>}
        </Panel>
      </div>

      <section className="card">
        <div className="card-head">
          <div className="card-title">Supervisor timeline</div>
          <span className="muted small">{e.log.length} events</span>
        </div>
        <ul className="timeline">
          <AnimatePresence initial={false}>
            {[...e.log].reverse().slice(0, 40).map((l) => (
              <motion.li key={l.id} layout initial={{ opacity: 0, x: -14 }} animate={{ opacity: 1, x: 0 }}>
                <span className="tl-dot" />
                <span className="tl-kind">{l.kind === 'phase' ? l.phase : l.kind}</span>
                <span className="tl-text">{describe(l)}</span>
                <span className="tl-ts">{timeAgo(l.ts)}</span>
              </motion.li>
            ))}
          </AnimatePresence>
          {!e.log.length && <Empty>Start an evolution run to watch the supervisor work.</Empty>}
        </ul>
      </section>
    </div>
  );
}

function describe(l) {
  if (l.kind === 'run_start') return `namespace ${l.namespace}, approve=${l.approve}, max ${l.max_iterations}`;
  if (l.kind === 'eval_start') return `scoring v${l.version} on ${l.tickets?.length} tickets`;
  if (l.kind === 'eval_end') return `v${l.version} scored ${pct(l.score)} · ${l.tokens} tok`;
  if (l.kind === 'gate_waiting') return `proposal v${l.proposal?.version} awaiting human`;
  if (l.kind === 'run_end') return `scores ${(l.scores || []).map((s) => pct(s)).join(' → ')}`;
  if (l.kind === 'run_error') return l.error;
  switch (l.phase) {
    case 'launch':
      return `iteration ${l.iteration} · team v${l.version} (${l.coordination})`;
    case 'monitor':
      return `score ${pct(l.score)}${l.focus_tag ? ` · focus ${tagLabel(l.focus_tag)}` : ''}${l.plateau ? ' · plateau' : ''}`;
    case 'reflect':
      return `${l.patterns?.length || 0} patterns, ${l.lessons?.length || 0} lessons`;
    case 'diagnose':
      return `${l.cause}: ${l.summary}`;
    case 'redesign':
      return `proposal v${l.proposal?.version} (${l.coordination})`;
    case 'redesign_retry':
    case 'redesign_failed':
      return l.error;
    case 'gate':
      return `${l.approved ? 'approved' : 'rejected'} (${l.mode})`;
    case 'adopt':
      return `team v${l.version} live`;
    default:
      return '';
  }
}
