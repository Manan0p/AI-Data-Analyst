'use client';

import React, { useState } from 'react';
import Link from 'next/link';

interface LandingPageProps {
  onOpenAuth: (mode?: 'login' | 'register') => void;
}

export function LandingPage({ onOpenAuth }: LandingPageProps) {
  const [activeDemoTab, setActiveDemoTab] = useState<'insights' | 'chat' | 'sql' | 'quality'>('insights');

  return (
    <div className="min-h-screen bg-surface text-on-surface font-body-md relative overflow-x-hidden antialiased selection:bg-primary-fixed selection:text-on-primary-fixed">
      {/* Dynamic Background Ambient Gradients */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-[800px] h-[500px] rounded-full bg-gradient-to-br from-primary-fixed/60 via-surface-variant/30 to-transparent blur-3xl opacity-70" />
        <div className="absolute top-[35%] -left-32 w-[500px] h-[500px] rounded-full bg-secondary-fixed/40 blur-3xl opacity-50" />
        <div className="absolute top-[65%] -right-32 w-[600px] h-[600px] rounded-full bg-tertiary-fixed/30 blur-3xl opacity-40" />
      </div>

      {/* Top Navbar */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-surface-container-lowest/90 border-b border-outline-variant/30 shadow-[0_1px_8px_rgba(0,0,0,0.03)]">
        <div className="max-w-7xl mx-auto px-gutter-canvas h-16 flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-space-sm">
            <div className="w-8 h-8 rounded-lg bg-primary-container text-white flex items-center justify-center shadow-xs">
              <span className="material-symbols-outlined text-[20px]">insights</span>
            </div>
            <div className="flex items-center gap-space-xs">
              <span className="font-headline-sm text-headline-sm font-bold text-on-surface tracking-tight">
                InsightForge
              </span>
              <span className="hidden sm:inline-flex px-space-xs py-space-3xs rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm uppercase">
                Autonomous AI Studio
              </span>
            </div>
          </div>

          {/* Navigation links */}
          <nav className="hidden md:flex items-center gap-space-lg font-label-md text-label-md text-on-surface-variant">
            <a href="#features" className="hover:text-primary transition-colors">Features</a>
            <a href="#demo" className="hover:text-primary transition-colors">Live Demo</a>
            <a href="#architecture" className="hover:text-primary transition-colors">Architecture</a>
            <a href="#security" className="hover:text-primary transition-colors">Security</a>
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-space-sm">
            <div className="hidden xl:flex items-center gap-space-xs px-space-sm py-space-2xs rounded-full bg-primary-fixed text-on-primary-fixed font-code-sm text-code-sm shadow-xs">
              <span className="material-symbols-outlined text-[14px] text-primary animate-pulse">bolt</span>
              <span className="font-semibold">Dual-Core AI</span>
            </div>
            <button
              onClick={() => onOpenAuth('login')}
              className="px-space-md py-space-xs rounded-lg text-label-md font-medium text-on-surface hover:bg-surface-container-low transition-all"
            >
              Sign In
            </button>
            <button
              onClick={() => onOpenAuth('register')}
              className="inline-flex items-center gap-space-xs px-space-md py-space-xs rounded-lg bg-primary hover:bg-primary-container text-on-primary font-label-md text-label-md font-semibold transition-all shadow-xs active:scale-95"
            >
              <span>Get Started Free</span>
              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-gutter-canvas pt-space-3xl pb-space-2xl text-center flex flex-col items-center">
        {/* Top Status Pill */}
        <div className="inline-flex items-center gap-space-xs px-space-md py-space-2xs rounded-full bg-surface-container-lowest border border-outline-variant/40 shadow-xs mb-space-lg">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-tertiary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-tertiary"></span>
          </span>
          <span className="font-label-md text-label-md text-on-surface font-semibold">
            Self-Correcting Multi-Agent Swarm
          </span>
          <span className="text-outline-variant font-code-sm">·</span>
          <span className="font-code-sm text-code-sm text-primary font-semibold">
            Gemini + Groq
          </span>
        </div>

        {/* Hero Title */}
        <h1 className="font-display-lg text-4xl sm:text-5xl lg:text-6xl font-extrabold text-on-surface tracking-tight max-w-4xl leading-tight">
          Autonomous Data Intelligence. <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-primary via-primary-container to-secondary bg-clip-text text-transparent">
            Instant Answers in Seconds.
          </span>
        </h1>

        {/* Hero Subtitle */}
        <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mt-space-md leading-relaxed">
          Upload raw CSV, Excel, or Parquet datasets and get automated executive briefings, sandboxed DuckDB SQL execution, AST-whitelisted Pandas transformations, and interactive Plotly figures with zero manual configuration.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-space-sm mt-space-xl">
          <button
            onClick={() => onOpenAuth('register')}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-space-xs px-space-xl py-space-sm rounded-xl bg-primary hover:bg-primary-container text-on-primary font-headline-sm text-headline-sm font-bold shadow-md hover:shadow-lg transition-all active:scale-95"
          >
            <span className="material-symbols-outlined text-[20px]">rocket_launch</span>
            <span>Launch Workspace Free</span>
          </button>
          <button
            onClick={() => onOpenAuth('login')}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-space-xs px-space-lg py-space-sm rounded-xl bg-surface-container-lowest hover:bg-surface-container-low border border-outline-variant/40 text-on-surface font-headline-sm text-headline-sm font-semibold transition-all shadow-xs"
          >
            <span>Sign In to Existing Account</span>
          </button>
        </div>

        {/* Feature Badges Strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-space-sm w-full max-w-4xl mt-space-2xl text-left">
          <div className="p-space-md rounded-xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-primary text-[24px]">speed</span>
            <div>
              <div className="font-title-md text-title-md font-bold text-on-surface">&lt;4s Parallel</div>
              <div className="font-body-sm text-body-sm text-on-surface-variant">Dual-Engine Latency</div>
            </div>
          </div>
          <div className="p-space-md rounded-xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-tertiary text-[24px]">verified</span>
            <div>
              <div className="font-title-md text-title-md font-bold text-on-surface">100% In-Memory</div>
              <div className="font-body-sm text-body-sm text-on-surface-variant">DuckDB SQL Isolation</div>
            </div>
          </div>
          <div className="p-space-md rounded-xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-secondary text-[24px]">monitoring</span>
            <div>
              <div className="font-title-md text-title-md font-bold text-on-surface">Auto-Charts</div>
              <div className="font-body-sm text-body-sm text-on-surface-variant">Dynamic Plotly Canvas</div>
            </div>
          </div>
          <div className="p-space-md rounded-xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-primary text-[24px]">troubleshoot</span>
            <div>
              <div className="font-title-md text-title-md font-bold text-on-surface">Auto-Anomalies</div>
              <div className="font-body-sm text-body-sm text-on-surface-variant">Isolation Forest Scan</div>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Live Demo Preview Section */}
      <section id="demo" className="relative z-10 max-w-7xl mx-auto px-gutter-canvas py-space-2xl">
        <div className="text-center mb-space-xl">
          <span className="font-label-sm text-label-sm uppercase tracking-wider text-primary font-bold">
            Interactive Agent Simulation
          </span>
          <h2 className="font-display-sm text-display-sm font-bold text-on-surface mt-space-3xs">
            See the Autonomous Swarm in Action
          </h2>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-xl mx-auto mt-space-xs">
            Toggle through live agent workflows to see how InsightForge turns raw questions into validated calculations and dynamic visuals.
          </p>
        </div>

        {/* Demo Window Container */}
        <div className="rounded-2xl bg-surface-container-lowest border border-outline-variant/40 shadow-xl overflow-hidden max-w-5xl mx-auto">
          {/* Top Window Bar */}
          <div className="px-space-md py-space-sm bg-surface-container-low border-b border-outline-variant/30 flex flex-wrap items-center justify-between gap-space-sm">
            <div className="flex items-center gap-space-xs">
              <span className="w-3 h-3 rounded-full bg-error/70"></span>
              <span className="w-3 h-3 rounded-full bg-secondary-container"></span>
              <span className="w-3 h-3 rounded-full bg-tertiary-fixed-dim"></span>
              <span className="ml-2 font-code-sm text-code-sm text-on-surface-variant">
                insightforge_session / Q3_Sales_Report.csv
              </span>
            </div>

            {/* Demo Tabs */}
            <div className="flex items-center gap-space-2xs">
              <button
                onClick={() => setActiveDemoTab('insights')}
                className={`px-space-sm py-1 rounded-lg font-label-md text-label-md transition-colors ${
                  activeDemoTab === 'insights'
                    ? 'bg-primary text-on-primary font-semibold'
                    : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                }`}
              >
                Executive Insights
              </button>
              <button
                onClick={() => setActiveDemoTab('chat')}
                className={`px-space-sm py-1 rounded-lg font-label-md text-label-md transition-colors ${
                  activeDemoTab === 'chat'
                    ? 'bg-primary text-on-primary font-semibold'
                    : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                }`}
              >
                Multi-Agent Chat
              </button>
              <button
                onClick={() => setActiveDemoTab('sql')}
                className={`px-space-sm py-1 rounded-lg font-label-md text-label-md transition-colors ${
                  activeDemoTab === 'sql'
                    ? 'bg-primary text-on-primary font-semibold'
                    : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                }`}
              >
                Sandboxed SQL
              </button>
              <button
                onClick={() => setActiveDemoTab('quality')}
                className={`px-space-sm py-1 rounded-lg font-label-md text-label-md transition-colors ${
                  activeDemoTab === 'quality'
                    ? 'bg-primary text-on-primary font-semibold'
                    : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                }`}
              >
                Quality Audit
              </button>
            </div>
          </div>

          {/* Demo Content Body */}
          <div className="p-space-lg bg-surface min-h-[380px] flex items-center justify-center">
            {activeDemoTab === 'insights' && (
              <div className="w-full space-y-space-md">
                <div className="p-space-md rounded-xl bg-gradient-to-br from-surface-container-low via-surface-container-lowest to-surface-variant/30 border border-outline-variant/30">
                  <div className="flex items-center gap-space-xs mb-space-2xs">
                    <span className="material-symbols-outlined text-primary text-[20px]">psychology</span>
                    <span className="font-headline-sm text-headline-sm font-bold text-on-surface">
                      Autonomous Narrative Synopsis
                    </span>
                    <span className="px-space-xs py-space-3xs rounded-full bg-primary-fixed text-on-primary-fixed font-label-sm text-label-sm font-semibold">
                      99.2% Confidence
                    </span>
                  </div>
                  <p className="font-body-md text-body-md text-on-surface">
                    Net revenue closed at <strong className="text-primary font-bold">$1.42M (+14.2% vs target)</strong>, driven predominantly by EMEA enterprise contract conversions. Operating margins reached an optimal <strong className="text-tertiary font-bold">28.4%</strong> with 0 critical schema corruptions.
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-space-md">
                  <div className="p-space-md rounded-xl bg-surface-container-lowest border border-outline-variant/30">
                    <span className="font-code-sm text-code-sm text-on-surface-variant uppercase">Total Sales</span>
                    <div className="font-display-sm text-display-sm font-bold text-on-surface mt-1">$1.42M</div>
                    <span className="font-code-sm text-code-sm text-tertiary font-semibold">+24.8% MoM</span>
                  </div>
                  <div className="p-space-md rounded-xl bg-surface-container-lowest border border-outline-variant/30">
                    <span className="font-code-sm text-code-sm text-on-surface-variant uppercase">Quality Health</span>
                    <div className="font-display-sm text-display-sm font-bold text-on-surface mt-1">98.8%</div>
                    <span className="font-code-sm text-code-sm text-tertiary font-semibold">Zero Null Rows</span>
                  </div>
                  <div className="p-space-md rounded-xl bg-surface-container-lowest border border-outline-variant/30">
                    <span className="font-code-sm text-code-sm text-on-surface-variant uppercase">Ingestion Speed</span>
                    <div className="font-display-sm text-display-sm font-bold text-on-surface mt-1">~4.2s</div>
                    <span className="font-code-sm text-code-sm text-primary font-semibold">Parallel Dual-LLM</span>
                  </div>
                </div>
              </div>
            )}

            {activeDemoTab === 'chat' && (
              <div className="w-full space-y-space-md">
                <div className="flex justify-end">
                  <div className="bg-primary text-on-primary px-space-md py-space-sm rounded-2xl rounded-tr-sm font-body-md text-body-md max-w-md">
                    Which product category has the highest average margin?
                  </div>
                </div>
                <div className="p-space-md rounded-xl bg-surface-container-lowest border border-outline-variant/30 space-y-space-xs">
                  <div className="flex items-center justify-between border-b border-outline-variant/20 pb-1">
                    <div className="flex items-center gap-space-xs">
                      <span className="material-symbols-outlined text-primary text-[18px]">psychology</span>
                      <span className="font-title-md text-title-md font-bold text-on-surface">Synthesis Result</span>
                    </div>
                    <span className="px-space-xs py-space-3xs rounded-full bg-surface-container-high text-on-surface-variant font-code-sm text-code-sm font-semibold">
                      Executed in 142ms
                    </span>
                  </div>
                  <p className="font-body-md text-body-md text-on-surface">
                    <strong>Enterprise Software & Cloud Licenses</strong> yields the highest average margin at <strong className="text-primary font-bold">44.8%</strong>, outperforming Hardware (21.4%) and Consulting (29.1%).
                  </p>
                  <div className="p-space-xs rounded bg-surface-container-low font-code-sm text-code-sm text-primary font-semibold">
                    SQL: SELECT category, AVG(margin) AS avg_margin FROM dataset GROUP BY category ORDER BY avg_margin DESC LIMIT 5
                  </div>
                </div>
              </div>
            )}

            {activeDemoTab === 'sql' && (
              <div className="w-full bg-slate-950 text-slate-100 rounded-xl p-space-lg font-code-sm text-code-sm space-y-space-sm">
                <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-space-xs">
                  <span className="uppercase font-bold tracking-wider">DuckDB In-Memory Execution</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/40">Read-Only Safe</span>
                </div>
                <pre className="text-emerald-300 overflow-x-auto">
                  <code>
{`SELECT 
    region,
    COUNT(order_id) AS total_orders,
    SUM(revenue) AS total_revenue,
    ROUND(AVG(customer_satisfaction), 2) AS csat
FROM sales_q3
GROUP BY region
ORDER BY total_revenue DESC;`}
                  </code>
                </pre>
                <div className="text-slate-400 text-xs">Returned 4 rows in 18ms. AST Whitelist: No write / drop operations permitted.</div>
              </div>
            )}

            {activeDemoTab === 'quality' && (
              <div className="w-full space-y-space-sm">
                <div className="flex items-center justify-between">
                  <span className="font-headline-sm text-headline-sm font-bold text-on-surface">Data Quality & Schema Audit</span>
                  <span className="px-space-xs py-space-3xs rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-code-sm text-code-sm font-semibold">
                    Verified (100% Score)
                  </span>
                </div>
                <div className="space-y-space-xs">
                  {[
                    { name: 'customer_id', complete: 100 },
                    { name: 'transaction_date', complete: 100 },
                    { name: 'gross_revenue', complete: 100 },
                    { name: 'shipping_address', complete: 98 },
                  ].map((col) => (
                    <div key={col.name} className="space-y-1">
                      <div className="flex justify-between text-xs font-code-sm">
                        <span className="font-medium text-on-surface">{col.name}</span>
                        <span className="text-on-surface-variant">{col.complete}% Complete</span>
                      </div>
                      <div className="w-full bg-surface-container-high rounded-full h-2 overflow-hidden">
                        <div className="bg-tertiary h-2 rounded-full" style={{ width: `${col.complete}%` }}></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Feature Grid Section */}
      <section id="features" className="relative z-10 max-w-7xl mx-auto px-gutter-canvas py-space-3xl border-t border-outline-variant/30">
        <div className="text-center mb-space-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-wider text-primary font-bold">
            Core Architecture & Capabilities
          </span>
          <h2 className="font-display-sm text-display-sm font-bold text-on-surface mt-space-3xs">
            Engineered for Quantitative Precision
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-space-lg">
          {/* Feature 1 */}
          <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-xl bg-primary-fixed text-primary flex items-center justify-center font-bold mb-space-md">
              <span className="material-symbols-outlined text-[26px]">bolt</span>
            </div>
            <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
              Dual-Model Parallel Swarm
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant mt-space-xs">
              Gemini calculates structured queries while Groq crafts narrative synthesis simultaneously in &lt;4s.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-xl bg-secondary-fixed text-secondary flex items-center justify-center font-bold mb-space-md">
              <span className="material-symbols-outlined text-[26px]">terminal</span>
            </div>
            <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
              Sandboxed DuckDB & Pandas
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant mt-space-xs">
              Executes read-only in-memory SQL queries and AST-whitelisted Python transformations with zero external network leakage.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-xl bg-tertiary-fixed text-tertiary flex items-center justify-center font-bold mb-space-md">
              <span className="material-symbols-outlined text-[26px]">monitoring</span>
            </div>
            <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
              Dynamic Visual Intelligence
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant mt-space-xs">
              Auto-generates Plotly charts (histograms, categorical distributions, correlation heatmaps, and time series curves).
            </p>
          </div>

          {/* Feature 4 */}
          <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-xl bg-primary-fixed text-primary flex items-center justify-center font-bold mb-space-md">
              <span className="material-symbols-outlined text-[26px]">troubleshoot</span>
            </div>
            <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
              Isolation Forest Outliers
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant mt-space-xs">
              Automatically isolates multidimensional statistical anomalies with human-readable variance explanations.
            </p>
          </div>

          {/* Feature 5 */}
          <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-xl bg-tertiary-fixed text-tertiary flex items-center justify-center font-bold mb-space-md">
              <span className="material-symbols-outlined text-[26px]">verified_user</span>
            </div>
            <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
              Data Quality Audit Engine
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant mt-space-xs">
              Scores dataset completeness, identifies missing cell percentages per column, and checks duplicate rows on upload.
            </p>
          </div>

          {/* Feature 6 */}
          <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-xl bg-secondary-fixed text-secondary flex items-center justify-center font-bold mb-space-md">
              <span className="material-symbols-outlined text-[26px]">schema</span>
            </div>
            <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
              Self-Correcting Graph
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant mt-space-xs">
              Powered by LangGraph agent cycles that automatically catch syntax or runtime errors, re-planning queries on the fly.
            </p>
          </div>
        </div>
      </section>

      {/* Security Strip */}
      <section id="security" className="relative z-10 max-w-7xl mx-auto px-gutter-canvas py-space-2xl border-t border-outline-variant/30">
        <div className="rounded-2xl bg-surface-container-lowest border border-outline-variant/30 p-space-2xl flex flex-col lg:flex-row items-center justify-between gap-space-xl">
          <div className="max-w-xl">
            <span className="font-label-sm text-label-sm uppercase tracking-wider text-tertiary font-bold">
              Enterprise Grade Security
            </span>
            <h3 className="font-headline-lg text-headline-lg font-bold text-on-surface mt-1">
              Zero Data Retention & Isolation
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant mt-space-xs leading-relaxed">
              Your data is processed in ephemeral, isolated worker threads with strict per-user database schemas. All code execution runs in strict read-only sandboxes.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-space-md">
            <div className="px-space-md py-space-sm rounded-xl bg-surface-container-low font-code-sm text-code-sm font-semibold text-on-surface flex items-center gap-space-xs">
              <span className="material-symbols-outlined text-tertiary text-[18px]">lock</span>
              <span>JWT Authentication</span>
            </div>
            <div className="px-space-md py-space-sm rounded-xl bg-surface-container-low font-code-sm text-code-sm font-semibold text-on-surface flex items-center gap-space-xs">
              <span className="material-symbols-outlined text-tertiary text-[18px]">memory</span>
              <span>DuckDB Memory Sandbox</span>
            </div>
            <div className="px-space-md py-space-sm rounded-xl bg-surface-container-low font-code-sm text-code-sm font-semibold text-on-surface flex items-center gap-space-xs">
              <span className="material-symbols-outlined text-tertiary text-[18px]">cloud</span>
              <span>Neon PostgreSQL</span>
            </div>
          </div>
        </div>
      </section>

      {/* Bottom CTA Hero Banner */}
      <section className="relative z-10 max-w-7xl mx-auto px-gutter-canvas py-space-3xl">
        <div className="rounded-3xl bg-gradient-to-br from-primary via-primary-container to-secondary p-space-3xl text-center text-white shadow-2xl relative overflow-hidden">
          <div className="relative z-10 max-w-2xl mx-auto space-y-space-md">
            <h2 className="font-display-lg text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight">
              Ready to automate your data analysis?
            </h2>
            <p className="font-body-lg text-body-lg text-on-primary-container max-w-lg mx-auto">
              Drop your first dataset and experience autonomous multi-agent intelligence in less than 5 seconds.
            </p>
            <div className="pt-space-sm">
              <button
                onClick={() => onOpenAuth('register')}
                className="inline-flex items-center gap-space-xs px-space-2xl py-space-md rounded-xl bg-white text-primary font-headline-sm text-headline-sm font-bold shadow-lg hover:bg-surface-container-low transition-all active:scale-95"
              >
                <span>Launch Free Studio</span>
                <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-outline-variant/30 bg-surface-container-lowest py-space-xl">
        <div className="max-w-7xl mx-auto px-gutter-canvas flex flex-col sm:flex-row items-center justify-between gap-space-md text-on-surface-variant font-body-sm text-body-sm">
          <div className="flex items-center gap-space-xs">
            <span className="font-headline-sm text-headline-sm font-bold text-on-surface">InsightForge</span>
            <span>· Autonomous Multi-Agent AI Data Analyst Platform</span>
          </div>
          <div>
            Built with <strong>FastAPI</strong>, <strong>LangGraph</strong>, <strong>Gemini</strong>, <strong>Groq</strong>, & <strong>Next.js</strong>
          </div>
        </div>
      </footer>
    </div>
  );
}
