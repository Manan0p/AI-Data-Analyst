'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { use, useState } from 'react';
import { api } from '@/services/api';

export default function ExplorePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [search, setSearch] = useState('');

  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: api.datasets });
  const { data: profile } = useQuery({ queryKey: ['profile', id], queryFn: () => api.profile(id) });
  const { data: rowData, isFetching } = useQuery({
    queryKey: ['rows', id, search],
    queryFn: () => api.rows(id, search),
  });

  const dataset = datasets?.find((d) => d.id === id);

  return (
    <div className="flex h-[calc(100vh-64px)] flex-col bg-surface">
      {/* 1. Explorer Top Breadcrumb & Action Bar */}
      <header className="flex items-center justify-between px-gutter-canvas py-space-sm bg-surface-container-lowest border-b border-outline-variant/30 shadow-xs flex-shrink-0">
        <div className="flex items-center gap-space-sm">
          <div className="flex items-center gap-space-xs text-on-surface-variant font-label-md text-label-md">
            <Link href="/" className="hover:text-primary transition-colors flex items-center gap-space-2xs">
              <span className="material-symbols-outlined text-[16px]">database</span>
              <span>Datasets</span>
            </Link>
            <span className="text-outline-variant font-code-sm text-code-sm">/</span>
            <span className="font-code-md text-code-md text-primary font-semibold">
              {dataset?.name || id}
            </span>
            <span className="text-outline-variant font-code-sm text-code-sm">/</span>
            <span className="px-space-xs py-space-3xs rounded bg-surface-container-high text-on-surface font-label-sm text-label-sm uppercase font-bold">
              Explorer & Profiler
            </span>
          </div>

          <div className="hidden lg:flex items-center gap-space-xs">
            <span className="px-space-xs py-space-3xs rounded-full bg-primary-fixed text-on-primary-fixed font-code-sm text-code-sm font-semibold">
              {dataset?.rows?.toLocaleString() || 0} Rows
            </span>
            <span className="px-space-xs py-space-3xs rounded-full bg-surface-container-high text-on-surface-variant font-code-sm text-code-sm font-semibold">
              {dataset?.columns || 0} Columns
            </span>
          </div>
        </div>

        <div className="flex items-center gap-space-sm">
          <Link
            href={`/insights/${id}`}
            className="flex items-center gap-space-2xs px-space-sm py-space-xs rounded-lg bg-surface-container-low hover:bg-surface-container-high text-on-surface font-label-md text-label-md transition-colors"
          >
            <span className="material-symbols-outlined text-[16px] text-primary">bolt</span>
            <span>Insights</span>
          </Link>
          <Link
            href={`/analyse/${id}`}
            className="flex items-center gap-space-2xs px-space-md py-space-xs rounded-lg bg-primary hover:bg-primary-container text-on-primary font-label-md text-label-md font-semibold transition-all shadow-xs"
          >
            <span className="material-symbols-outlined text-[16px]">smart_toy</span>
            <span>Analyse with AI →</span>
          </Link>
        </div>
      </header>

      {/* 2. Column Profiler Strip */}
      {profile && (
        <div className="flex gap-space-sm px-gutter-canvas py-space-xs overflow-x-auto flex-shrink-0 bg-surface-container-low/60 border-b border-outline-variant/30">
          <div className="flex items-center gap-space-xs text-body-sm flex-shrink-0 pr-space-sm border-r border-outline-variant/30">
            <span className="material-symbols-outlined text-[16px] text-primary">folder_open</span>
            <span className="font-code-sm text-code-sm font-semibold text-on-surface">
              {profile.rows.toLocaleString()} rows · {profile.columns} cols
            </span>
          </div>
          {profile.columns_profile.map((c) => (
            <div
              key={c.name}
              className="flex items-center gap-space-xs text-body-sm flex-shrink-0 rounded-lg px-space-sm py-1 bg-surface-container-lowest border border-outline-variant/30 shadow-xs"
            >
              <span className="material-symbols-outlined text-[14px] text-on-surface-variant">
                {c.dtype.includes('int') || c.dtype.includes('float')
                  ? 'pin'
                  : c.dtype.includes('date')
                  ? 'calendar_today'
                  : 'abc'}
              </span>
              <span className="font-code-sm text-code-sm font-semibold text-on-surface">{c.name}</span>
              <span className="font-code-sm text-code-sm text-on-surface-variant">({c.dtype})</span>
              {c.null_percentage > 0 && (
                <span className="px-1.5 py-0.5 rounded bg-error-container text-error font-code-sm text-code-sm font-bold">
                  {c.null_percentage.toFixed(0)}% null
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 3. Search Bar */}
      <div className="px-gutter-canvas py-space-sm flex-shrink-0 bg-surface-container-lowest border-b border-outline-variant/30 flex items-center justify-between">
        <div className="relative w-full max-w-md">
          <span className="material-symbols-outlined text-[18px] absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
            search
          </span>
          <input
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-surface-container-low border border-outline-variant/40 text-on-surface font-body-sm text-body-sm focus:outline-none focus:border-primary focus:bg-white"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search across all table cells..."
          />
        </div>
        <span className="font-code-sm text-code-sm text-on-surface-variant">
          Showing {rowData?.rows?.length || 0} sample rows
        </span>
      </div>

      {/* 4. High-Performance Data Table */}
      <div className="flex-1 overflow-auto bg-surface-container-lowest">
        {isFetching && !rowData && (
          <div className="flex items-center justify-center h-48 gap-space-sm text-on-surface-variant font-label-md">
            <span className="material-symbols-outlined text-[24px] text-primary animate-spin">sync</span>
            <span>Streaming dataset rows...</span>
          </div>
        )}
        {rowData && (
          <table className="stitch-table">
            <thead className="sticky top-0 z-10 shadow-xs">
              <tr>
                {rowData.columns.map((c) => (
                  <th key={c} className="whitespace-nowrap">
                    <div className="flex items-center gap-space-xs">
                      <span>{c}</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rowData.rows.map((row, i) => (
                <tr key={i} className="hover:bg-surface-container-low/60 transition-colors">
                  {rowData.columns.map((c) => (
                    <td key={c} className="whitespace-nowrap max-w-[240px] truncate font-code-sm text-code-sm">
                      {String(row[c] ?? '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
