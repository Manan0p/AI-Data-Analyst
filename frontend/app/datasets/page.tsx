'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { UploadPanel } from '@/components/UploadPanel';

export default function DatasetsPage() {
  const { data: datasets, isLoading } = useQuery({ queryKey: ['datasets'], queryFn: api.datasets });

  return (
    <div className="page-enter p-8">
      {/* Header */}
      <div className="mb-8">
        <p className="label mb-2" style={{ color: 'var(--accent-cyan)' }}>Manage</p>
        <h1 className="text-4xl font-bold text-white">Datasets</h1>
        <p className="muted mt-2">Upload and manage your CSV datasets for analysis.</p>
      </div>

      {/* Upload */}
      <div className="mb-10">
        <h2 className="mb-4 text-sm font-semibold text-white">Upload New Dataset</h2>
        <UploadPanel />
      </div>

      {/* List */}
      <div>
        <h2 className="mb-4 text-sm font-semibold text-white">
          Uploaded Datasets
          {datasets && (
            <span className="ml-2 badge badge-cyan">{datasets.length}</span>
          )}
        </h2>

        {isLoading && (
          <div className="flex items-center gap-3 text-sm" style={{ color: 'var(--text-muted)' }}>
            <div className="spinner" /> Loading datasets…
          </div>
        )}

        {!isLoading && (!datasets || datasets.length === 0) && (
          <div className="card py-12 text-center">
            <p className="text-3xl mb-3 opacity-30">◈</p>
            <p className="muted">No datasets uploaded yet.</p>
          </div>
        )}

        {datasets && datasets.length > 0 && (
          <div className="rounded-2xl overflow-hidden" style={{ border: '1px solid var(--border)' }}>
            <table className="w-full data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Rows</th>
                  <th>Columns</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map(d => (
                  <tr key={d.id}>
                    <td>
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg flex-shrink-0" style={{ background: 'rgba(34,211,238,0.08)' }}>
                          <span className="text-xs" style={{ color: 'var(--accent-cyan)' }}>◈</span>
                        </div>
                        <span className="font-medium text-white">{d.name}</span>
                      </div>
                    </td>
                    <td className="muted">{d.rows.toLocaleString()}</td>
                    <td className="muted">{d.columns}</td>
                    <td>
                      <div className="flex gap-2">
                        <Link href={`/analyse/${d.id}`} className="btn py-1.5 px-3 text-xs">
                          Analyse
                        </Link>
                        <Link href={`/explore/${d.id}`} className="btn-ghost border rounded-lg py-1.5 px-3 text-xs" style={{ borderColor: 'var(--border)' }}>
                          Explore
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
