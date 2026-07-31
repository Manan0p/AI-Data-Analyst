'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';

export default function DashboardPage() {
  const { data: datasets, isLoading } = useQuery({ queryKey: ['datasets'], queryFn: api.datasets });

  const totalRows = datasets?.reduce((s, d) => s + d.rows, 0) ?? 0;
  const totalCols = datasets?.reduce((s, d) => s + d.columns, 0) ?? 0;

  const stats = [
    { label: 'Datasets', value: datasets?.length ?? 0, icon: '◈', color: 'var(--accent-cyan)' },
    { label: 'Total Rows', value: totalRows.toLocaleString(), icon: '≡', color: 'var(--accent-violet)' },
    { label: 'Total Columns', value: totalCols, icon: '⊞', color: 'var(--accent-emerald)' },
  ];

  return (
    <div className="page-enter p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <p className="label mb-2" style={{ color: 'var(--accent-cyan)' }}>Workspace Overview</p>
        <h1 className="text-4xl font-bold text-white tracking-tight">Dashboard</h1>
        <p className="muted mt-2">Your AI-powered data workspace. Upload datasets and start analyzing.</p>
      </div>

      {/* Stats */}
      <div className="mb-10 grid grid-cols-1 md:grid-cols-3 gap-4">
        {stats.map(s => (
          <div key={s.label} className="stat-card">
            <div className="flex items-start justify-between">
              <p className="muted">{s.label}</p>
              <span className="text-xl" style={{ color: s.color }}>{s.icon}</span>
            </div>
            <p className="mt-3 text-3xl font-bold text-white tracking-tight">{isLoading ? '—' : s.value}</p>
          </div>
        ))}
      </div>

      {/* Datasets */}
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Your Datasets</h2>
        <Link href="/datasets" className="btn-ghost text-sm">
          Upload new →
        </Link>
      </div>

      {!datasets || datasets.length === 0 ? (
        <div className="card text-center py-16">
          <p className="text-5xl mb-4" style={{ color: 'var(--accent-cyan)' }}>◈</p>
          <h3 className="text-lg font-semibold text-white">No datasets uploaded</h3>
          <p className="muted mt-2 mb-6">Upload a CSV file to get started with AI-powered analysis.</p>
          <Link href="/datasets" className="btn">Upload Dataset</Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {datasets.map(d => (
            <div key={d.id} className="card-hover group">
              {/* Header */}
              <div className="mb-4 flex items-start justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl" style={{ background: 'rgba(56,189,248,0.1)', border: '1px solid rgba(56,189,248,0.2)' }}>
                  <span style={{ color: 'var(--accent-cyan)' }}>◈</span>
                </div>
                <span className="badge badge-cyan">CSV</span>
              </div>

              <h3 className="font-semibold text-white truncate">{d.name.replace(/\.csv$/i, '')}</h3>
              <p className="muted mt-1">{d.rows.toLocaleString()} rows · {d.columns} columns</p>

              {/* Actions */}
              <div className="mt-5 flex gap-2 border-t pt-4" style={{ borderColor: 'var(--border)' }}>
                <Link
                  href={`/analyse/${d.id}`}
                  className="btn flex-1 justify-center text-xs py-2"
                >
                  Analyse
                </Link>
                <Link
                  href={`/explore/${d.id}`}
                  className="btn-ghost flex-1 justify-center text-xs border rounded-xl"
                  style={{ borderColor: 'var(--border)' }}
                >
                  Explore
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quick tips */}
      {datasets && datasets.length > 0 && (
        <div className="mt-10 card" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)' }}>
          <h3 className="font-semibold text-white">💡 Try asking</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {[
              'Which region generated the highest revenue?',
              'Show monthly sales trends',
              'Detect anomalies in the dataset',
              'What are the top 5 customers by sales?',
              'Show a bar chart of sales by category',
            ].map(q => (
              <Link
                key={q}
                href={`/analyse/${datasets[0].id}?q=${encodeURIComponent(q)}`}
                className="rounded-lg px-3 py-1.5 text-xs transition-all"
                style={{ background: 'var(--bg-elevated)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent-cyan)'; (e.currentTarget as HTMLElement).style.color = 'var(--text-primary)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'; (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)'; }}
              >
                {q}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
