'use client';

import React, { useState } from 'react';
import Link from 'next/link';

interface LandingPageProps {
  onOpenAuth: (mode?: 'login' | 'register') => void;
}

export function LandingPage({ onOpenAuth }: LandingPageProps) {
  const [activeTab, setActiveTab] = useState<'chat' | 'sql' | 'anomaly' | 'charts'>('chat');

  return (
    <div className="min-h-screen bg-[#09090b] text-[#fafafa] selection:bg-cyan-500/30 selection:text-cyan-200 relative overflow-x-hidden font-sans">
      {/* Dynamic Background Ambient Glows */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div
          className="absolute -top-[20%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] rounded-full opacity-25 blur-[140px]"
          style={{ background: 'radial-gradient(circle, #0284c7 0%, #6366f1 50%, transparent 80%)' }}
        />
        <div
          className="absolute top-[40%] -left-[200px] w-[600px] h-[600px] rounded-full opacity-15 blur-[120px]"
          style={{ background: 'radial-gradient(circle, #38bdf8 0%, transparent 70%)' }}
        />
        <div
          className="absolute top-[70%] -right-[200px] w-[600px] h-[600px] rounded-full opacity-15 blur-[120px]"
          style={{ background: 'radial-gradient(circle, #a855f7 0%, transparent 70%)' }}
        />
      </div>

      {/* Top Navbar */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-[#09090b]/80 border-b border-white/10 transition-all">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-9 w-9 items-center justify-center rounded-xl shadow-lg shadow-cyan-500/20"
              style={{ background: 'linear-gradient(135deg, #0284c7, #6366f1)' }}
            >
              <span className="text-sm font-black text-white tracking-wider">IF</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-white">InsightForge</span>
              <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-cyan-950/60 text-cyan-300 border border-cyan-800/40">
                AI Data Analyst
              </span>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-8 text-sm text-gray-300 font-medium">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#demo" className="hover:text-white transition-colors">Interactive Demo</a>
            <a href="#architecture" className="hover:text-white transition-colors">Architecture</a>
            <a href="#security" className="hover:text-white transition-colors">Security</a>
          </nav>

          <div className="flex items-center gap-3">
            <button
              onClick={() => onOpenAuth('login')}
              className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:text-white hover:bg-white/5 transition-all"
            >
              Sign In
            </button>
            <button
              onClick={() => onOpenAuth('register')}
              className="px-4 py-2 rounded-lg text-sm font-semibold text-white shadow-lg transition-all transform hover:-translate-y-0.5 active:translate-y-0"
              style={{
                background: 'linear-gradient(135deg, #0284c7, #6366f1)',
                boxShadow: '0 4px 14px 0 rgba(2, 132, 199, 0.35)'
              }}
            >
              Get Started Free →
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 pt-20 pb-16 px-6 max-w-5xl mx-auto text-center">
        {/* Pill Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.05] border border-white/10 text-xs font-medium text-cyan-300 mb-8 backdrop-blur-md shadow-inner">
          <span className="flex h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>Self-Correcting LangGraph Multi-Agent Architecture</span>
          <span className="text-gray-500">•</span>
          <span className="text-gray-300">Gemini 2.5 Flash</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.12]">
          Autonomous Data Intelligence.{' '}
          <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
            Instant Answers.
          </span>
        </h1>

        {/* Hero Subtitle */}
        <p className="mt-6 text-lg sm:text-xl text-gray-400 max-w-3xl mx-auto font-normal leading-relaxed">
          Upload raw CSV datasets and ask complex business questions in plain English.
          InsightForge generates and validates sandboxed <strong className="text-white">DuckDB SQL</strong>, executes <strong className="text-white">AST-whitelisted Pandas</strong> transformations, detects <strong className="text-white">Isolation Forest</strong> outliers, and crafts interactive charts.
        </p>

        {/* Action CTAs */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={() => onOpenAuth('register')}
            className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-bold text-white shadow-xl flex items-center justify-center gap-2.5 transition-all transform hover:-translate-y-1 active:translate-y-0"
            style={{
              background: 'linear-gradient(135deg, #0284c7, #6366f1)',
              boxShadow: '0 8px 24px -4px rgba(2, 132, 199, 0.45)'
            }}
          >
            <span>Launch Workspace Free</span>
            <span className="text-lg">→</span>
          </button>
          <button
            onClick={() => onOpenAuth('login')}
            className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-semibold text-gray-300 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 transition-all backdrop-blur-md"
          >
            Sign In with Existing Account
          </button>
        </div>

        {/* Key Guardrail Highlights */}
        <div className="mt-12 pt-8 border-t border-white/5 flex flex-wrap items-center justify-center gap-6 text-xs text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="text-emerald-400">✓</span> AST-Allowlist Sandbox
          </span>
          <span className="flex items-center gap-1.5">
            <span className="text-cyan-400">✓</span> DuckDB Multi-CSV JOINs
          </span>
          <span className="flex items-center gap-1.5">
            <span className="text-violet-400">✓</span> Neon Cloud PostgreSQL
          </span>
          <span className="flex items-center gap-1.5">
            <span className="text-amber-400">✓</span> 2-Retry Error Recovery
          </span>
        </div>
      </section>

      {/* Interactive Mock Preview / Demo Section */}
      <section id="demo" className="relative z-10 py-12 px-6 max-w-6xl mx-auto">
        <div className="rounded-2xl border border-white/10 bg-[#121215]/90 backdrop-blur-2xl shadow-2xl overflow-hidden">
          {/* Mock Window Header */}
          <div className="px-5 py-3.5 bg-white/[0.03] border-b border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-rose-500/80" />
              <div className="h-3 w-3 rounded-full bg-amber-500/80" />
              <div className="h-3 w-3 rounded-full bg-emerald-500/80" />
              <span className="ml-3 text-xs text-gray-400 font-mono">InsightForge Agent Workspace — Sample Superstore.csv</span>
            </div>
            <div className="hidden sm:flex items-center gap-1.5 text-[11px] text-gray-400 bg-white/5 px-2.5 py-1 rounded-md">
              <span className="text-emerald-400">●</span>
              <span>DuckDB Active & Sandboxed</span>
            </div>
          </div>

          {/* Interactive Feature Tabs */}
          <div className="flex border-b border-white/5 bg-black/20 overflow-x-auto text-xs font-medium">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-5 py-3 border-b-2 flex items-center gap-2 transition-all ${
                activeTab === 'chat'
                  ? 'border-cyan-400 text-cyan-300 bg-cyan-500/5'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <span>💬</span>
              <span>LangGraph Agent QA</span>
            </button>
            <button
              onClick={() => setActiveTab('sql')}
              className={`px-5 py-3 border-b-2 flex items-center gap-2 transition-all ${
                activeTab === 'sql'
                  ? 'border-cyan-400 text-cyan-300 bg-cyan-500/5'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <span>🛢️</span>
              <span>DuckDB SQL Engine</span>
            </button>
            <button
              onClick={() => setActiveTab('anomaly')}
              className={`px-5 py-3 border-b-2 flex items-center gap-2 transition-all ${
                activeTab === 'anomaly'
                  ? 'border-cyan-400 text-cyan-300 bg-cyan-500/5'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <span>🔍</span>
              <span>ML Anomaly Detection</span>
            </button>
            <button
              onClick={() => setActiveTab('charts')}
              className={`px-5 py-3 border-b-2 flex items-center gap-2 transition-all ${
                activeTab === 'charts'
                  ? 'border-cyan-400 text-cyan-300 bg-cyan-500/5'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <span>📊</span>
              <span>Dynamic Visualizations</span>
            </button>
          </div>

          {/* Tab Content Display */}
          <div className="p-6 md:p-8 min-h-[380px] flex flex-col justify-center">
            {activeTab === 'chat' && (
              <div className="space-y-4">
                {/* User Bubble */}
                <div className="flex justify-end">
                  <div className="max-w-xl bg-gradient-to-r from-sky-600 to-indigo-600 text-white p-3.5 rounded-2xl rounded-tr-sm text-sm shadow-md">
                    Which region generated the highest profit margin in 2024, and what were the top 3 selling product categories?
                  </div>
                </div>

                {/* Agent Trace */}
                <div className="max-w-xl bg-black/40 border border-white/10 rounded-xl p-3 text-xs font-mono text-gray-300 space-y-1.5">
                  <div className="flex items-center gap-2 text-cyan-400 font-semibold">
                    <span>⚡ LangGraph State Execution Trace</span>
                  </div>
                  <div className="text-gray-400">1. classify_intent → [tool: sql_tool, intent: aggregation_and_rank]</div>
                  <div className="text-gray-400">2. select_tool → Generated read-only DuckDB SQL JOIN</div>
                  <div className="text-gray-400">3. execute_tool → Executed in 0.024s (Returned 4 rows)</div>
                  <div className="text-emerald-400">4. validate_result → Check passed (0 errors, 0 retries required)</div>
                  <div className="text-gray-400">5. synthesize_answer → Formatted executive response</div>
                </div>

                {/* Assistant Bubble */}
                <div className="flex justify-start">
                  <div className="max-w-2xl bg-white/[0.05] border border-white/10 p-4 rounded-2xl rounded-tl-sm text-sm text-gray-200 space-y-2">
                    <p className="font-semibold text-white">
                      The <span className="text-cyan-300 font-bold">West Region</span> led all territories with an average profit margin of <span className="text-emerald-400 font-bold">28.4%</span> ($108,418 total profit).
                    </p>
                    <p className="text-xs text-gray-400">
                      Top 3 performing categories in the West Region:
                    </p>
                    <div className="grid grid-cols-3 gap-2 pt-1 text-xs">
                      <div className="p-2 rounded bg-black/30 border border-white/5">
                        <p className="text-gray-400">1. Technology</p>
                        <p className="font-bold text-white mt-0.5">$47,210</p>
                      </div>
                      <div className="p-2 rounded bg-black/30 border border-white/5">
                        <p className="text-gray-400">2. Office Supplies</p>
                        <p className="font-bold text-white mt-0.5">$34,820</p>
                      </div>
                      <div className="p-2 rounded bg-black/30 border border-white/5">
                        <p className="text-gray-400">3. Furniture</p>
                        <p className="font-bold text-white mt-0.5">$26,388</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'sql' && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-black/60 border border-white/10 font-mono text-xs text-sky-300 overflow-x-auto">
                  <div className="text-gray-500 mb-2">-- DuckDB Multi-Table Vectorized Query (Read-Only)</div>
                  <div>SELECT r.region, SUM(s.sales) as total_sales, ROUND(AVG(s.profit_margin), 2) as avg_margin</div>
                  <div>FROM dataset_orders s</div>
                  <div>JOIN dataset_regions r ON s.region_id = r.id</div>
                  <div>GROUP BY r.region ORDER BY total_sales DESC LIMIT 5;</div>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                  <div className="p-3 rounded-lg bg-white/[0.03] border border-white/5">
                    <p className="text-[11px] text-gray-400">Execution Speed</p>
                    <p className="text-lg font-bold text-emerald-400">0.018s</p>
                  </div>
                  <div className="p-3 rounded-lg bg-white/[0.03] border border-white/5">
                    <p className="text-[11px] text-gray-400">External Access</p>
                    <p className="text-lg font-bold text-cyan-400">Blocked</p>
                  </div>
                  <div className="p-3 rounded-lg bg-white/[0.03] border border-white/5">
                    <p className="text-[11px] text-gray-400">Memory Cap</p>
                    <p className="text-lg font-bold text-violet-400">256MB</p>
                  </div>
                  <div className="p-3 rounded-lg bg-white/[0.03] border border-white/5">
                    <p className="text-[11px] text-gray-400">Cross-Table JOINs</p>
                    <p className="text-lg font-bold text-amber-400">Supported</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'anomaly' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-amber-950/30 border border-amber-500/30 text-xs text-amber-200">
                  <span className="font-semibold">⚠️ 14 Outliers Detected via Scikit-Learn IsolationForest</span>
                  <span className="text-[11px] bg-amber-900/50 px-2 py-0.5 rounded">Contamination: 0.05</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3.5 rounded-xl bg-black/40 border border-white/10 text-xs">
                    <span className="text-rose-400 font-bold">Transaction #4092</span>
                    <p className="text-gray-400 mt-1">Discount: 80% | Quantity: 200</p>
                    <p className="text-[11px] text-gray-500 mt-2">Anomaly Score: -0.384 (Extreme negative margin variance)</p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-black/40 border border-white/10 text-xs">
                    <span className="text-rose-400 font-bold">Transaction #8121</span>
                    <p className="text-gray-400 mt-1">Shipping Cost: $480 | Sales: $12</p>
                    <p className="text-[11px] text-gray-500 mt-2">Anomaly Score: -0.342 (Severe shipping-to-sales ratio skew)</p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-black/40 border border-white/10 text-xs">
                    <span className="text-rose-400 font-bold">Transaction #1944</span>
                    <p className="text-gray-400 mt-1">Unit Price: $9,400 | Return: Yes</p>
                    <p className="text-[11px] text-gray-500 mt-2">Anomaly Score: -0.311 (High-value return anomaly)</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'charts' && (
              <div className="space-y-4">
                <div className="h-44 w-full rounded-xl bg-gradient-to-b from-white/[0.03] to-black/40 border border-white/10 p-4 flex flex-col justify-between">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-white">Monthly Sales Trend (2024)</span>
                    <span className="text-cyan-400 text-[11px]">Dynamic Line & Area Chart</span>
                  </div>
                  {/* Simulated SVG Wave */}
                  <svg className="w-full h-24 stroke-cyan-400 fill-cyan-500/10" viewBox="0 0 500 100" preserveAspectRatio="none">
                    <path
                      d="M0,80 Q70,30 140,65 T280,20 T420,40 T500,10 L500,100 L0,100 Z"
                      strokeWidth="2.5"
                    />
                  </svg>
                  <div className="flex justify-between text-[10px] text-gray-500">
                    <span>Jan</span><span>Mar</span><span>May</span><span>Jul</span><span>Sep</span><span>Nov</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Metrics Bar */}
      <section className="py-12 px-6 max-w-6xl mx-auto border-y border-white/5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="p-5 rounded-xl bg-white/[0.02] border border-white/5">
            <p className="text-3xl font-extrabold text-white tracking-tight">0.02s</p>
            <p className="text-xs text-gray-400 mt-1 font-medium">DuckDB Query Latency</p>
          </div>
          <div className="p-5 rounded-xl bg-white/[0.02] border border-white/5">
            <p className="text-3xl font-extrabold text-cyan-400 tracking-tight">100%</p>
            <p className="text-xs text-gray-400 mt-1 font-medium">AST-Allowlisted Sandbox</p>
          </div>
          <div className="p-5 rounded-xl bg-white/[0.02] border border-white/5">
            <p className="text-3xl font-extrabold text-violet-400 tracking-tight">5-Node</p>
            <p className="text-xs text-gray-400 mt-1 font-medium">Self-Healing LangGraph Graph</p>
          </div>
          <div className="p-5 rounded-xl bg-white/[0.02] border border-white/5">
            <p className="text-3xl font-extrabold text-emerald-400 tracking-tight">500k</p>
            <p className="text-xs text-gray-400 mt-1 font-medium">Rows Defensive Cap</p>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-20 px-6 max-w-6xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <p className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-2">Production Architecture</p>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white">Engineered for Accuracy & Speed</h2>
          <p className="text-sm text-gray-400 mt-3">
            InsightForge combines bleeding-edge agent orchestration with strict computational guardrails.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Feature 1 */}
          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-cyan-500/40 transition-all group">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-lg mb-4 text-cyan-400 group-hover:scale-110 transition-transform">
              🤖
            </div>
            <h3 className="text-lg font-bold text-white mb-2">LangGraph Multi-Agent</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              5-node state graph with intent classification, tool selection, and a self-correcting 2-retry feedback loop that recovers from bad queries automatically.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-sky-500/40 transition-all group">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-lg mb-4 text-sky-400 group-hover:scale-110 transition-transform">
              🛢️
            </div>
            <h3 className="text-lg font-bold text-white mb-2">In-Process DuckDB SQL</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Multi-table columnar analytical execution. Execute complex relational JOINs across multiple uploaded CSV files with zero disk I/O bottlenecks.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-emerald-500/40 transition-all group">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-lg mb-4 text-emerald-400 group-hover:scale-110 transition-transform">
              🛡️
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Strict AST Allowlist</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Code execution is guarded by an explicit Python syntax tree allowlist. Disallowed function calls, dunder lookups, and OS imports are blocked at compile time.
            </p>
          </div>

          {/* Feature 4 */}
          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-violet-500/40 transition-all group">
            <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-lg mb-4 text-violet-400 group-hover:scale-110 transition-transform">
              🔍
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Isolation Forest ML</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Unsupervised machine learning anomaly scoring pinpointing statistical outliers across multivariate numerical distributions.
            </p>
          </div>

          {/* Feature 5 */}
          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-amber-500/40 transition-all group">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-lg mb-4 text-amber-400 group-hover:scale-110 transition-transform">
              ☁️
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Neon Cloud PostgreSQL</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Auto-rehydrating datasets and multi-turn chat history persisted to serverless Neon PostgreSQL with connection pooling and retry safety.
            </p>
          </div>

          {/* Feature 6 */}
          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-rose-500/40 transition-all group">
            <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-lg mb-4 text-rose-400 group-hover:scale-110 transition-transform">
              🔒
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Multi-Tenant JWT Auth</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Salted bcrypt password hashing and signed JWT bearer tokens. Datasets, chat history, and background jobs are strictly scoped by tenant owner ID.
            </p>
          </div>
        </div>
      </section>

      {/* Architecture / How It Works */}
      <section id="architecture" className="py-16 px-6 max-w-6xl mx-auto">
        <div className="rounded-3xl border border-white/10 bg-gradient-to-b from-white/[0.03] to-transparent p-8 md:p-12">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <p className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-2">Step-by-Step</p>
            <h2 className="text-3xl font-bold text-white">How InsightForge Works</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="p-5 rounded-xl bg-black/40 border border-white/5 space-y-2">
              <span className="text-xs font-mono font-bold text-cyan-400">01 / INGESTION</span>
              <h4 className="text-sm font-bold text-white">Upload & Validate</h4>
              <p className="text-xs text-gray-400">
                CSV headers and types are parsed, sanitized, capped at 25MB/500k rows, and registered in DuckDB.
              </p>
            </div>
            <div className="p-5 rounded-xl bg-black/40 border border-white/5 space-y-2">
              <span className="text-xs font-mono font-bold text-sky-400">02 / AGENT PLAN</span>
              <h4 className="text-sm font-bold text-white">LangGraph Routing</h4>
              <p className="text-xs text-gray-400">
                Gemini 2.5 classifies intent and generates structured tool execution plans with historical context.
              </p>
            </div>
            <div className="p-5 rounded-xl bg-black/40 border border-white/5 space-y-2">
              <span className="text-xs font-mono font-bold text-violet-400">03 / SANDBOX</span>
              <h4 className="text-sm font-bold text-white">Secure Execution</h4>
              <p className="text-xs text-gray-400">
                Code runs through the AST allowlist or read-only DuckDB engine with an automated self-correcting retry loop.
              </p>
            </div>
            <div className="p-5 rounded-xl bg-black/40 border border-white/5 space-y-2">
              <span className="text-xs font-mono font-bold text-emerald-400">04 / SYNTHESIS</span>
              <h4 className="text-sm font-bold text-white">Visual Insights</h4>
              <p className="text-xs text-gray-400">
                Dynamic Recharts/Plotly specs, ML anomaly alerts, and confidence reasoning delivered to the dashboard.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Security Accordion / Section */}
      <section id="security" className="py-16 px-6 max-w-4xl mx-auto">
        <div className="text-center mb-10">
          <p className="text-xs font-bold uppercase tracking-widest text-emerald-400 mb-2">Zero Arbitrary Code Execution</p>
          <h2 className="text-3xl font-bold text-white">Built Ground-Up For Sandbox Security</h2>
        </div>

        <div className="space-y-4">
          <div className="p-5 rounded-xl bg-white/[0.02] border border-white/10">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <span className="text-emerald-400">●</span>
              <span>Why an AST Allowlist instead of a Blacklist?</span>
            </h4>
            <p className="text-xs text-gray-400 mt-2 leading-relaxed">
              Traditional string blacklists (checking for words like &quot;import&quot; or &quot;os&quot;) are notoriously vulnerable to obfuscation bypasses (e.g. <code className="text-cyan-300">getattr(__builtins__, &#39;eval&#39;)</code>). InsightForge parses code into an Abstract Syntax Tree and strictly permits only mathematical operations, subscripts, and 30 explicitly allowed Pandas analytical methods.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-white/[0.02] border border-white/10">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400">●</span>
              <span>How does DuckDB prevent disk access?</span>
            </h4>
            <p className="text-xs text-gray-400 mt-2 leading-relaxed">
              DuckDB is initialized with <code className="text-cyan-300">enable_external_access: False</code> at the engine C++ level and all file-reading table functions (<code className="text-cyan-300">read_csv</code>, <code className="text-cyan-300">read_parquet</code>, <code className="text-cyan-300">glob</code>) are blocked. Only in-memory tables registered by the authenticated user can ever be queried.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-white/[0.02] border border-white/10">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <span className="text-violet-400">●</span>
              <span>How are API costs and server resources protected?</span>
            </h4>
            <p className="text-xs text-gray-400 mt-2 leading-relaxed">
              FastAPI routes are throttled with <strong className="text-white">SlowAPI</strong> rate limiters (10 uploads/min, 30 chats/min) keyed to the authenticated user ID. Ingestion rejects any file over 25MB or 500,000 rows to prevent Out-Of-Memory (OOM) crashes.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Pre-Footer */}
      <section className="py-20 px-6 max-w-5xl mx-auto text-center relative">
        <div
          className="p-10 sm:p-14 rounded-3xl border border-white/10 relative overflow-hidden"
          style={{ background: 'linear-gradient(135deg, rgba(2,132,199,0.12), rgba(99,102,241,0.12))' }}
        >
          <div className="relative z-10 max-w-2xl mx-auto space-y-6">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Ready to experience autonomous data analysis?
            </h2>
            <p className="text-sm text-gray-300">
              Sign in or create a free account to upload your CSV files and start conversing with InsightForge right away.
            </p>
            <div className="pt-2">
              <button
                onClick={() => onOpenAuth('register')}
                className="px-8 py-4 rounded-xl text-base font-bold text-white shadow-xl transition-all transform hover:-translate-y-1 active:translate-y-0"
                style={{
                  background: 'linear-gradient(135deg, #0284c7, #6366f1)',
                  boxShadow: '0 8px 24px -4px rgba(2, 132, 199, 0.45)'
                }}
              >
                Launch Workspace Free →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-white/5 text-xs text-gray-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-white">InsightForge</span>
            <span>—</span>
            <span>Autonomous AI Data Analyst</span>
          </div>
          <div className="flex items-center gap-6">
            <button onClick={() => onOpenAuth('login')} className="hover:text-gray-300 transition-colors">Sign In</button>
            <button onClick={() => onOpenAuth('register')} className="hover:text-gray-300 transition-colors">Register</button>
            <a
              href="https://github.com/Manan0p/AI-Data-Analyst"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-gray-300 transition-colors"
            >
              GitHub Repo
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
