import React, { useEffect, useState } from 'react';
import { ReactFlow, Background, Controls, useNodesState, useEdgesState } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import axios from 'axios';

export default function DependencyGraph({ projectId }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);

    axios.get(`http://localhost:5000/api/codebase/graph/${projectId}`)
      .then((res) => {
        const rawNodes = res.data.nodes || [];
        const rawEdges = res.data.edges || [];

        // Grid layout calculation for graph nodes
        const formattedNodes = rawNodes.map((node, idx) => ({
          id: node.id,
          data: { label: `${node.label} (${node.symbols.length} symbols)` },
          position: { x: (idx % 4) * 250 + 50, y: Math.floor(idx / 4) * 120 + 50 },
          style: {
            background: '#1e293b',
            color: '#f8fafc',
            border: '1px solid #3b82f6',
            borderRadius: '8px',
            padding: '10px',
            fontSize: '12px',
            width: 200,
          },
        }));

        const formattedEdges = rawEdges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          animated: true,
          style: { stroke: '#60a5fa' },
        }));

        setNodes(formattedNodes);
        setEdges(formattedEdges);
      })
      .catch((err) => console.error('Failed to load dependency graph:', err))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <div className="p-4 text-slate-400">Rendering AST Graph...</div>;

  return (
    <div style={{ width: '100%', height: '500px' }} className="rounded-xl border border-slate-700 bg-slate-900 overflow-hidden">
      <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} fitView>
        <Background color="#334155" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
}