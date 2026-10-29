'use client';

import { createContext, useCallback, useContext, useEffect, useReducer, useRef, useState } from 'react';
import { api } from './api';

const Ctx = createContext(null);
export const useConsole = () => useContext(Ctx);

const EVO_IDLE = {
  status: 'idle', namespace: null, approve: null, maxIter: null, iteration: 0, step: null,
  launch: null, monitor: null, reflect: null, diagnose: null, redesign: null, gateResult: null, adopt: null,
  scores: {}, failures: {}, evalVersion: null, evalScore: null, evalTokens: null, retries: [], log: [], error: null,
  endScores: null,
};

const initial = { runs: {}, evo: EVO_IDLE, gate: null, lastTs: 0, count: 0 };

let seq = 0;

function newRun(ev) {
  return {
    run: ev.run, ticket: ev.ticket, text: ev.text, version: ev.version, stages: ev.stages || [],
    stageStatus: (ev.stages || []).map(() => 'pending'), activeStage: -1, roleStatus: {}, tools: {},
    outputs: [], feed: [], status: 'running', guardrail: null, reply: null, error: null, scored: null,
    tokens: 0, startedAt: ev.ts, endedAt: null,
  };
}

function reduceRun(r, ev) {
  const feedItem = { id: ++seq, ...ev };
  switch (ev.kind) {
    case 'ticket_start':
      return { ...newRun(ev), feed: [feedItem] };
    case 'stage_start': {
      const stageStatus = [...r.stageStatus];
      stageStatus[ev.stage] = 'active';
      const roleStatus = { ...r.roleStatus };
      (ev.roles || []).forEach((n) => (roleStatus[n] = 'active'));
      return { ...r, stageStatus, roleStatus, activeStage: ev.stage, feed: [...r.feed, feedItem] };
    }
    case 'tool_start': {
      const list = [...(r.tools[ev.role] || []), { id: feedItem.id, tool: ev.tool, args: ev.args, status: 'running' }];
      return { ...r, tools: { ...r.tools, [ev.role]: list }, feed: [...r.feed, { ...feedItem, status: 'running' }] };
    }
    case 'tool_end': {
      const list = [...(r.tools[ev.role] || [])];
      const i = list.findLastIndex((t) => t.tool === ev.tool && t.status === 'running');
      let fid = null;
      if (i >= 0) {
        fid = list[i].id;
        list[i] = { ...list[i], status: ev.ok ? 'ok' : 'error', result: ev.result };
      }
      const feed = fid
        ? r.feed.map((f) => (f.id === fid ? { ...f, status: ev.ok ? 'ok' : 'error', result: ev.result } : f))
        : [...r.feed, { ...feedItem, kind: 'tool_start', status: ev.ok ? 'ok' : 'error' }];
      return { ...r, tools: { ...r.tools, [ev.role]: list }, feed };
    }
    case 'stage_end': {
      const stageStatus = [...r.stageStatus];
      stageStatus[ev.stage] = ev.ok ? 'done' : 'error';
      const roleStatus = { ...r.roleStatus };
      (ev.roles || []).forEach((n) => (roleStatus[n] = ev.ok ? 'done' : 'error'));
      return {
        ...r, stageStatus, roleStatus, tokens: r.tokens + (ev.tokens || 0),
        outputs: [...r.outputs, ev], feed: [...r.feed, feedItem],
      };
    }
    case 'guardrail':
      return { ...r, guardrail: ev.detail || 'blocked', status: 'blocked', feed: [...r.feed, feedItem] };
    case 'ticket_end':
      return {
        ...r, reply: ev.reply, status: r.status === 'blocked' ? 'blocked' : 'done', endedAt: ev.ts,
        activeStage: -1, stageStatus: r.stageStatus.map((s) => (s === 'pending' ? 'skipped' : s)),
        feed: [...r.feed, feedItem],
      };
    case 'ticket_error':
      return { ...r, error: ev.error, status: 'error', endedAt: ev.ts, activeStage: -1, feed: [...r.feed, feedItem] };
    case 'live_scored':
      return { ...r, scored: ev, feed: [...r.feed, feedItem] };
    default:
      return r;
  }
}

const RUN_KINDS = new Set(['ticket_start', 'stage_start', 'tool_start', 'tool_end', 'stage_end', 'guardrail', 'ticket_end', 'ticket_error', 'live_scored']);

function reduceEvo(e, ev) {
  const log = [...e.log.slice(-80), { id: ++seq, ...ev }];
  switch (ev.kind) {
    case 'run_start':
      return { ...EVO_IDLE, status: 'running', namespace: ev.namespace, approve: ev.approve, maxIter: ev.max_iterations, log };
    case 'eval_start':
      return { ...e, step: 'score', scores: {}, failures: {}, evalVersion: ev.version, evalScore: null, evalTokens: null, log };
    case 'ticket_scored':
      return { ...e, scores: { ...e.scores, [ev.ticket]: ev.score }, failures: { ...e.failures, [ev.ticket]: ev.failures || [] } };
    case 'eval_end':
      return { ...e, evalScore: ev.score, evalTokens: ev.tokens, log };
    case 'phase': {
      const p = ev.phase;
      if (p === 'launch')
        return { ...e, status: e.status === 'idle' ? 'running' : e.status, step: 'launch', iteration: ev.iteration, launch: ev,
          monitor: null, reflect: null, diagnose: null, redesign: null, gateResult: null, adopt: null, retries: [], log };
      if (p === 'redesign_retry') return { ...e, retries: [...e.retries, ev.error], log };
      if (p === 'redesign_failed') return { ...e, step: 'redesign', redesign: { failed: true, error: ev.error }, log };
      if (p === 'gate') return { ...e, step: 'gate', gateResult: ev, log };
      return { ...e, step: p, [p]: ev, log };
    }
    case 'gate_waiting':
      return { ...e, step: 'gate', log };
    case 'run_end':
      return { ...e, status: 'done', step: 'done', endScores: ev.scores, log };
    case 'run_error':
      return { ...e, status: 'error', error: ev.error, log };
    default:
      return e;
  }
}

const EVO_KINDS = new Set(['run_start', 'eval_start', 'ticket_scored', 'eval_end', 'phase', 'gate_waiting', 'run_end', 'run_error']);

function applyEvent(s, ev) {
  let { runs, evo, gate } = s;
  if (RUN_KINDS.has(ev.kind) && ev.run) {
    const cur = runs[ev.run];
    if (cur || ev.kind === 'ticket_start') runs = { ...runs, [ev.run]: reduceRun(cur, ev) };
  }
  if (EVO_KINDS.has(ev.kind)) evo = reduceEvo(evo, ev);
  if (ev.kind === 'gate_waiting') gate = ev.proposal;
  if ((ev.kind === 'phase' && ev.phase === 'gate') || ev.kind === 'run_end' || ev.kind === 'run_error') gate = null;
  return { ...s, runs, evo, gate, lastTs: ev.ts || s.lastTs, count: s.count + 1 };
}

function reducer(s, a) {
  switch (a.type) {
    case 'event':
      return applyEvent(s, a.ev);
    case 'batch':
      return a.events.reduce(applyEvent, s);
    case 'clearGate':
      return { ...s, gate: null };
    case 'setGate':
      return s.gate ? s : { ...s, gate: a.proposal };
    case 'evoStarting':
      return { ...s, evo: { ...EVO_IDLE, status: 'running', approve: a.approve, maxIter: a.maxIter } };
    default:
      return s;
  }
}

const REFRESH_ON = (ev) =>
  ev.kind === 'eval_end' || ev.kind === 'run_end' || ev.kind === 'evals_done' || (ev.kind === 'phase' && ev.phase === 'adopt');

function spacing(ev, backlog) {
  const fast = backlog > 120 ? 0.25 : backlog > 50 ? 0.6 : 1;
  const tool = ev.kind === 'tool_start' || ev.kind === 'tool_end';
  let ms = tool ? 250 : 350;
  if (ev.run === 'evals') ms = 30;
  else if (ev.run === 'eval') ms = tool ? 140 : 220;
  if (ev.kind === 'ticket_scored') ms = 260;
  return ms * fast;
}

const sig = (ev) => [ev.ts, ev.kind, ev.run, ev.ticket, ev.stage, ev.role, ev.tool, ev.phase].join('|');

export function ConsoleProvider({ children }) {
  const [ui, dispatch] = useReducer(reducer, initial);
  const [server, setServer] = useState(null);
  const [serverError, setServerError] = useState(null);
  const [conn, setConn] = useState('connecting');
  const [queued, setQueued] = useState(0);
  const [liveRun, setLiveRun] = useState(null);
  const queue = useRef([]);
  const timer = useRef(null);
  const seen = useRef(new Set());

  const refresh = useCallback(async () => {
    try {
      const st = await api.state();
      setServer(st);
      setServerError(null);
      if (!st.gate_open) dispatch({ type: 'clearGate' });
      else if (st.gate_proposal) dispatch({ type: 'setGate', proposal: st.gate_proposal });
    } catch (e) {
      setServerError(e.message);
    }
  }, []);

  const pump = useCallback(() => {
    if (timer.current) return;
    const next = () => {
      const ev = queue.current.shift();
      setQueued(queue.current.length);
      if (!ev) {
        timer.current = null;
        return;
      }
      dispatch({ type: 'event', ev });
      if (REFRESH_ON(ev)) refresh();
      timer.current = setTimeout(next, spacing(ev, queue.current.length));
    };
    timer.current = setTimeout(next, 0);
  }, [refresh]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    let es;
    let closed = false;
    let backlog = [];
    let ready = false;
    let retry;

    const remember = (ev) => {
      const k = sig(ev);
      if (seen.current.has(k)) return false;
      seen.current.add(k);
      if (seen.current.size > 4000) seen.current = new Set([...seen.current].slice(-2000));
      return true;
    };

    const open = () => {
      setConn('connecting');
      ready = false;
      backlog = [];
      es = new EventSource('/api/events');
      es.onmessage = (m) => {
        let ev;
        try {
          ev = JSON.parse(m.data);
        } catch {
          return;
        }
        if (ev.kind === 'ready') {
          ready = true;
          setConn('live');
          const fresh = backlog.filter(remember).map((e) => ({ ...e, replayed: true }));
          if (fresh.length) dispatch({ type: 'batch', events: fresh });
          backlog = [];
          return;
        }
        if (!ready) {
          backlog.push(ev);
          return;
        }
        seen.current.add(sig(ev)); // only backlog replays are deduped; live events always play
        queue.current.push(ev);
        setQueued(queue.current.length);
        pump();
      };
      es.onerror = () => {
        es.close();
        if (closed) return;
        setConn('offline');
        retry = setTimeout(open, 2500);
      };
    };
    open();
    return () => {
      closed = true;
      clearTimeout(retry);
      es?.close();
      clearTimeout(timer.current);
      timer.current = null;
    };
  }, [pump]);

  const value = { ui, dispatch, server, serverError, conn, queued, refresh, liveRun, setLiveRun };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
