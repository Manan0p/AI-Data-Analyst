'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import { Suspense, use, useEffect, useRef, useState } from 'react';
import { api } from '@/services/api';
import { Analysis } from '@/types';

const Chart = dynamic(() => import('@/components/Chart'), { ssr: false });

function RowsTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows || rows.length === 0) return null;
  const cols = Object.keys(rows[0]);
  return (
    <div className="mt-3 rounded-xl overflow-x-auto max-h-60" style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)' }}>
      <table className="w-full data-table text-xs">
        <thead>
          <tr>
            {cols.map(c => (
              <th key={c} className="py-2 px-3">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 10).map((r, i) => (
            <tr key={i}>
              {cols.map(c => (
                <td key={c} className="py-2 px-3 whitespace-nowrap">
                  {String(r[c] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const SUGGESTIONS = [
  'Which region generated the highest revenue?',
  'Show monthly sales trends',
  'What are the top 5 customers by sales?',
  'Detect anomalies',
  'Show a bar chart of sales by category',
  'Which product sub-category has the most orders?',
];

function AnalysePage({ id }: { id: string }) {
  const searchParams = useSearchParams();
  const { data: datasets, isLoading: datasetsLoading } = useQuery({ queryKey: ['datasets'], queryFn: api.datasets });
  const { data: profile } = useQuery({ queryKey: ['profile', id], queryFn: () => api.profile(id), enabled: !!id });

  const dataset = datasets?.find(d => d.id === id);
  const [question, setQuestion] = useState(searchParams?.get('q') ?? '');
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string; analysis?: Analysis }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-fire from query param
  useEffect(() => {
    const q = searchParams?.get('q');
    if (q && dataset) { setQuestion(q); }
  }, [searchParams, dataset]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function send() {
    if (!question.trim() || loading) return;
    const q = question.trim();
    setMessages(m => [...m, { role: 'user', content: q }]);
    setQuestion('');
    setLoading(true);
    setError('');
    try {
      const res = await api.chat(id, q);
      setMessages(m => [...m, { role: 'assistant', content: res.answer, analysis: res }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  if (datasetsLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4" style={{ width: 32, height: 32 }} />
          <p className="muted">Loading dataset details…</p>
        </div>
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="flex h-screen items-center justify-center p-8">
        <div className="card text-center max-w-md py-12 px-8">
          <p className="text-4xl mb-3">◈</p>
          <h2 className="text-xl font-bold text-white mb-2">Dataset Not Found</h2>
          <p className="muted mb-6">The dataset you are trying to access does not exist or may have expired.</p>
          <Link href="/datasets" className="btn">View All Datasets</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-[#09090b]">
      {/* Top bar */}
      <header className="flex items-center justify-between px-8 py-4 flex-shrink-0" style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ background: 'rgba(56,189,248,0.1)', border: '1px solid rgba(56,189,248,0.2)' }}>
            <span style={{ color: 'var(--accent-cyan)' }}>◈</span>
          </div>
          <div>
            <h1 className="font-semibold text-white text-sm">{dataset.name.replace(/\.csv$/i, '')}</h1>
            <p className="faint">{dataset.rows.toLocaleString()} rows · {dataset.columns} cols</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {profile && (
            <div className="flex gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
              <span className="badge badge-cyan">{profile.duplicate_rows} dupes</span>
              <span className="badge badge-violet">{profile.columns_profile.filter(c => c.null_percentage > 0).length} cols w/ nulls</span>
            </div>
          )}
          <Link href={`/explore/${id}`} className="btn-ghost border rounded-xl text-xs px-3 py-2" style={{ borderColor: 'var(--border)' }}>
            Explore data ↗
          </Link>
        </div>
      </header>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {messages.length === 0 && (
          <div className="page-enter flex h-full flex-col items-center justify-center text-center py-12">
            <div className="mb-4 text-3xl" style={{ color: 'var(--accent-cyan)' }}>✦</div>
            <h2 className="text-2xl font-bold text-white mb-2">Ask about your data</h2>
            <p className="muted mb-8">Ask questions, analyze trends, create charts, run SQL, or detect anomalies.</p>
            <div className="flex flex-wrap justify-center gap-2 max-w-xl">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => setQuestion(s)}
                  className="rounded-xl px-3.5 py-2 text-sm text-left transition-all"
                  style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
                  onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent-cyan)'; (e.currentTarget as HTMLElement).style.color = 'var(--text-primary)'; }}
                  onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'; (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)'; }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.role === 'user' ? (
              <div className="max-w-lg rounded-2xl px-5 py-3 text-sm font-medium text-white shadow-sm" style={{ background: 'linear-gradient(135deg, #0284c7, #6366f1)', border: '1px solid rgba(255,255,255,0.1)' }}>
                {m.content}
              </div>
            ) : (
              <div className="max-w-2xl w-full space-y-3">
                {/* Answer */}
                <div className="card">
                  <div className="flex items-start gap-3">
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg flex-shrink-0" style={{ background: 'linear-gradient(135deg, #38bdf8, #818cf8)' }}>
                      <span className="text-xs font-bold text-black">AI</span>
                    </div>
                    <p className="text-sm text-white leading-relaxed">{m.content}</p>
                  </div>

                  {/* Chart */}
                  {m.analysis?.chart && (
                    <div className="mt-4">
                      <Chart spec={m.analysis.chart} />
                    </div>
                  )}

                  {/* SQL */}
                  {m.analysis?.generated_sql && (
                    <details className="mt-3">
                      <summary className="cursor-pointer text-xs font-medium" style={{ color: 'var(--accent-cyan)' }}>▸ Generated SQL</summary>
                      <pre className="code-block mt-2">{m.analysis.generated_sql}</pre>
                    </details>
                  )}

                  {/* Pandas */}
                  {m.analysis?.generated_pandas && (
                    <details className="mt-3">
                      <summary className="cursor-pointer text-xs font-medium" style={{ color: 'var(--accent-emerald)' }}>▸ Generated Pandas</summary>
                      <pre className="code-block mt-2">{m.analysis.generated_pandas}</pre>
                    </details>
                  )}

                  {/* Result rows table (for SQL / metric / tabular responses) */}
                  {Array.isArray(m.analysis?.metadata?.rows) && (m.analysis.metadata.rows as Record<string, unknown>[]).length > 0 && !m.analysis.chart && (
                    <RowsTable rows={m.analysis.metadata.rows as Record<string, unknown>[]} />
                  )}

                  {/* Anomalies */}
                  {m.analysis?.anomalies && m.analysis.anomalies.length > 0 && (
                    <div className="mt-3 rounded-xl p-3 text-sm" style={{ background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.2)' }}>
                      <span className="badge badge-rose mr-2">{m.analysis.anomalies.length}</span>
                      <span style={{ color: '#f43f5e' }}>anomalies detected</span>
                    </div>
                  )}

                  {/* Meta */}
                  {m.analysis && (
                    <div className="mt-3 flex flex-wrap gap-2 border-t pt-3" style={{ borderColor: 'var(--border)' }}>
                      <span className="faint">{Math.round(m.analysis.confidence * 100)}% confidence</span>
                      {m.analysis.metadata?.tool != null && (
                        <span className="badge badge-violet text-xs">{String(m.analysis.metadata.tool)}</span>
                      )}
                      {m.analysis.metadata?.planner != null && (
                        <span className="badge badge-cyan text-xs">{String(m.analysis.metadata.planner)}</span>
                      )}
                    </div>
                  )}
                </div>

                {/* Reasoning */}
                {m.analysis?.reasoning && (
                  <p className="px-1 text-xs" style={{ color: 'var(--text-faint)' }}>
                    {m.analysis.reasoning}
                  </p>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="card flex items-center gap-3 py-4">
              <div className="spinner" />
              <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Analysing with Gemini…</span>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-xl px-4 py-3 text-sm" style={{ background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.2)', color: '#f43f5e' }}>
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 px-8 py-4" style={{ borderTop: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
        <div className="relative">
          <textarea
            ref={textareaRef}
            className="textarea pr-28 min-h-[56px] leading-relaxed"
            rows={1}
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask a question about your data… (Press Enter to send)"
          />
          <button
            onClick={send}
            disabled={loading || !question.trim()}
            className="btn absolute right-3 top-3 px-4 py-2 text-xs"
          >
            {loading ? <span className="spinner" style={{ width: 14, height: 14 }} /> : 'Send'}
          </button>
        </div>
        <p className="mt-1.5 text-right faint">Press Enter to send · Shift + Enter for new line</p>
      </div>
    </div>
  );
}

export default function AnalysePageWrapper({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center"><div className="spinner" style={{ width: 32, height: 32 }} /></div>}>
      <AnalysePage id={id} />
    </Suspense>
  );
}
