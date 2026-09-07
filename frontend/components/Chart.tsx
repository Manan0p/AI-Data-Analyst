'use client';

import { useEffect, useState } from 'react';

interface ChartProps {
  spec?: any;
  figure?: any;
}

export default function Chart({ spec, figure }: ChartProps) {
  const raw = figure || spec || {};
  const chartData =
    raw && typeof raw === 'object' && 'figure' in raw && raw.figure
      ? raw.figure
      : raw && typeof raw === 'object' && 'spec' in raw && raw.spec
      ? raw.spec
      : raw;

  const traces = Array.isArray(chartData?.data) ? chartData.data : [];
  const layout = chartData?.layout && typeof chartData.layout === 'object' ? chartData.layout : {};

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
      .catch((err) => {
        console.error('Failed to load Plotly module:', err);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  if (!PlotComponent) {
    return (
      <div className="flex h-64 w-full items-center justify-center rounded-xl border border-outline-variant/30 bg-surface-container-low/40">
        <div className="flex items-center gap-2 text-sm text-on-surface-variant font-label-md">
          <span className="material-symbols-outlined text-[20px] text-primary animate-spin">sync</span>
          <span>Rendering interactive chart...</span>
        </div>
      </div>
    );
  }

  if (traces.length === 0) {
    return (
      <div className="flex h-64 w-full items-center justify-center rounded-xl border border-outline-variant/30 bg-surface-container-low/20">
        <div className="flex flex-col items-center gap-2 text-sm text-on-surface-variant font-label-md">
          <span className="material-symbols-outlined text-[28px] text-outline">bar_chart</span>
          <span>No chart series data available</span>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full rounded-xl overflow-hidden bg-white">
      <PlotComponent
        data={traces}
        layout={{
          ...layout,
          autosize: true,
          font: { color: '#131b2e', family: 'Inter, sans-serif' },
          paper_bgcolor: '#ffffff',
          plot_bgcolor: '#faf8ff',
          margin: { t: 30, b: 40, l: 50, r: 20 },
        }}
        style={{ width: '100%', height: '360px' }}
        useResizeHandler
        config={{ responsive: true, displaylogo: false, displayModeBar: true }}
      />
    </div>
  );
}
