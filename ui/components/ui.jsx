'use client';

import { useEffect } from 'react';
import { animate, motion, useMotionValue, useTransform } from 'framer-motion';
import { scoreTone, tagLabel } from '@/lib/format';

export function AnimatedNumber({ value, format = (v) => v.toFixed(0), duration = 0.9 }) {
  const mv = useMotionValue(0);
  const text = useTransform(mv, (v) => format(v));
  useEffect(() => {
    const c = animate(mv, value ?? 0, { duration, ease: [0.16, 1, 0.3, 1] });
    return () => c.stop();
  }, [value, duration, mv]);
  return <motion.span>{text}</motion.span>;
}

export function ScoreRing({ score, size = 72, stroke = 6, label }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const tone = scoreTone(score);
  return (
    <div className={`ring ring-${tone}`} style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <defs>
          <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} className="ring-bg" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          className="ring-fg"
          strokeWidth={stroke}
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - (score ?? 0)) }}
          transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1] }}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="ring-label">
        <strong>
          <AnimatedNumber value={(score ?? 0) * 100} />
        </strong>
        {label && <small>{label}</small>}
      </div>
    </div>
  );
}

export function TagPill({ tag, count }) {
  return (
    <span className={`tag tag-${tag}`}>
      {tagLabel(tag)}
      {count > 1 && <b>×{count}</b>}
    </span>
  );
}

export function Stat({ label, children, sub }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{children}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

export function TeamGraph({ design, added = new Set(), small }) {
  if (!design) return null;
  return (
    <div className={`team-graph ${small ? 'tg-small' : ''}`}>
      {design.stages.map((names, i) => (
        <div key={i} className="tg-step">
          {i > 0 && <span className="tg-arrow">→</span>}
          <div className="tg-stage">
            {names.map((n) => (
              <span key={n} className={`tg-role ${added.has(n) ? 'tg-added' : ''}`}>
                {added.has(n) && <span className="tg-plus">+</span>}
                {n}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
