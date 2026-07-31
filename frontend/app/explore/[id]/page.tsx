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

  const dataset = datasets?.find(d => d.id === id);

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-4 flex-shrink-0" style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ background: 'rgba(129,140,248,0.1)', border: '1px solid rgba(129,140,248,0.2)' }}>
            <span style={{ color: 'var(--accent-violet)' }}>⊞</span>
          </div>
          <div>
            <h1 className="font-semibold text-white text-sm">{dataset?.name.replace(/\.csv$/i, '') ?? 'Explorer'}</h1>
            <p className="faint">{dataset?.rows.toLocaleString()} rows · {dataset?.columns} columns</p>
          </div>
        </div>
        <Link href={`/analyse/${id}`} className="btn text-xs px-4 py-2">
          Analyse with AI →
        </Link>
      </header>

      {/* Profile strip */}
      {profile && (
        <div className="flex gap-4 px-8 py-3 overflow-x-auto flex-shrink-0" style={{ background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border)' }}>
          <div className="flex items-center gap-1.5 text-xs flex-shrink-0">
            <span style={{ color: 'var(--accent-cyan)' }}>≡</span>
            <span style={{ color: 'var(--text-muted)' }}>{profile.rows.toLocaleString()} rows</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs flex-shrink-0">
            <span style={{ color: 'var(--accent-violet)' }}>⊞</span>
            <span style={{ color: 'var(--text-muted)' }}>{profile.columns} columns</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs flex-shrink-0">
            <span style={{ color: 'var(--accent-rose)' }}>⊗</span>
            <span style={{ color: 'var(--text-muted)' }}>{profile.duplicate_rows} duplicate rows</span>
          </div>
          {profile.columns_profile.slice(0, 5).map(c => (
            <div key={c.name} className="flex items-center gap-1.5 text-xs flex-shrink-0 rounded-lg px-2 py-1" style={{ background: 'rgba(34,211,238,0.05)', border: '1px solid var(--border)' }}>
              <span className="font-medium text-white">{c.name}</span>
              <span style={{ color: 'var(--text-faint)' }}>{c.dtype}</span>
              {c.null_percentage > 0 && <span className="badge badge-rose" style={{ fontSize: 10 }}>{c.null_percentage.toFixed(0)}% null</span>}
            </div>
          ))}
        </div>
      )}

      {/* Search bar */}
      <div className="px-8 py-4 flex-shrink-0" style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border)' }}>
        <div className="relative max-w-sm">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm" style={{ color: 'var(--text-faint)' }}>⌕</span>
          <input
            className="input pl-8"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search all columns…"
          />
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {isFetching && !rowData && (
          <div className="flex items-center justify-center h-32 gap-3 text-sm" style={{ color: 'var(--text-muted)' }}>
            <div className="spinner" /> Loading rows…
          </div>
        )}
        {rowData && (
          <>
            <table className="w-full data-table">
              <thead>
                <tr>
                  {rowData.columns.map(c => (
                    <th key={c} className="whitespace-nowrap">{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rowData.rows.map((row, i) => (
                  <tr key={i}>
                    {rowData.columns.map(c => (
                      <td key={c} className="whitespace-nowrap max-w-[200px] truncate">
                        {String(row[c] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="px-6 py-3 text-xs" style={{ color: 'var(--text-faint)', borderTop: '1px solid var(--border)' }}>
              Showing {rowData.rows.length.toLocaleString()} of {rowData.total.toLocaleString()} rows
              {search && ` matching "${search}"`}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
