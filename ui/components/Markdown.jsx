'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Agent output is model-written markdown (bold, lists, tables). Raw HTML is not rendered.
export default function Markdown({ children, className = '' }) {
  return (
    <div className={`md ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ a: (p) => <a {...p} target="_blank" rel="noreferrer" /> }}>
        {String(children ?? '')}
      </ReactMarkdown>
    </div>
  );
}
