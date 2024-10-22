import React, { useCallback, useEffect } from 'react';
import Dagre from '@dagrejs/dagre';
import {
  ReactFlow,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  addEdge,
  Controls,
  Background,
  Panel,
  useReactFlow,
  Handle,
  Position,
} from '@xyflow/react';

import '@xyflow/react/dist/style.css';

// Dagre layout function
const getLayoutedElements = (nodes, edges, options) => {
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: options.direction });

  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  nodes.forEach((node) =>
    g.setNode(node.id, {
      ...node,
      width: node.measured?.width ?? 0,
      height: node.measured?.height ?? 0,
    })
  );

  Dagre.layout(g);

  return {
    nodes: nodes.map((node) => {
      const position = g.node(node.id);
      const x = position.x - (node.measured?.width ?? 0) / 2;
      const y = position.y - (node.measured?.height ?? 0) / 2;
      return { ...node, position: { x, y }, dragHandle: 'drag' };  // Ensures nodes remain draggable
    }),
    edges,
  };
};

const nodeStyle = {
  padding: 10,
  border: '2px solid #000',
  borderRadius: 10,
  backgroundColor: '#fff',
  display: 'flex',
  alignItems: 'center',
  position: 'relative', // For positioning handles
};

function CustomNode({ data }) {
  return (
    <>
      {/* Target handle (top) */}
      {data.hasInput && <Handle type="target" position={Position.Top} />}
      
      {/* Node content */}
      <div style={nodeStyle}>
        {data.icon && <img src={data.icon} alt={data.label} style={{ width: 20, height: 20, marginRight: 10 }} />}
        <span>{data.label}</span>
      </div>

      {/* Source handles (bottom) */}
      {data.hasOutput && (
        <Handle type="source" position={Position.Bottom} id="a" />
      )}
    </>
  );
}

const nodeTypes = {
  customNode: CustomNode, // Use the custom node with handles
};

function CogFlowInner({ title = "Cognitive Design", nodes: initialNodes, edges: initialEdges, height = '400px' }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div style={{ width: '100%', height: height }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}  // Custom node types
        fitView
        panOnScroll
        zoomOnScroll
        panOnDrag
      >
        <Panel position="top-left">{title}</Panel>
        <Controls showInteractive={true} />
        {/* <Background variant="lines" gap={10} size={1} /> */}
      </ReactFlow>
    </div>
  );
}

// wrapping with ReactFlowProvider is done outside of the component
function CogFlow(props) {
  return (
    <ReactFlowProvider>
      <CogFlowInner {...props} />
    </ReactFlowProvider>
  );
}

// Ensure ReactFlowProvider wraps the component
export default CogFlow;
