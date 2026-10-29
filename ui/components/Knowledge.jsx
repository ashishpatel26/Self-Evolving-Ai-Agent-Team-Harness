'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { BookOpen, GitBranch } from 'lucide-react';
import { useConsole } from '@/lib/store';

function inline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((p, i) =>
    p.startsWith('**') && p.endsWith('**') ? <strong key={i}>{p.slice(2, -2)}</strong> : p.startsWith('`') && p.endsWith('`') ? <code key={i}>{p.slice(1, -1)}</code> : p,
  );
}

function Markdown({ text }) {
  if (!text?.trim()) return <div className="muted small panel-empty">Nothing recorded yet.</div>;
  const out = [];
  let list = [];
  const flush = () => {
    if (list.length) out.push(<ul key={`ul${out.length}`}>{list}</ul>);
    list = [];
  };
  text.split(/\r?\n/).forEach((raw, i) => {
    const line = raw.trimEnd();
    const rule = /RULE:/i.test(line);
    const h = line.match(/^(#{1,4})\s+(.*)/);
    const li = line.match(/^\s*(?:[-*]|\d+\.)\s+(.*)/);
    if (h) {
      flush();
      const Tag = `h${Math.min(h[1].length + 1, 5)}`;
      out.push(<Tag key={i}>{inline(h[2])}</Tag>);
    } else if (li) {
      list.push(
        <li key={i} className={rule ? 'md-rule' : ''}>
          {inline(li[1])}
        </li>,
      );
    } else if (!line.trim()) {
      flush();
    } else {
      flush();
      out.push(
        <p key={i} className={rule ? 'md-rule' : ''}>
          {inline(line)}
        </p>,
      );
    }
  });
  flush();
  return <div className="md">{out}</div>;
}

const DOCS = [
  { id: 'learnings', label: 'LEARNINGS.md', Icon: BookOpen, hint: 'What the team has learned — rules injected into every role.' },
  { id: 'evolution', label: 'EVOLUTION.md', Icon: GitBranch, hint: 'Why each team version was created.' },
];

export default function Knowledge() {
  const { server } = useConsole();
  const [doc, setDoc] = useState('learnings');
  const d = DOCS.find((x) => x.id === doc);
  const text = server?.[doc] || '';
  const rules = (server?.learnings || '').split('\n').filter((l) => /RULE:/i.test(l)).length;

  return (
    <div className="knowledge">
      <div className="doc-tabs">
        {DOCS.map(({ id, label, Icon }) => (
          <button key={id} className={`doc-tab ${doc === id ? 'on' : ''}`} onClick={() => setDoc(id)}>
            {doc === id && <motion.span layoutId="doc-on" className="doc-pill" />}
            <Icon size={14} /> <span>{label}</span>
          </button>
        ))}
        <span className="muted small doc-count">{rules} rules learned</span>
      </div>
      <motion.section key={doc} className="card doc-card" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <div className="card-head">
          <div className="card-title">
            <d.Icon size={15} /> {d.label}
          </div>
          <span className="muted small">{d.hint}</span>
        </div>
        <Markdown text={text} />
      </motion.section>
    </div>
  );
}
