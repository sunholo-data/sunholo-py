import React, { useState, useEffect } from 'react';

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

const CustomPlot = ({ data, layout }) => {
  const [Plot, setPlot] = useState(null);

  // Dynamically import `react-plotly.js` on the client side
  useEffect(() => {
    let isMounted = true;
    import('react-plotly.js').then((module) => {
      if (isMounted) {
        setPlot(() => module.default);
      }
    });

    return () => {
      isMounted = false; // Cleanup to prevent memory leaks
    };
  }, []);

  if (!Plot) {
    return <div>Loading Plot...</div>; // Show a loading state while Plotly is being imported
  }

  return (
    <Plot
      data={data}
      layout={layout || {
        title: 'Dynamic UI Plot',
        autosize: true,
        margin: { t: 30, l: 30, r: 30, b: 30 },
      }}
      useResizeHandler
      style={{ width: '100%', height: '300px' }}
    />
  );
};

export default CustomPlot;
