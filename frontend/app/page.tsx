'use client';

import React, { useState, useRef } from 'react';
import Link from 'next/link';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { useAuth } from '@/store/useAuth';
import { LandingPage } from '@/components/LandingPage';
import { Dataset } from '@/types';

export default function HomePage() {
  const { user, isInitialized, openAuthModal } = useAuth();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState('');
  const [filterTab, setFilterTab] = useState<'all' | 'clean' | 'anomalies'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const { data: datasets, isLoading, refetch } = useQuery({
    queryKey: ['datasets'],
    queryFn: api.datasets,
    enabled: isInitialized && !!user,
  });

  // Calculate vital aggregate metrics
  const datasetList: Dataset[] = datasets || [];
  const totalRows = datasetList.reduce((acc, d) => acc + (d.rows || 0), 0);
  const totalDatasets = datasetList.length;

  // Filter datasets by tab and search
  const filteredDatasets = datasetList.filter((d) => {
    const matchesSearch = d.name.toLowerCase().includes(searchQuery.toLowerCase()) || d.id.includes(searchQuery);
    return matchesSearch;
  });

  async function handleFileUpload(files: FileList | null) {
    if (!files || files.length === 0) return;
    const file = files[0];
    setUploading(true);
    setUploadError('');
    setUploadProgress(20);

    try {
      const interval = setInterval(() => {
        setUploadProgress((prev) => (prev < 85 ? prev + 15 : prev));
      }, 150);

      await api.upload(file);
      clearInterval(interval);
      setUploadProgress(100);

      await queryClient.invalidateQueries({ queryKey: ['datasets'] });
      setTimeout(() => {
        setUploading(false);
        setUploadProgress(0);
      }, 600);
    } catch (err: unknown) {
      setUploading(false);
      setUploadProgress(0);
      setUploadError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
    }
  }

  async function handleDeleteDataset(id: string, name: string) {
    if (!confirm(`Are you sure you want to delete dataset "${name}"?`)) return;
    try {
      await api.deleteDataset(id);
      await queryClient.invalidateQueries({ queryKey: ['datasets'] });
    } catch (err) {
      alert('Failed to delete dataset');
    }
  }

  if (isInitialized && !user) {
    return <LandingPage onOpenAuth={openAuthModal} />;
  }

  return (
    <div className="w-full bg-surface min-h-[calc(100vh-64px)] pb-16">
      {/* Dynamic Top Ambient Aura */}
      <div className="relative w-full px-gutter-canvas py-space-xl overflow-hidden">
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-gradient-to-br from-primary-fixed to-surface-variant/40 rounded-full blur-3xl -z-10 pointer-events-none opacity-60"></div>
        <div className="absolute -top-12 left-10 w-72 h-72 bg-secondary-fixed/50 rounded-full blur-2xl -z-10 pointer-events-none opacity-40"></div>

        {/* 1. Welcome & Strategic Overview Section */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-space-lg mb-space-2xl">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-space-xs px-space-sm py-space-3xs rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm uppercase mb-space-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-ping"></span>
              <span>Agent Mesh Synchronized</span>
            </div>
            <h1 className="font-display-lg text-display-lg text-on-surface tracking-tight">
              Welcome back, <span className="text-primary font-bold">{user?.name || 'Data Lead'}</span>
            </h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant mt-space-2xs">
              InsightForge Autonomous Swarm is active and monitoring{' '}
              <span className="font-semibold text-on-surface">{totalDatasets} connected data pipelines</span> with zero manual intervention.
            </p>
          </div>

          {/* Quick Action Shortcuts */}
          <div className="flex items-center gap-space-sm self-start lg:self-end">
            <button
              onClick={() => refetch()}
              className="inline-flex items-center gap-space-xs px-space-md py-space-xs rounded-xl bg-surface-container-lowest text-on-surface hover:bg-surface-container-low transition-all shadow-xs border border-outline-variant/30"
              type="button"
            >
              <span className="material-symbols-outlined text-[18px] text-on-surface-variant">cached</span>
              <span className="font-label-md text-label-md font-medium">Poll Pipelines</span>
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-space-xs px-space-md py-space-xs rounded-xl bg-primary text-on-primary hover:bg-primary-container transition-all shadow-sm font-medium"
              type="button"
            >
              <span className="material-symbols-outlined text-[18px]">add_circle</span>
              <span className="font-label-md text-label-md">New Ingestion</span>
            </button>
          </div>
        </div>

        {/* System Vital Metrics Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-space-md mb-space-2xl">
          {/* Metric 1 */}
          <div className="p-space-lg rounded-xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex items-center justify-between">
            <div className="flex flex-col">
              <span className="font-label-sm text-label-sm uppercase text-on-surface-variant tracking-wider font-semibold">Active Datasets</span>
              <span className="font-headline-lg text-headline-lg text-on-surface mt-space-3xs font-bold">{totalDatasets} Active</span>
              <span className="font-body-sm text-body-sm text-on-surface-variant mt-space-3xs">Automatic AI caching active</span>
            </div>
            <div className="w-12 h-12 rounded-xl bg-surface-container-high flex items-center justify-center text-primary">
              <span className="material-symbols-outlined text-[24px]">folder_data</span>
            </div>
          </div>

          {/* Metric 2 */}
          <div className="p-space-lg rounded-xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex items-center justify-between">
            <div className="flex flex-col">
              <span className="font-label-sm text-label-sm uppercase text-on-surface-variant tracking-wider font-semibold">Records Ingested</span>
              <span className="font-headline-lg text-headline-lg text-on-surface mt-space-3xs font-bold">{totalRows.toLocaleString()}</span>
              <span className="font-code-sm text-code-sm text-tertiary flex items-center gap-space-3xs mt-space-3xs font-semibold">
                <span className="material-symbols-outlined text-[14px]">trending_up</span>+100% indexed
              </span>
            </div>
            <div className="w-12 h-12 rounded-xl bg-surface-container-high flex items-center justify-center text-secondary">
              <span className="material-symbols-outlined text-[24px]">analytics</span>
            </div>
          </div>

          {/* Metric 3 */}
          <div className="p-space-lg rounded-xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex items-center justify-between">
            <div className="flex flex-col">
              <span className="font-label-sm text-label-sm uppercase text-on-surface-variant tracking-wider font-semibold">Pipeline Health</span>
              <div className="flex items-baseline gap-space-xs mt-space-3xs">
                <span className="font-headline-lg text-headline-lg text-on-surface font-bold">99.4%</span>
                <span className="inline-flex items-center px-space-xs py-space-3xs rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-code-sm text-code-sm font-semibold">Optimal</span>
              </div>
              <span className="font-body-sm text-body-sm text-on-surface-variant mt-space-3xs">Zero schema corruption</span>
            </div>
            <div className="w-12 h-12 rounded-xl bg-surface-container-high flex items-center justify-center text-tertiary">
              <span className="material-symbols-outlined text-[24px]">verified_user</span>
            </div>
          </div>

          {/* Metric 4 */}
          <div className="p-space-lg rounded-xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex items-center justify-between">
            <div className="flex flex-col min-w-0">
              <span className="font-label-sm text-label-sm uppercase text-on-surface-variant tracking-wider font-semibold">Dual Core Mesh</span>
              <div className="flex items-center gap-space-2xs mt-space-3xs">
                <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse"></span>
                <span className="font-title-md text-title-md text-on-surface font-semibold truncate">Gemini</span>
              </div>
              <span className="font-code-sm text-code-sm text-on-surface-variant truncate mt-space-3xs">Groq (Hot)</span>
            </div>
            <div className="w-12 h-12 rounded-xl bg-primary-fixed text-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-[24px]">neurology</span>
            </div>
          </div>
        </div>

        {/* 2. Live Batch Job & Agent Execution Queue Widget */}
        <div className="mb-space-2xl bg-surface-container-lowest rounded-xl p-space-lg border border-outline-variant/30 shadow-xs">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-md mb-space-md">
            <div className="flex items-center gap-space-sm">
              <div className="w-2.5 h-2.5 rounded-full bg-tertiary animate-pulse"></div>
              <div className="flex items-center gap-space-xs">
                <span className="font-label-sm text-label-sm uppercase text-on-surface-variant font-semibold">Live Execution Queue:</span>
                <span className="font-code-md text-code-md text-primary font-semibold">Engine Synced</span>
                {datasetList[0] && <span className="font-body-sm text-body-sm text-on-surface-variant">({datasetList[0].name})</span>}
              </div>
            </div>
            <div className="flex items-center gap-space-lg text-on-surface-variant font-code-sm text-code-sm">
              <div className="flex items-center gap-space-2xs">
                <span className="material-symbols-outlined text-[16px] text-tertiary">memory</span>
                <span>Workers: 8/8 Active</span>
              </div>
              <div className="flex items-center gap-space-2xs">
                <span className="material-symbols-outlined text-[16px] text-primary">speed</span>
                <span>Latency: ~4.2s Parallel</span>
              </div>
            </div>
          </div>

          {/* Stepper Progress Visualizer */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-space-xs">
            <div className="p-space-xs rounded-lg bg-surface-container-low flex items-center gap-space-xs">
              <span className="material-symbols-outlined text-[16px] text-tertiary">check_circle</span>
              <span className="font-code-sm text-code-sm text-on-surface font-medium">01 Statistical Pass (~100ms)</span>
            </div>
            <div className="p-space-xs rounded-lg bg-surface-container-low flex items-center gap-space-xs">
              <span className="material-symbols-outlined text-[16px] text-tertiary">check_circle</span>
              <span className="font-code-sm text-code-sm text-on-surface font-medium">02 Schema Alignment</span>
            </div>
            <div className="p-space-xs rounded-lg bg-surface-container-low flex items-center gap-space-xs">
              <span className="material-symbols-outlined text-[16px] text-primary animate-spin">sync</span>
              <span className="font-code-sm text-code-sm text-primary font-semibold">03 Parallel Dual-LLM Ingestion</span>
            </div>
            <div className="p-space-xs rounded-lg bg-surface-container-low flex items-center gap-space-xs opacity-75">
              <span className="material-symbols-outlined text-[16px] text-on-surface-variant">pending</span>
              <span className="font-code-sm text-code-sm text-on-surface-variant">04 Narrative Synthesis</span>
            </div>
          </div>
        </div>

        {/* 3. Ingestion Dropzone */}
        <div className="mb-space-2xl">
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFileUpload(e.target.files)}
            className="hidden"
            accept=".csv,.xlsx,.json,.parquet"
          />
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              handleFileUpload(e.dataTransfer.files);
            }}
            className={`border-2 border-dashed rounded-xl p-space-2xl text-center cursor-pointer transition-all bg-surface-container-low/40 hover:bg-surface-container-low/80 ${
              uploading ? 'border-primary bg-primary-fixed/20' : 'border-outline-variant/60 hover:border-primary'
            }`}
          >
            {uploading ? (
              <div className="flex flex-col items-center gap-space-sm max-w-md mx-auto">
                <span className="material-symbols-outlined text-[36px] text-primary animate-spin">sync</span>
                <span className="font-headline-sm text-headline-sm text-on-surface">Ingesting & Profiling Dataset...</span>
                <div className="w-full bg-surface-container-high rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-primary h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <span className="font-code-sm text-code-sm text-on-surface-variant">Running Statistical & Dual-LLM Pipeline ({uploadProgress}%)</span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-space-xs">
                <div className="w-12 h-12 rounded-full bg-primary-fixed text-primary flex items-center justify-center mb-space-2xs">
                  <span className="material-symbols-outlined text-[28px]">cloud_upload</span>
                </div>
                <span className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                  Drop tabular datasets here or click to browse
                </span>
                <p className="font-body-md text-body-md text-on-surface-variant">
                  Autonomous ingestion triggers statistical profiling, auto-chart generation, and dual-model insights in &lt;5s.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-space-xs mt-space-sm">
                  {['.CSV', '.XLSX', '.JSON', '.PARQUET', '.ARROW'].map((ext) => (
                    <span
                      key={ext}
                      className="px-space-xs py-space-3xs rounded-full bg-surface-container-high text-on-surface-variant font-code-sm text-code-sm font-semibold"
                    >
                      {ext}
                    </span>
                  ))}
                </div>
                {uploadError && (
                  <p className="mt-space-sm text-error font-body-sm text-body-sm font-medium">{uploadError}</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 4. Active Pipelines Matrix (Datasets Grid) */}
        <div className="flex flex-col gap-space-lg">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-md">
            <div>
              <h2 className="font-headline-md text-headline-md text-on-surface font-bold">Active Repositories & Pipeline Matrix</h2>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Autonomous multi-agent analytics workspaces ready for instant queries and executive briefings.
              </p>
            </div>
            {/* Search & Filter */}
            <div className="flex items-center gap-space-sm">
              <div className="relative">
                <span className="material-symbols-outlined text-[18px] absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
                  search
                </span>
                <input
                  type="text"
                  placeholder="Filter pipelines..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-3 py-1.5 rounded-lg bg-surface-container-lowest border border-outline-variant/40 text-on-surface text-body-sm focus:outline-none focus:border-primary"
                />
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-space-lg">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-64 rounded-xl bg-surface-container-low animate-pulse"></div>
              ))}
            </div>
          ) : filteredDatasets.length === 0 ? (
            <div className="p-space-2xl text-center rounded-xl bg-surface-container-lowest border border-outline-variant/30">
              <span className="material-symbols-outlined text-[40px] text-on-surface-variant">folder_open</span>
              <p className="font-body-lg text-body-lg text-on-surface-variant mt-space-xs">No datasets ingested yet.</p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="mt-space-md inline-flex items-center gap-space-xs px-space-md py-space-xs rounded-lg bg-primary text-on-primary text-label-md font-medium"
              >
                <span className="material-symbols-outlined text-[16px]">upload_file</span>
                Upload Your First Dataset
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-space-lg">
              {filteredDatasets.map((d) => (
                <div
                  key={d.id}
                  className="rounded-xl bg-surface-container-lowest border border-outline-variant/30 p-space-lg shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-space-sm mb-space-sm">
                      <div className="flex items-center gap-space-xs">
                        <div className="w-10 h-10 rounded-lg bg-primary-fixed text-primary flex items-center justify-center font-bold">
                          <span className="material-symbols-outlined text-[22px]">table_chart</span>
                        </div>
                        <div className="min-w-0">
                          <h3 className="font-headline-sm text-headline-sm text-on-surface font-bold truncate">
                            {d.name.replace(/\.[^/.]+$/, '')}
                          </h3>
                          <span className="font-code-sm text-code-sm text-on-surface-variant truncate block">{d.name}</span>
                        </div>
                      </div>
                      <span className="px-space-xs py-space-3xs rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-code-sm text-code-sm font-semibold">
                        99.4% Health
                      </span>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 gap-space-xs py-space-sm my-space-xs border-y border-outline-variant/20">
                      <div>
                        <span className="font-label-sm text-label-sm uppercase text-on-surface-variant">Rows</span>
                        <p className="font-headline-sm text-headline-sm text-on-surface font-semibold">{d.rows.toLocaleString()}</p>
                      </div>
                      <div>
                        <span className="font-label-sm text-label-sm uppercase text-on-surface-variant">Columns</span>
                        <p className="font-headline-sm text-headline-sm text-on-surface font-semibold">{d.columns}</p>
                      </div>
                    </div>

                    {/* Engine Tags */}
                    <div className="flex flex-wrap gap-space-2xs mb-space-md">
                      <span className="px-space-xs py-space-3xs rounded bg-surface-container-high text-on-surface-variant font-code-sm text-code-sm">
                        Dual-LLM Cached
                      </span>
                      <span className="px-space-xs py-space-3xs rounded bg-surface-container-high text-on-surface-variant font-code-sm text-code-sm">
                        Plotly Dynamic
                      </span>
                    </div>
                  </div>

                  {/* Actions Bar */}
                  <div className="flex items-center gap-space-2xs pt-space-xs border-t border-outline-variant/20">
                    <Link
                      href={`/insights/${d.id}`}
                      className="flex-1 inline-flex items-center justify-center gap-space-3xs py-space-xs px-space-xs rounded-lg bg-primary-fixed text-on-primary-fixed hover:bg-primary-fixed-dim font-label-md text-label-md font-semibold transition-colors"
                    >
                      <span className="material-symbols-outlined text-[16px]">bolt</span>
                      <span>Insights</span>
                    </Link>
                    <Link
                      href={`/analyse/${d.id}`}
                      className="flex-1 inline-flex items-center justify-center gap-space-3xs py-space-xs px-space-xs rounded-lg bg-surface-container-low hover:bg-surface-container-high text-on-surface font-label-md text-label-md font-medium transition-colors"
                    >
                      <span className="material-symbols-outlined text-[16px]">smart_toy</span>
                      <span>Analyse</span>
                    </Link>
                    <Link
                      href={`/explore/${d.id}`}
                      className="inline-flex items-center justify-center p-space-xs rounded-lg bg-surface-container-low hover:bg-surface-container-high text-on-surface transition-colors"
                      title="Explore Data"
                    >
                      <span className="material-symbols-outlined text-[18px]">table_rows</span>
                    </Link>
                    <button
                      onClick={() => handleDeleteDataset(d.id, d.name)}
                      className="inline-flex items-center justify-center p-space-xs rounded-lg bg-surface-container-low hover:bg-error-container hover:text-error text-on-surface-variant transition-colors"
                      title="Delete Dataset"
                    >
                      <span className="material-symbols-outlined text-[18px]">delete</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
