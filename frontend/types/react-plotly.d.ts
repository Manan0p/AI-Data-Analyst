declare module 'react-plotly.js' {
  import { ComponentType } from 'react';
  const Plot: ComponentType<any>;
  export default Plot;
}

declare module 'react-plotly.js/factory' {
  import { ComponentType } from 'react';
  export default function createPlotlyComponent(plotly: any): ComponentType<any>;
}

declare module 'plotly.js/dist/plotly';
declare module 'plotly.js-dist-min';
