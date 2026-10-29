'use client';

import { Cpu, Database, Menu, RefreshCw } from 'lucide-react';
import { useConsole } from '@/lib/store';

const CONN = {
  live: { label: 'Live', cls: 'ok' },
  connecting: { label: 'Connecting', cls: 'warn' },
  offline: { label: 'Reconnecting', cls: 'err' },
};

export default function TopBar({ onMenu, title }) {
  const { server, serverError, conn, queued, refresh } = useConsole();
  const c = CONN[conn] || CONN.connecting;
  return (
    <header className="topbar">
      <button className="icon-btn only-mobile" onClick={onMenu} aria-label="Open menu">
        <Menu size={18} />
      </button>
      <h1 className="page-title">{title}</h1>
      <div className="topbar-right">
        {serverError && <span className="chip chip-err" title={serverError}>API error</span>}
        <span className="chip hide-sm" title="Model">
          <Cpu size={13} /> {server?.model || '…'}
        </span>
        {server?.offline && <span className="chip chip-warn">Offline mode</span>}
        <span className="chip hide-sm" title="Team namespace in K">
          <Database size={13} /> {server?.namespace || '…'}
        </span>
        <span className={`live-pill ${c.cls}`} title={queued ? `${queued} events buffered for playback` : 'Event stream'}>
          <span className={`dot dot-${c.cls}`} />
          {c.label}
          {queued > 0 && <span className="queued">+{queued}</span>}
        </span>
        <button className="icon-btn" onClick={refresh} aria-label="Refresh state" title="Refresh state">
          <RefreshCw size={15} />
        </button>
      </div>
    </header>
  );
}
