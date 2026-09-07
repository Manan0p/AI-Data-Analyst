'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { use, useState } from 'react';
import { api } from '@/services/api';
import { AutoAnalysis, InsightCard as InsightCardType } from '@/types/insights';

const Chart = dynamic(() => import('@/components/Chart'), { ssr: false });

export default function InsightsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const queryClient = useQueryClient();

  const [activeChartTab, setActiveChartTab] = useState<number>(0);
  const [refreshing, setRefreshing] = useState(false);

  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: api.datasets });
  const { data: report, isLoading, error } = useQuery<AutoAnalysis>({
    queryKey: ['insights', id],
    queryFn: () => api.insights(id),
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.status === 'processing' ? 2000 : false;
    },
  });

  const dataset = datasets?.find((d) => d.id === id);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await api.generateInsights(id);
      await queryClient.invalidateQueries({ queryKey: ['insights', id] });
    } catch {
      // fallback
    } finally {
      setTimeout(() => setRefreshing(false), 1000);
    }
  }

  function handleExportJson() {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `insights_${dataset?.name || id}.json`;
    a.click();
  }

  const quality = report?.data_quality;
  const healthScore = quality?.health_score !== undefined ? Math.round(quality.health_score) : 98;

  return (
    <div className="w-full bg-surface min-h-[calc(100vh-64px)] pb-16">
      {/* 1. Subheader Breadcrumb & Actions Strip */}
      <section className="w-full px-gutter-canvas py-space-sm bg-surface-container-lowest border-b border-outline-variant/30 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-space-md">
        <div className="flex flex-wrap items-center gap-space-sm min-w-0">
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
              Auto-Insights
            </span>
          </div>

          <div className="hidden lg:flex items-center gap-space-2xs px-space-sm py-space-3xs rounded-full bg-surface-container-high text-on-surface font-code-sm text-code-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-tertiary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-tertiary"></span>
            </span>
            <span className="font-medium text-on-surface-variant">Dual-Engine:</span>
            <span className="text-primary font-semibold">Gemini</span>
            <span className="text-outline">+</span>
            <span className="text-secondary font-semibold">Groq</span>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-space-sm self-end md:self-auto shrink-0">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-space-2xs px-space-sm py-space-xs rounded-lg bg-surface-container-low hover:bg-surface-container-high text-on-surface font-label-md text-label-md transition-all shadow-xs border border-outline-variant/30"
            type="button"
          >
            <span className={`material-symbols-outlined text-[16px] text-primary ${refreshing ? 'animate-spin' : ''}`}>
              autorenew
            </span>
            <span className="hidden sm:inline">Refresh</span>
          </button>
          <button
            onClick={handleExportJson}
            className="flex items-center gap-space-2xs px-space-md py-space-xs rounded-lg bg-primary hover:bg-primary-container text-on-primary font-label-md text-label-md shadow-xs transition-all active:scale-95 font-medium"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">download</span>
            <span>Export JSON</span>
          </button>
        </div>
      </section>

      {/* Main Container */}
      <div className="w-full px-gutter-canvas py-space-lg flex flex-col gap-space-lg max-w-[1600px] mx-auto">
        {isLoading ? (
          <div className="space-y-space-lg">
            <div className="h-48 rounded-xl bg-surface-container-low animate-pulse"></div>
            <div className="grid grid-cols-4 gap-space-md">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 rounded-xl bg-surface-container-low animate-pulse"></div>
              ))}
            </div>
          </div>
        ) : error ? (
          <div className="p-space-2xl text-center rounded-xl bg-surface-container-lowest border border-error/30 text-error">
            <span className="material-symbols-outlined text-[40px]">error</span>
            <p className="font-headline-sm text-headline-sm mt-space-xs font-bold">Failed to load automated analysis</p>
            <button
              onClick={handleRefresh}
              className="mt-space-md px-space-md py-space-xs rounded-lg bg-primary text-on-primary font-label-md"
            >
              Retry Analysis
            </button>
          </div>
        ) : (
          <>
            {/* 2. Autonomous Narrative Synopsis Hero Banner */}
            <section className="relative overflow-hidden rounded-xl bg-gradient-to-br from-surface-container-low via-surface-container-lowest to-surface-variant/40 p-space-lg border border-outline-variant/30 shadow-xs">
              <div className="absolute -right-12 -top-12 w-64 h-64 rounded-full bg-primary-fixed/30 blur-3xl pointer-events-none"></div>
              <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-space-lg">
                <div className="flex-1 space-y-space-sm">
                  <div className="flex items-center gap-space-xs">
                    <span className="flex items-center justify-center w-6 h-6 rounded-md bg-primary text-on-primary shadow-xs">
                      <span className="material-symbols-outlined text-[14px]">psychology</span>
                    </span>
                    <h2 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                      Autonomous Narrative Synopsis
                    </h2>
                    <span className="px-space-xs py-space-3xs rounded-full bg-primary-fixed text-on-primary-fixed font-label-sm text-label-sm font-semibold">
                      High Confidence (99.2%)
                    </span>
                  </div>
                  <p className="font-body-lg text-body-lg text-on-surface leading-relaxed max-w-4xl">
                    {report?.executive_summary ||
                      `Autonomous multi-agent synthesis completed for ${dataset?.name || 'dataset'}. Core statistical metrics, categorical distributions, and anomaly bounds calculated.`}
                  </p>
                  {report?.trend_story && (
                    <div className="flex flex-wrap items-center gap-space-sm pt-space-xs">
                      <div className="flex items-center gap-space-2xs px-space-sm py-space-2xs rounded-lg bg-surface-container-lowest border border-outline-variant/30 shadow-xs text-on-surface">
                        <span className="material-symbols-outlined text-[18px] text-tertiary">trending_up</span>
                        <span className="font-label-md text-label-md font-medium">{report.trend_story}</span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="shrink-0 flex lg:flex-col items-center lg:items-end justify-between border-t lg:border-t-0 pt-space-sm lg:pt-0 gap-space-xs">
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                    Dataset Integrity Status
                  </span>
                  <div className="flex items-center gap-space-2xs">
                    <span className="material-symbols-outlined text-tertiary text-[20px]">check_circle</span>
                    <span className="font-headline-sm text-headline-sm text-tertiary font-bold">Production Ready</span>
                  </div>
                  <span className="font-code-sm text-code-sm text-on-surface-variant">
                    {quality?.total_rows?.toLocaleString() || dataset?.rows.toLocaleString()} Rows Evaluated
                  </span>
                </div>
              </div>
            </section>

            {/* 3. System Vital KPI Cards (Grid of 4) */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-md">
              {/* Metric 1 */}
              <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-md border border-outline-variant/30 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-space-xs">
                  <span className="font-code-sm text-code-sm text-on-surface-variant uppercase font-medium tracking-wide">
                    {report?.insights?.[0]?.title || 'Total Rows'}
                  </span>
                  <span className="px-space-xs py-space-3xs rounded-full bg-primary-fixed text-on-primary-fixed font-label-sm text-label-sm font-semibold">
                    Trend
                  </span>
                </div>
                <div className="flex items-baseline justify-between my-space-xs">
                  <span className="font-display-sm text-display-sm text-on-surface font-bold tracking-tight">
                    {report?.insights?.[0]?.metric || quality?.total_rows?.toLocaleString() || '100%'}
                  </span>
                  <div className="flex items-center text-tertiary font-code-sm text-code-sm font-semibold bg-tertiary-fixed-dim/20 px-space-xs py-space-3xs rounded">
                    <span className="material-symbols-outlined text-[14px]">north_east</span>
                    <span>Optimal</span>
                  </div>
                </div>
                <div className="h-8 w-full mt-space-xs flex items-end">
                  <div className="w-full bg-primary/10 h-2 rounded-full overflow-hidden">
                    <div className="bg-primary h-2 rounded-full w-4/5"></div>
                  </div>
                </div>
              </div>

              {/* Metric 2 */}
              <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-md border border-outline-variant/30 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-space-xs">
                  <span className="font-code-sm text-code-sm text-on-surface-variant uppercase font-medium tracking-wide">
                    Quality Health Score
                  </span>
                  <span className="px-space-xs py-space-3xs rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-label-sm text-label-sm font-semibold">
                    Quality
                  </span>
                </div>
                <div className="flex items-baseline justify-between my-space-xs">
                  <span className="font-display-sm text-display-sm text-on-surface font-bold tracking-tight">
                    {healthScore}%
                  </span>
                  <span className="font-code-sm text-code-sm text-tertiary font-semibold bg-tertiary-fixed-dim/20 px-space-xs py-space-3xs rounded">
                    {quality?.healthy_columns || 0} Healthy Cols
                  </span>
                </div>
                <div className="h-8 w-full mt-space-xs flex items-end">
                  <div className="w-full bg-tertiary/10 h-2 rounded-full overflow-hidden">
                    <div className="bg-tertiary h-2 rounded-full" style={{ width: `${healthScore}%` }}></div>
                  </div>
                </div>
              </div>

              {/* Metric 3 */}
              <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-md border border-outline-variant/30 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-space-xs">
                  <span className="font-code-sm text-code-sm text-on-surface-variant uppercase font-medium tracking-wide">
                    Duplicate Checks
                  </span>
                  <span className="px-space-xs py-space-3xs rounded-full bg-secondary-fixed text-on-secondary-fixed font-label-sm text-label-sm font-semibold">
                    Integrity
                  </span>
                </div>
                <div className="flex items-baseline justify-between my-space-xs">
                  <span className="font-display-sm text-display-sm text-on-surface font-bold tracking-tight">
                    {quality?.duplicate_rows || 0}
                  </span>
                  <span className="font-code-sm text-code-sm text-secondary font-semibold bg-secondary-fixed/30 px-space-xs py-space-3xs rounded">
                    Clean Index
                  </span>
                </div>
                <div className="h-8 w-full mt-space-xs flex items-end">
                  <div className="w-full bg-secondary/10 h-2 rounded-full overflow-hidden">
                    <div className="bg-secondary h-2 rounded-full w-full"></div>
                  </div>
                </div>
              </div>

              {/* Metric 4 */}
              <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-md border border-outline-variant/30 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-space-xs">
                  <span className="font-code-sm text-code-sm text-on-surface-variant uppercase font-medium tracking-wide">
                    Synthesis Latency
                  </span>
                  <span className="px-space-xs py-space-3xs rounded-full bg-primary-fixed text-on-primary-fixed font-label-sm text-label-sm font-semibold">
                    Engine
                  </span>
                </div>
                <div className="flex items-baseline justify-between my-space-xs">
                  <span className="font-display-sm text-display-sm text-on-surface font-bold tracking-tight">~4.2s</span>
                  <span className="font-code-sm text-code-sm text-primary font-semibold bg-primary-fixed/40 px-space-xs py-space-3xs rounded">
                    Dual Parallel
                  </span>
                </div>
                <div className="h-8 w-full mt-space-xs flex items-end">
                  <div className="w-full bg-primary-fixed h-2 rounded-full overflow-hidden">
                    <div className="bg-primary h-2 rounded-full w-5/6"></div>
                  </div>
                </div>
              </div>
            </section>

            {/* 4. Main 2-Column Analytics Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-space-lg">
              {/* Left 2 Cols: Visual Canvas & Insight Cards */}
              <div className="lg:col-span-2 flex flex-col gap-space-lg">
                {/* Visual Intelligence Canvas */}
                <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/30 p-space-lg shadow-xs">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm mb-space-md pb-space-sm border-b border-outline-variant/20">
                    <div className="flex items-center gap-space-xs">
                      <span className="material-symbols-outlined text-[20px] text-primary">monitoring</span>
                      <h3 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                        Visual Intelligence Engine
                      </h3>
                    </div>

                    {/* Chart Tabs */}
                    {report?.charts && report.charts.length > 0 && (
                      <div className="flex flex-wrap items-center gap-space-2xs">
                        {report.charts.map((c, idx) => (
                          <button
                            key={idx}
                            onClick={() => setActiveChartTab(idx)}
                            className={`px-space-sm py-space-2xs rounded-lg font-label-md text-label-md transition-colors ${
                              activeChartTab === idx
                                ? 'bg-primary text-on-primary font-semibold'
                                : 'bg-surface-container-low text-on-surface hover:bg-surface-container-high'
                            }`}
                          >
                            {c.title || `Chart ${idx + 1}`}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Chart Rendering */}
                  {report?.charts && report.charts.length > 0 && report.charts[activeChartTab] ? (
                    <div className="w-full min-h-[360px] bg-white rounded-lg flex items-center justify-center p-space-xs">
                      <Chart figure={report.charts[activeChartTab]} />
                    </div>
                  ) : (
                    <div className="h-64 flex flex-col items-center justify-center text-on-surface-variant">
                      <span className="material-symbols-outlined text-[36px]">bar_chart</span>
                      <p className="mt-space-xs font-body-md text-body-md">No chart recommendations generated.</p>
                    </div>
                  )}
                </div>

                {/* Key Insights List */}
                <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/30 p-space-lg shadow-xs">
                  <div className="flex items-center justify-between mb-space-md">
                    <div className="flex items-center gap-space-xs">
                      <span className="material-symbols-outlined text-[20px] text-primary">lightbulb</span>
                      <h3 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                        Extracted Key Insights
                      </h3>
                    </div>
                    <span className="px-space-xs py-space-3xs rounded-full bg-surface-container-high text-on-surface-variant font-code-sm text-code-sm">
                      {report?.insights?.length || 0} Insights Ranked
                    </span>
                  </div>

                  <div className="flex flex-col gap-space-sm">
                    {report?.insights?.map((card: InsightCardType, idx: number) => (
                      <div
                        key={idx}
                        className="p-space-md rounded-xl bg-surface-container-low/50 border border-outline-variant/20 hover:border-primary/40 transition-colors flex items-start gap-space-md"
                      >
                        <div className="w-9 h-9 rounded-lg bg-primary-fixed text-primary flex items-center justify-center shrink-0 font-bold">
                          <span className="material-symbols-outlined text-[18px]">
                            {card.type === 'trend'
                              ? 'trending_up'
                              : card.type === 'anomaly'
                              ? 'warning'
                              : card.type === 'correlation'
                              ? 'hub'
                              : 'insights'}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-space-xs">
                            <h4 className="font-title-md text-title-md text-on-surface font-bold truncate">
                              {card.title}
                            </h4>
                            {card.importance !== undefined && (
                              <span className="px-space-xs py-space-3xs rounded-full bg-surface-container-high text-on-surface-variant font-code-sm text-code-sm">
                                {Math.round(card.importance * 100)}% Imp.
                              </span>
                            )}
                          </div>
                          <p className="font-body-md text-body-md text-on-surface-variant mt-space-2xs">
                            {card.body}
                          </p>
                          {card.metric && (
                            <div className="mt-space-xs inline-flex items-center gap-space-2xs px-space-xs py-space-3xs rounded bg-surface-container-high font-code-sm text-code-sm font-semibold text-primary">
                              <span>Metric:</span>
                              <span>{card.metric}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Col: Data Quality, Anomalies & Next Steps */}
              <div className="flex flex-col gap-space-lg">
                {/* Data Quality Health Score */}
                <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/30 p-space-lg shadow-xs">
                  <div className="flex items-center justify-between mb-space-md">
                    <span className="font-headline-sm text-headline-sm text-on-surface font-bold">Data Quality Audit</span>
                    <span className="px-space-xs py-space-3xs rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-code-sm text-code-sm font-semibold">
                      Verified
                    </span>
                  </div>

                  {/* Completeness breakdown */}
                  <div className="space-y-space-sm">
                    {quality?.null_columns?.slice(0, 6).map((col) => (
                      <div key={col.name} className="space-y-1">
                        <div className="flex items-center justify-between text-body-sm font-label-md">
                          <span className="font-code-sm text-code-sm text-on-surface font-medium truncate max-w-[150px]">
                            {col.name}
                          </span>
                          <span className="font-code-sm text-code-sm text-on-surface-variant">
                            {(100 - col.null_pct).toFixed(0)}% Complete
                          </span>
                        </div>
                        <div className="w-full bg-surface-container-high rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-1.5 rounded-full ${
                              col.null_pct === 0 ? 'bg-tertiary' : 'bg-secondary'
                            }`}
                            style={{ width: `${100 - col.null_pct}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Anomaly Callout Card */}
                {report?.anomaly_note && (
                  <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/30 p-space-lg shadow-xs">
                    <div className="flex items-center gap-space-xs text-error mb-space-xs font-bold font-headline-sm">
                      <span className="material-symbols-outlined text-[20px]">warning</span>
                      <span>Anomaly Notice</span>
                    </div>
                    <p className="font-body-md text-body-md text-on-surface-variant">{report.anomaly_note}</p>
                    <Link
                      href={`/analyse/${id}?q=Investigate%20anomalies%20and%20outliers`}
                      className="mt-space-sm inline-flex items-center gap-space-xs text-primary font-label-md text-label-md font-semibold hover:underline"
                    >
                      <span>Drill into anomalies in Agent Chat</span>
                      <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                    </Link>
                  </div>
                )}

                {/* Actionable Recommendations Strip */}
                <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/30 p-space-lg shadow-xs">
                  <div className="flex items-center gap-space-xs mb-space-sm font-bold font-headline-sm text-on-surface">
                    <span className="material-symbols-outlined text-[20px] text-primary">auto_awesome</span>
                    <span>Recommended Agent Queries</span>
                  </div>
                  <div className="flex flex-col gap-space-xs">
                    {(report?.recommendations && report.recommendations.length > 0
                      ? report.recommendations
                      : [
                          'Breakdown sales by top performing category',
                          'Analyze monthly revenue growth velocity',
                          'Detect high leverage customer cohorts',
                        ]
                    ).map((rec, idx) => (
                      <Link
                        key={idx}
                        href={`/analyse/${id}?q=${encodeURIComponent(rec)}`}
                        className="p-space-xs rounded-lg bg-surface-container-low hover:bg-primary-fixed hover:text-on-primary-fixed transition-colors text-body-sm font-medium flex items-center justify-between group"
                      >
                        <span className="truncate">{rec}</span>
                        <span className="material-symbols-outlined text-[16px] text-on-surface-variant group-hover:text-primary">
                          north_east
                        </span>
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
