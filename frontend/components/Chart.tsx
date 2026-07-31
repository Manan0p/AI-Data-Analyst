'use client';

import { useEffect, useState } from 'react';

interface ChartProps {
  spec: {
    data: unknown[];
    layout: object;
  };
}

export default function Chart({ spec }: ChartProps) {
  const [PlotComponent, setPlotComponent] = useState<any>(null);

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      import('plotly.js/dist/plotly'),
      import('react-plotly.js/factory'),
    ])
      .then(([PlotlyModule, createPlotlyComponent]) => {
        if (!isMounted) return;
        const Plotly = PlotlyModule.default || PlotlyModule;
        const factory = createPlotlyComponent.default || createPlotlyComponent;
        setPlotComponent(() => factory(Plotly));
      })
      .catch(err => {
        console.error('Failed to load Plotly module:', err);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  if (!PlotComponent) {
    return (
      <div className="flex h-64 w-full items-center justify-center rounded-2xl border border-[var(--border)] bg-slate-900/40">
        <div className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
          <div className="spinner" /> Loading visualization…
        </div>
      </div>
    );
  }

  return (
    <div className="w-full rounded-2xl overflow-hidden" style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)' }}>
      <PlotComponent
        data={spec.data}
        layout={{
          ...spec.layout,
          autosize: true,
          font: { color: '#e8edf8', family: 'Inter, sans-serif' },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          margin: { t: 40, b: 40, l: 50, r: 20 },
        }}
        style={{ width: '100%', height: '340px' }}
        useResizeHandler
        config={{ responsive: true, displaylogo: false, displayModeBar: false }}
      />
    </div>
  );
}
