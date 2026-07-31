'use client';

import { useDropzone } from 'react-dropzone';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export function UploadPanel() {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [uploaded, setUploaded] = useState<string[]>([]);
  const queryClient = useQueryClient();
  const router = useRouter();

  const onDrop = async (files: File[]) => {
    setBusy(true);
    setError('');
    try {
      const datasets = await api.upload(files);
      setUploaded(datasets.map(d => d.name));
      await queryClient.invalidateQueries({ queryKey: ['datasets'] });
      if (datasets[0]) router.push(`/analyse/${datasets[0].id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setBusy(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    multiple: true,
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={`drop-zone ${isDragActive ? 'active' : ''} ${busy ? 'pointer-events-none opacity-70' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl" style={{ background: 'rgba(34,211,238,0.08)', border: '1px solid rgba(34,211,238,0.15)' }}>
          {busy ? (
            <div className="spinner" />
          ) : (
            <span className="text-2xl" style={{ color: 'var(--accent-cyan)' }}>↑</span>
          )}
        </div>
        <div>
          <p className="font-semibold text-white">
            {isDragActive ? 'Drop your CSV files here' : busy ? 'Uploading & profiling…' : 'Upload CSV datasets'}
          </p>
          <p className="muted mt-1">Drag and drop one or more CSV files, or click to browse</p>
        </div>
      </div>

      {error && (
        <div className="mt-3 rounded-xl p-3 text-sm" style={{ background: 'rgba(251,113,133,0.1)', border: '1px solid rgba(251,113,133,0.2)', color: '#fb7185' }}>
          {error}
        </div>
      )}

      {uploaded.length > 0 && !busy && (
        <div className="mt-3 rounded-xl p-3 text-sm" style={{ background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.2)', color: '#34d399' }}>
          ✓ Uploaded: {uploaded.join(', ')}
        </div>
      )}
    </div>
  );
}
