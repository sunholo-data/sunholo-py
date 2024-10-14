import React from 'react';
import Plot from 'react-plotly.js';

export const Highlight = ({ children, color }) => (
  <span
    style={{
      backgroundColor: color,
      borderRadius: '2px',
      color: '#fff',
      padding: '0.2rem',
    }}
  >
    {children}
  </span>
);

const CustomPlot = ({ data }) => {
  return (
    <Plot
      data={data}
      layout={{
        title: 'Generated Plot',
        autosize: true,
        margin: { t: 30, l: 30, r: 30, b: 30 },
        xaxis: {
          title: 'X Axis',
        },
        yaxis: {
          title: 'Y Axis',
        },
      }}
      useResizeHandler
      style={{ width: '100%', height: '400px' }}
    />
  );
};

export default CustomPlot;