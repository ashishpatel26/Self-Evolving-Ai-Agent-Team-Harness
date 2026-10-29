'use client';

import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Activity, GitBranch, History, BookOpen, Sparkles, X } from 'lucide-react';
import { ConsoleProvider, useConsole } from '@/lib/store';
import TopBar from './TopBar';
import LiveDesk from './LiveDesk';
import Evolution from './Evolution';
import TeamHistory from './TeamHistory';
import Knowledge from './Knowledge';
import GateModal from './GateModal';

const NAV = [
  { id: 'live', label: 'Live Desk', Icon: Activity, hint: 'Run a ticket' },
  { id: 'evolution', label: 'Evolution', Icon: GitBranch, hint: 'Supervisor loop' },
  { id: 'history', label: 'Team History', Icon: History, hint: 'Versions & scores' },
  { id: 'knowledge', label: 'Knowledge', Icon: BookOpen, hint: 'Learnings & log' },
];

export default function Console() {
  return (
    <ConsoleProvider>
      <Shell />
    </ConsoleProvider>
  );
}

function Shell() {
  const [tab, setTab] = useState('live');
  const [navOpen, setNavOpen] = useState(false);
  const { ui, server } = useConsole();

  useEffect(() => {
    const h = window.location.hash.slice(1);
    if (NAV.some((n) => n.id === h)) setTab(h);
  }, []);

  const go = (id) => {
    setTab(id);
    setNavOpen(false);
    history.replaceState(null, '', `#${id}`);
  };

  const evolving = ui.evo.status === 'running' || server?.evolving;

  return (
    <div className="app">
      <div className="bg-grid" aria-hidden />
      <div className="bg-glow" aria-hidden />
      <aside className={`sidebar ${navOpen ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">
            <Sparkles size={16} />
          </div>
          <div>
            <div className="brand-name">Evolving Support</div>
            <div className="brand-sub">Agent Team Console</div>
          </div>
          <button className="icon-btn only-mobile" onClick={() => setNavOpen(false)} aria-label="Close menu">
            <X size={16} />
          </button>
        </div>
        <nav className="nav">
          {NAV.map(({ id, label, Icon, hint }) => (
            <button key={id} className={`nav-item ${tab === id ? 'active' : ''}`} onClick={() => go(id)}>
              {tab === id && <motion.span layoutId="nav-pill" className="nav-pill" transition={{ type: 'spring', stiffness: 400, damping: 34 }} />}
              <Icon size={16} />
              <span className="nav-text">
                <span>{label}</span>
                <small>{hint}</small>
              </span>
              {id === 'evolution' && evolving && <span className="dot dot-live" />}
              {id === 'evolution' && ui.gate && <span className="nav-badge">gate</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="foot-label">Current team</div>
          <div className="foot-version">
            <span className="grad-text">v{server?.current?.version ?? '–'}</span>
            <span className="muted">{server?.current?.roles?.length ?? 0} roles · {server?.current?.coordination || '—'}</span>
          </div>
          <div className="foot-paper">Based on “Evolving Agent Teams”</div>
        </div>
      </aside>
      {navOpen && <div className="scrim only-mobile" onClick={() => setNavOpen(false)} />}

      <main className="main">
        <TopBar onMenu={() => setNavOpen(true)} title={NAV.find((n) => n.id === tab)?.label} />
        <div className="content">
          <AnimatePresence mode="wait">
            <motion.div
              key={tab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18 }}
            >
              {tab === 'live' && <LiveDesk />}
              {tab === 'evolution' && <Evolution />}
              {tab === 'history' && <TeamHistory />}
              {tab === 'knowledge' && <Knowledge />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
      <GateModal onOpenEvolution={() => go('evolution')} />
    </div>
  );
}
