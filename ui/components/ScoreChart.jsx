'use client';

import { motion } from 'framer-motion';

export default function ScoreChart({ points }) {
  const W = 1000;
  const H = 280;
  const P = { l: 40, r: 24, t: 30, b: 30 };
  if (!points.length) return <div className="muted small panel-empty">No scored versions yet.</div>;
  const n = points.length;
  const x = (i) => P.l + (n === 1 ? (W - P.l - P.r) / 2 : (i * (W - P.l - P.r)) / (n - 1));
  const y = (v) => P.t + (1 - v) * (H - P.t - P.b);
  const line = points.map((p, i) => `${i ? 'L' : 'M'}${x(i)},${y(p.score)}`).join(' ');
  const area = `${line} L${x(n - 1)},${y(0)} L${x(0)},${y(0)} Z`;
  const acc = points.filter((p) => p.accuracy != null);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label="Score over versions">
      <defs>
        <linearGradient id="chartLine" x1="0" x2="1">
          <stop offset="0%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#22d3ee" />
        </linearGradient>
        <linearGradient id="chartArea" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0, 0.25, 0.5, 0.75, 1].map((g) => (
        <g key={g}>
          <line x1={P.l} x2={W - P.r} y1={y(g)} y2={y(g)} className="grid-line" />
          <text x={P.l - 8} y={y(g) + 4} className="axis" textAnchor="end">
            {g * 100}
          </text>
        </g>
      ))}
      <motion.path d={area} fill="url(#chartArea)" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5, duration: 0.8 }} />
      <motion.path
        d={line}
        fill="none"
        stroke="url(#chartLine)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
      />
      {acc.length > 1 && (
        <motion.path
          d={points.map((p, i) => (p.accuracy == null ? '' : `${i && points[i - 1]?.accuracy != null ? 'L' : 'M'}${x(i)},${y(p.accuracy)}`)).join(' ')}
          fill="none"
          className="acc-line"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.2, delay: 0.3 }}
        />
      )}
      {points.map((p, i) => (
        <g key={p.version}>
          <motion.circle
            cx={x(i)}
            cy={y(p.score)}
            r="5"
            className="pt"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.3 + (i / n) * 0.9, type: 'spring', stiffness: 400 }}
          />
          <text x={x(i)} y={y(p.score) - 12} className="pt-label" textAnchor="middle">
            {Math.round(p.score * 100)}
          </text>
          <text x={x(i)} y={H - 8} className="axis" textAnchor="middle">
            v{p.version}
          </text>
        </g>
      ))}
    </svg>
  );
}
