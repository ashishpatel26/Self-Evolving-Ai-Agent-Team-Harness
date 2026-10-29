'use client';

import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Send, Loader2, Ticket, Coins, Clock } from 'lucide-react';
import { useConsole } from '@/lib/store';
import { api } from '@/lib/api';
import { fmtNum } from '@/lib/format';
import PipelineGraph from './PipelineGraph';
import ActivityFeed from './ActivityFeed';
import ReplyCard from './ReplyCard';

export default function LiveDesk() {
  const { server, ui, liveRun: runId, setLiveRun: setRunId } = useConsole();
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const lastLive = Object.keys(ui.runs).filter((k) => k.startsWith('live-')).pop();
  const shown = runId || lastLive;
  const run = shown ? ui.runs[shown] : null;
  const version = server?.current?.version;
  const running = busy || run?.status === 'running' || (runId && !run);

  const submit = async (t = text) => {
    if (!t.trim() || running) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await api.ticket(t.trim());
      setRunId(res.run);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const elapsed = run?.endedAt && run?.startedAt ? (run.endedAt - run.startedAt).toFixed(1) : null;

  return (
    <div className="desk">
      <section className="card composer">
        <div className="card-head">
          <div className="card-title">
            <Ticket size={15} /> New ticket
          </div>
          <span className="muted small">Ctrl/⌘ + Enter to run</span>
        </div>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => (e.metaKey || e.ctrlKey) && e.key === 'Enter' && submit()}
          placeholder="Describe the customer's problem… e.g. “My order A1002 arrived broken and I also want to change my delivery address.”"
          rows={4}
        />
        <div className="composer-foot">
          <div className="samples">
            {(server?.tickets || []).map((t) => (
              <button key={t.id} className="sample" title={t.text} onClick={() => setText(t.text)}>
                <span className="sample-id">{t.id}</span>
                <span className="sample-text">{t.text}</span>
              </button>
            ))}
          </div>
          <button className="btn btn-primary" disabled={!text.trim() || running} onClick={() => submit()}>
            {running ? <Loader2 size={15} className="spin" /> : <Send size={15} />}
            Run with team v{version ?? '…'}
          </button>
        </div>
        {err && <div className="alert alert-err">{err}</div>}
      </section>

      <div className="desk-grid">
        <section className="card graph-card">
          <div className="card-head">
            <div className="card-title">
              Agent pipeline
              {run && <span className={`status-pill sp-${run.status}`}>{run.status}</span>}
            </div>
            <div className="meta-row">
              {run && <span className="mono muted small">{run.ticket}</span>}
              {run && (
                <span className="meta">
                  <Coins size={12} /> {fmtNum(run.tokens)} tok
                </span>
              )}
              {elapsed && (
                <span className="meta">
                  <Clock size={12} /> {elapsed}s
                </span>
              )}
            </div>
          </div>
          <div className="graph-scroll">
            <PipelineGraph design={server?.current} run={run} />
          </div>
          <AnimatePresence>
            {run?.text && (
              <motion.blockquote className="ticket-quote" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                “{run.text}”
              </motion.blockquote>
            )}
          </AnimatePresence>
        </section>

        <section className="card feed-card">
          <div className="card-head">
            <div className="card-title">Activity</div>
            <span className="muted small">{run ? `${run.feed.length} events` : 'idle'}</span>
          </div>
          <ActivityFeed items={run?.feed || []} />
        </section>
      </div>

      <ReplyCard run={run} />
    </div>
  );
}
