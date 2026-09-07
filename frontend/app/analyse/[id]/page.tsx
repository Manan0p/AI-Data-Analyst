'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import { Suspense, use, useEffect, useRef, useState } from 'react';
import { api } from '@/services/api';
import { Analysis } from '@/types';

const Chart = dynamic(() => import('@/components/Chart'), { ssr: false });

function getRowsFromAnalysis(analysis?: Analysis | null): Record<string, unknown>[] | null {
  if (!analysis) return null;
  if (Array.isArray(analysis.data) && analysis.data.length > 0) return analysis.data;
  if (analysis.metadata && Array.isArray(analysis.metadata.rows) && analysis.metadata.rows.length > 0) {
    return analysis.metadata.rows as Record<string, unknown>[];
  }
  return null;
}

function getCodeFromAnalysis(analysis?: Analysis | null): { type: 'sql' | 'pandas'; code: string } | null {
  if (!analysis) return null;
  if (analysis.generated_sql) return { type: 'sql', code: analysis.generated_sql };
  if (analysis.generated_pandas) return { type: 'pandas', code: analysis.generated_pandas };
  if (analysis.code) return { type: 'pandas', code: analysis.code };
  return null;
}

function RowsTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows || rows.length === 0) return null;
  const cols = Object.keys(rows[0]);
  return (
    <div className="mt-space-sm rounded-xl overflow-x-auto max-h-64 border border-outline-variant/30 bg-surface-container-lowest shadow-xs">
      <table className="stitch-table text-xs">
        <thead className="sticky top-0 bg-surface-container-low shadow-xs">
          <tr>
            {cols.map((c) => (
              <th key={c} className="py-2 px-3 text-left font-semibold text-on-surface-variant font-code-sm text-code-sm">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 15).map((r, i) => (
            <tr key={i} className="hover:bg-surface-container-low/60 transition-colors">
              {cols.map((c) => (
                <td key={c} className="py-2 px-3 whitespace-nowrap font-code-sm text-code-sm text-on-surface">
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
  'What are the top 5 product categories by sales?',
  'Plot monthly revenue trends over time',
  'Which region generated highest total revenue?',
  'Detect anomalies and outliers in this dataset',
  'Show correlation between price and quantity',
  'Provide an executive summary of key metrics',
];

function AnalysePageContent({ id }: { id: string }) {
  const searchParams = useSearchParams();
  const { data: datasets, isLoading: datasetsLoading } = useQuery({ queryKey: ['datasets'], queryFn: api.datasets });

  const dataset = datasets?.find((d) => d.id === id);
  const [question, setQuestion] = useState(searchParams?.get('q') ?? '');
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string; analysis?: Analysis }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeRightTab, setActiveRightTab] = useState<'chart' | 'table' | 'code'>('chart');
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null);
  const [clearingHistory, setClearingHistory] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);

  // Deterministic session ID for this dataset (persists across visits/reloads)
  const sessionId = `session-${id}`;

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load chat history from backend (Redis / DB) on mount
  useEffect(() => {
    if (!sessionId) return;
    let isMounted = true;
    api.chatHistory(sessionId)
      .then((history) => {
        if (!isMounted) return;
        if (Array.isArray(history) && history.length > 0) {
          setMessages(history);
          const lastAssistant = [...history].reverse().find((m) => m.role === 'assistant' && m.analysis);
          if (lastAssistant?.analysis) {
            setSelectedAnalysis(lastAssistant.analysis);
            const rows = getRowsFromAnalysis(lastAssistant.analysis);
            if (lastAssistant.analysis.chart) {
              setActiveRightTab('chart');
            } else if (rows && rows.length > 0) {
              setActiveRightTab('table');
            } else if (lastAssistant.analysis.generated_sql || lastAssistant.analysis.generated_pandas) {
              setActiveRightTab('code');
            }
          }
        }
      })
      .catch((err) => {
        console.error('Failed to load chat history:', err);
      })
      .finally(() => {
        if (isMounted) setHistoryLoaded(true);
      });

    return () => {
      isMounted = false;
    };
  }, [sessionId]);

  // Auto-fire from query param
  useEffect(() => {
    const q = searchParams?.get('q');
    if (q && dataset && historyLoaded) {
      setQuestion(q);
    }
  }, [searchParams, dataset, historyLoaded]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function send(queryText?: string) {
    const promptToSend = queryText || question;
    if (!promptToSend.trim() || loading) return;
    const q = promptToSend.trim();
    setMessages((m) => [...m, { role: 'user', content: q }]);
    setQuestion('');
    setLoading(true);
    setError('');

    try {
      const res = await api.chat(id, q, sessionId);
      setMessages((m) => [...m, { role: 'assistant', content: res.answer, analysis: res }]);
      setSelectedAnalysis(res);

      const rows = getRowsFromAnalysis(res);
      if (res.chart) {
        setActiveRightTab('chart');
      } else if (rows && rows.length > 0) {
        setActiveRightTab('table');
      } else if (res.generated_sql || res.generated_pandas) {
        setActiveRightTab('code');
      }
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

  async function clearHistory() {
    if (clearingHistory) return;
    setClearingHistory(true);
    try {
      await api.clearChatHistory(sessionId);
      setMessages([]);
      setSelectedAnalysis(null);
    } catch {
      // silently ignore
    } finally {
      setClearingHistory(false);
    }
  }

  if (datasetsLoading) {
    return (
      <div className="flex h-[calc(100vh-64px)] items-center justify-center bg-surface text-on-surface-variant">
        <span className="material-symbols-outlined text-[32px] text-primary animate-spin">sync</span>
        <span className="ml-2 font-label-md">Loading Agent Workspace...</span>
      </div>
    );
  }

  const selectedRows = getRowsFromAnalysis(selectedAnalysis);
  const selectedCode = getCodeFromAnalysis(selectedAnalysis);

  return (
    <div className="flex h-[calc(100vh-64px)] flex-col bg-surface overflow-hidden">
      {/* 1. Header Toolbar */}
      <header className="flex items-center justify-between px-gutter-canvas py-space-sm bg-surface-container-lowest border-b border-outline-variant/30 shadow-xs flex-shrink-0">
        <div className="flex items-center gap-space-sm">
          <div className="flex items-center gap-space-xs text-on-surface-variant font-label-md text-label-md">
            <Link href="/" className="hover:text-primary transition-colors flex items-center gap-space-2xs">
              <span className="material-symbols-outlined text-[16px]">database</span>
              <span>Datasets</span>
            </Link>
            <span className="text-outline-variant font-code-sm text-code-sm">/</span>
            <span className="font-code-md text-code-md text-primary font-semibold truncate max-w-[200px]">
              {dataset?.name || id}
            </span>
            <span className="text-outline-variant font-code-sm text-code-sm">/</span>
            <span className="px-space-xs py-space-3xs rounded bg-primary-fixed text-on-primary-fixed font-label-sm text-label-sm uppercase font-bold">
              AI Analyst Chat
            </span>
          </div>

          <div className="hidden lg:flex items-center gap-space-2xs px-space-sm py-space-3xs rounded-full bg-surface-container-high text-on-surface font-code-sm text-code-sm">
            <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse"></span>
            <span className="font-semibold text-primary">LangGraph Multi-Agent Mesh Active</span>
          </div>
        </div>

        <div className="flex items-center gap-space-sm">
          <Link
            href={`/insights/${id}`}
            className="flex items-center gap-space-2xs px-space-sm py-space-xs rounded-lg bg-surface-container-low hover:bg-surface-container-high text-on-surface font-label-md text-label-md transition-colors"
          >
            <span className="material-symbols-outlined text-[16px] text-primary">bolt</span>
            <span>Insights Dashboard</span>
          </Link>
          <Link
            href={`/explore/${id}`}
            className="flex items-center gap-space-2xs px-space-sm py-space-xs rounded-lg bg-surface-container-low hover:bg-surface-container-high text-on-surface font-label-md text-label-md transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">table_rows</span>
            <span>Data Grid</span>
          </Link>
          {messages.length > 0 && (
            <button
              id="clear-chat-history-btn"
              onClick={clearHistory}
              disabled={clearingHistory}
              title="Clear chat history (removes from Redis + DB)"
              className="flex items-center gap-space-2xs px-space-sm py-space-xs rounded-lg bg-error-container hover:bg-error text-on-error-container hover:text-on-error font-label-md text-label-md transition-colors disabled:opacity-50"
            >
              <span className="material-symbols-outlined text-[16px]">
                {clearingHistory ? 'sync' : 'delete_history'}
              </span>
              <span className="hidden sm:inline">Clear History</span>
            </button>
          )}
        </div>
      </header>

      {/* 2. Split Workspace Layout */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left Pane: Multi-Agent Conversation Thread (50% width) */}
        <div className="w-full lg:w-1/2 flex flex-col bg-surface border-r border-outline-variant/30 h-full overflow-hidden">
          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-space-lg space-y-space-lg">
            {messages.length === 0 ? (
              <div className="py-space-xl text-center space-y-space-md">
                <div className="w-14 h-14 rounded-2xl bg-primary-fixed text-primary mx-auto flex items-center justify-center shadow-xs">
                  <span className="material-symbols-outlined text-[32px]">neurology</span>
                </div>
                <div>
                  <h3 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                    Autonomous Multi-Agent AI Analyst
                  </h3>
                  <p className="font-body-md text-body-md text-on-surface-variant max-w-md mx-auto mt-space-2xs">
                    Ask quantitative questions in plain English. The swarm coordinates Planner, SQL/Python Code Sandbox, and Chart Specialists.
                  </p>
                </div>

                {/* Suggestions Grid */}
                <div className="max-w-lg mx-auto pt-space-sm text-left">
                  <span className="font-label-sm text-label-sm uppercase text-on-surface-variant font-semibold block mb-space-xs">
                    Quick Analytical Inquiries:
                  </span>
                  <div className="flex flex-col gap-space-2xs">
                    {SUGGESTIONS.map((s, idx) => (
                      <button
                        key={idx}
                        onClick={() => send(s)}
                        className="p-space-sm rounded-xl bg-surface-container-lowest border border-outline-variant/30 hover:border-primary/50 text-on-surface font-body-sm text-body-sm text-left transition-all shadow-xs flex items-center justify-between group"
                      >
                        <span>{s}</span>
                        <span className="material-symbols-outlined text-[16px] text-on-surface-variant group-hover:text-primary">
                          north_east
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              messages.map((m, idx) => {
                const rows = getRowsFromAnalysis(m.analysis);
                const codeObj = getCodeFromAnalysis(m.analysis);

                return (
                  <div key={idx} className="space-y-space-sm">
                    {m.role === 'user' ? (
                      <div className="flex justify-end">
                        <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-primary text-on-primary px-space-md py-space-sm shadow-xs font-body-md text-body-md">
                          {m.content}
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-space-sm">
                        {/* Assistant Agent Container */}
                        <div
                          onClick={() => {
                            if (m.analysis) {
                              setSelectedAnalysis(m.analysis);
                              if (m.analysis.chart) setActiveRightTab('chart');
                            }
                          }}
                          className={`rounded-xl bg-surface-container-lowest border ${
                            selectedAnalysis === m.analysis
                              ? 'border-primary shadow-sm ring-1 ring-primary/20'
                              : 'border-outline-variant/30 hover:border-outline-variant'
                          } p-space-md shadow-xs space-y-space-sm transition-all cursor-pointer`}
                        >
                          {/* Agent Header */}
                          <div className="flex items-center justify-between border-b border-outline-variant/20 pb-space-xs">
                            <div className="flex items-center gap-space-xs">
                              <span className="flex items-center justify-center w-6 h-6 rounded-md bg-primary-fixed text-primary">
                                <span className="material-symbols-outlined text-[14px]">psychology</span>
                              </span>
                              <span className="font-title-md text-title-md text-on-surface font-bold">
                                Synthesis & Insights
                              </span>
                            </div>
                            <span className="px-space-xs py-space-3xs rounded-full bg-surface-container-high text-on-surface-variant font-code-sm text-code-sm font-semibold">
                              Agent Executed
                            </span>
                          </div>

                          {/* Synthesis Text */}
                          <div className="font-body-md text-body-md text-on-surface leading-relaxed whitespace-pre-wrap">
                            {m.content}
                          </div>

                          {/* Inline Table of Returned Rows */}
                          {rows && rows.length > 0 && (
                            <div className="pt-space-2xs">
                              <div className="flex items-center justify-between text-xs text-on-surface-variant font-semibold mb-1">
                                <span className="flex items-center gap-1 font-code-sm">
                                  <span className="material-symbols-outlined text-[14px] text-primary">table_chart</span>
                                  <span>Returned Records ({rows.length})</span>
                                </span>
                                <button
                                  onClick={() => {
                                    setSelectedAnalysis(m.analysis || null);
                                    setActiveRightTab('table');
                                  }}
                                  className="text-primary hover:underline font-label-md text-label-md"
                                >
                                  Open in Inspector ➔
                                </button>
                              </div>
                              <RowsTable rows={rows} />
                            </div>
                          )}

                          {/* SQL / Python Query Block (Collapsible) */}
                          {codeObj && (
                            <details className="group rounded-lg bg-surface-container-low border border-outline-variant/30 overflow-hidden">
                              <summary className="px-space-sm py-space-2xs cursor-pointer font-code-sm text-code-sm font-semibold text-primary flex items-center justify-between select-none">
                                <span className="flex items-center gap-space-2xs">
                                  <span className="material-symbols-outlined text-[16px]">
                                    {codeObj.type === 'sql' ? 'database' : 'terminal'}
                                  </span>
                                  <span>Executed {codeObj.type.toUpperCase()} Query</span>
                                </span>
                                <span className="font-code-sm text-code-sm text-on-surface-variant">Click to view</span>
                              </summary>
                              <pre className="p-space-sm bg-slate-900 text-slate-100 font-code-sm text-code-sm overflow-x-auto rounded-b-lg">
                                <code>{codeObj.code}</code>
                              </pre>
                            </details>
                          )}

                          {/* Inline Chart View Trigger */}
                          {m.analysis?.chart && (
                            <button
                              onClick={() => {
                                setSelectedAnalysis(m.analysis || null);
                                setActiveRightTab('chart');
                              }}
                              className="mt-space-xs inline-flex items-center gap-space-2xs px-space-sm py-space-2xs rounded-lg bg-primary-fixed text-on-primary-fixed font-label-md text-label-md font-semibold hover:bg-primary-fixed-dim transition-colors"
                            >
                              <span className="material-symbols-outlined text-[16px]">bar_chart</span>
                              <span>View Interactive Plotly Canvas</span>
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}

            {loading && (
              <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/30 p-space-md shadow-xs flex items-center gap-space-sm text-on-surface-variant">
                <span className="material-symbols-outlined text-[20px] text-primary animate-spin">sync</span>
                <span className="font-label-md text-label-md font-medium">
                  Swarm coordinating: Planner ➔ Query Execution ➔ Synthesis...
                </span>
              </div>
            )}
            {error && (
              <div className="rounded-xl bg-error-container/40 border border-error/30 p-space-md text-error text-body-sm font-medium">
                {error}
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Prompt Input Dock */}
          <div className="p-space-md bg-surface-container-lowest border-t border-outline-variant/30">
            <div className="relative rounded-xl border border-outline-variant/40 bg-surface-container-low focus-within:border-primary focus-within:bg-white transition-all shadow-xs">
              <textarea
                ref={textareaRef}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Ask about top categories, sales trends, correlations, anomalies..."
                rows={2}
                className="w-full bg-transparent px-space-md py-space-sm font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant focus:outline-none resize-none"
              />
              <div className="flex items-center justify-between px-space-md pb-space-xs">
                <span className="font-code-sm text-code-sm text-on-surface-variant">
                  Press <strong>Enter</strong> to run · <strong>Shift+Enter</strong> for newline
                </span>
                <button
                  onClick={() => send()}
                  disabled={!question.trim() || loading}
                  className="inline-flex items-center gap-space-2xs px-space-md py-space-2xs rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold hover:bg-primary-container disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-xs"
                >
                  <span>Dispatch</span>
                  <span className="material-symbols-outlined text-[16px]">send</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Pane: Interactive Visualization Canvas & Inspector (50% width) */}
        <div className="w-full lg:w-1/2 flex flex-col bg-surface-container-lowest h-full overflow-hidden">
          {/* Canvas View Mode Switcher */}
          <div className="flex items-center justify-between px-space-lg py-space-sm border-b border-outline-variant/30 bg-surface-container-lowest flex-shrink-0">
            <div className="flex items-center gap-space-2xs">
              <button
                onClick={() => setActiveRightTab('chart')}
                className={`px-space-sm py-space-2xs rounded-lg font-label-md text-label-md transition-colors ${
                  activeRightTab === 'chart'
                    ? 'bg-primary text-on-primary font-semibold'
                    : 'bg-surface-container-low text-on-surface hover:bg-surface-container-high'
                }`}
              >
                Interactive Chart
              </button>
              <button
                onClick={() => setActiveRightTab('table')}
                className={`px-space-sm py-space-2xs rounded-lg font-label-md text-label-md transition-colors ${
                  activeRightTab === 'table'
                    ? 'bg-primary text-on-primary font-semibold'
                    : 'bg-surface-container-low text-on-surface hover:bg-surface-container-high'
                }`}
              >
                Computed Data {selectedRows ? `(${selectedRows.length})` : ''}
              </button>
              <button
                onClick={() => setActiveRightTab('code')}
                className={`px-space-sm py-space-2xs rounded-lg font-label-md text-label-md transition-colors ${
                  activeRightTab === 'code'
                    ? 'bg-primary text-on-primary font-semibold'
                    : 'bg-surface-container-low text-on-surface hover:bg-surface-container-high'
                }`}
              >
                Query / Code
              </button>
            </div>

            <span className="font-code-sm text-code-sm text-on-surface-variant font-medium">
              Inspector Canvas
            </span>
          </div>

          {/* Canvas Main Body */}
          <div className="flex-1 p-space-lg overflow-auto bg-surface-container-low/30 flex items-center justify-center">
            {activeRightTab === 'chart' && (
              selectedAnalysis?.chart ? (
                <div className="w-full h-full min-h-[420px] bg-white rounded-xl border border-outline-variant/30 p-space-md shadow-xs flex items-center justify-center">
                  <Chart figure={selectedAnalysis.chart} />
                </div>
              ) : (
                <div className="text-center p-space-2xl text-on-surface-variant">
                  <span className="material-symbols-outlined text-[48px] text-outline">analytics</span>
                  <p className="font-headline-sm text-headline-sm mt-space-xs font-semibold text-on-surface">
                    No Chart Rendered Yet
                  </p>
                  <p className="font-body-sm text-body-sm mt-space-2xs max-w-sm">
                    Ask a query like &quot;Plot monthly revenue breakdown by category&quot; or check the <strong>Computed Data</strong> tab to view extracted records.
                  </p>
                  {selectedRows && selectedRows.length > 0 && (
                    <button
                      onClick={() => setActiveRightTab('table')}
                      className="mt-space-md inline-flex items-center gap-space-xs px-space-md py-space-xs rounded-lg bg-primary-fixed text-on-primary-fixed font-label-md text-label-md font-semibold"
                    >
                      <span className="material-symbols-outlined text-[16px]">table_chart</span>
                      <span>View {selectedRows.length} Computed Rows</span>
                    </button>
                  )}
                </div>
              )
            )}

            {activeRightTab === 'table' && (
              selectedRows && selectedRows.length > 0 ? (
                <div className="w-full h-full bg-white rounded-xl border border-outline-variant/30 p-space-md shadow-xs overflow-auto flex flex-col">
                  <div className="flex items-center justify-between pb-space-xs border-b border-outline-variant/20 mb-space-xs">
                    <span className="font-headline-sm text-headline-sm font-bold text-on-surface">
                      Extracted Result Records ({selectedRows.length})
                    </span>
                  </div>
                  <div className="flex-1 overflow-auto">
                    <RowsTable rows={selectedRows} />
                  </div>
                </div>
              ) : (
                <div className="text-center p-space-2xl text-on-surface-variant">
                  <span className="material-symbols-outlined text-[48px] text-outline">table_chart</span>
                  <p className="font-headline-sm text-headline-sm mt-space-xs font-semibold text-on-surface">
                    No Computed Table Output
                  </p>
                  <p className="font-body-sm text-body-sm mt-space-2xs">
                    Run a query to execute SQL or Pandas and preview results here.
                  </p>
                </div>
              )
            )}

            {activeRightTab === 'code' && (
              selectedCode ? (
                <div className="w-full h-full bg-slate-950 text-slate-100 rounded-xl p-space-lg font-code-sm text-code-sm overflow-auto shadow-sm">
                  <div className="flex items-center justify-between pb-space-sm mb-space-sm border-b border-slate-800 text-slate-400">
                    <span className="uppercase font-bold tracking-wider">Executed {selectedCode.type.toUpperCase()} Code</span>
                    <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/40">Validated</span>
                  </div>
                  <pre className="overflow-x-auto text-emerald-300">
                    <code>{selectedCode.code}</code>
                  </pre>
                </div>
              ) : (
                <div className="text-center p-space-2xl text-on-surface-variant">
                  <span className="material-symbols-outlined text-[48px] text-outline">code</span>
                  <p className="font-headline-sm text-headline-sm mt-space-xs font-semibold text-on-surface">
                    No Execution Code Yet
                  </p>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AnalysePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm font-code-sm">Loading Agent Analyst...</div>}>
      <AnalysePageContent id={id} />
    </Suspense>
  );
}
