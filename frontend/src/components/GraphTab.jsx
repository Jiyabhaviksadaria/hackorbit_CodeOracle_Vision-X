import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { X, Layers, FileCode, Search, Maximize2 } from 'lucide-react';
import { EmptyState } from './EmptyState';

// Deterministic color hashing for 6 vibrant edge stripes
const FILE_HUE_STRIPES = [
  '#58A6FF', // electric blue
  '#3FB950', // green
  '#D29922', // amber
  '#F85149', // red
  '#BC8CFF', // purple
  '#39C5CF', // cyan
];

function getFileStripeColor(filename) {
  if (!filename) return FILE_HUE_STRIPES[0];
  let hash = 0;
  for (let i = 0; i < filename.length; i++) {
    hash = filename.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % FILE_HUE_STRIPES.length;
  return FILE_HUE_STRIPES[index];
}

// Auto layout helper using Dagre graph library
const getLayoutedElements = (nodes, edges, direction = 'LR') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 50,
    ranksep: 100,
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 160, height: 44 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      targetPosition: 'left',
      sourcePosition: 'right',
      position: {
        x: nodeWithPosition.x - 80,
        y: nodeWithPosition.y - 22,
      },
    };
  });

  return { initialNodes: layoutedNodes, initialEdges: edges };
};

export function GraphTab({ depGraph, themeMode }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNodeId, setHoveredNodeId] = useState(null);

  const isFun = themeMode === 'fun';

  // Keyboard Escape listener to close Inspector Drawer
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') setSelectedNode(null);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const rawNodes = depGraph?.nodes || [];
  const rawEdges = depGraph?.edges || [];

  // Generate React Flow node and edge objects with layout & hover dimming
  const { initialNodes, initialEdges } = useMemo(() => {
    if (!rawNodes.length) return { initialNodes: [], initialEdges: [] };

    const formattedNodes = rawNodes.map((n) => {
      const colorStripe = getFileStripeColor(n.file || n.label);
      const isHovered = hoveredNodeId === n.id;

      return {
        id: n.id,
        data: { label: n.label, file: n.file, nodeData: n },
        position: { x: 0, y: 0 },
        style: {
          background: isFun ? '#ffffff' : '#161B22',
          color: isFun ? '#050505' : '#E6EDF3',
          border: isFun ? '2.5px solid #000000' : '1px solid #30363D',
          borderRadius: '999px',
          padding: '6px 16px 6px 12px',
          fontSize: '12px',
          fontFamily: 'JetBrains Mono, monospace',
          fontWeight: isFun ? '800' : '600',
          boxShadow: isFun ? '3px 3px 0px #000000' : 'none',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          borderLeft: `4px solid ${colorStripe}`,
          opacity: hoveredNodeId ? (isHovered ? 1 : 0.4) : 1,
          transition: 'all 150ms ease',
          cursor: 'pointer',
        },
      };
    });

    const formattedEdges = rawEdges.map((e, idx) => {
      const isConnectedToHovered =
        hoveredNodeId && (e.source === hoveredNodeId || e.target === hoveredNodeId);

      return {
        id: `e-${e.source}-${e.target}-${idx}`,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: isConnectedToHovered,
        style: {
          stroke: isConnectedToHovered
            ? isFun ? '#ff3e00' : '#58A6FF'
            : isFun ? '#000000' : '#8B949E',
          strokeWidth: isConnectedToHovered ? 2.5 : 1.5,
          opacity: hoveredNodeId ? (isConnectedToHovered ? 1 : 0.2) : 0.6,
          transition: 'all 150ms ease',
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 12,
          height: 12,
          color: isConnectedToHovered
            ? isFun ? '#ff3e00' : '#58A6FF'
            : isFun ? '#000000' : '#8B949E',
        },
      };
    });

    return getLayoutedElements(formattedNodes, formattedEdges);
  }, [rawNodes, rawEdges, hoveredNodeId, isFun]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick = useCallback((_, node) => {
    setSelectedNode(node.data.nodeData);
  }, []);

  const onNodeMouseEnter = useCallback((_, node) => {
    setHoveredNodeId(node.id);
  }, []);

  const onNodeMouseLeave = useCallback(() => {
    setHoveredNodeId(null);
  }, []);

  if (!rawNodes.length) {
    return (
      <EmptyState
        title="No dependency graph available"
        message="The parser found no module relationship edges for this repository."
      />
    );
  }

  return (
    <div className="relative w-full h-[620px] rounded-[6px] overflow-hidden select-none">
      {/* React Flow Canvas */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onNodeMouseEnter={onNodeMouseEnter}
        onNodeMouseLeave={onNodeMouseLeave}
        fitView
        className={isFun ? 'bg-[#FFFBEB]' : 'bg-[#0D1117]'}
      >
        <Background color={isFun ? '#000000' : '#30363D'} gap={20} size={1} opacity={isFun ? 0.15 : 0.3} />
        <Controls className={isFun ? '!bg-[#FFFFFF] !border-2 !border-[#000000] !shadow-[3px_3px_0px_#000000]' : '!bg-[#161B22] !border-[#30363D] !fill-[#E6EDF3]'} />
        <MiniMap
          nodeColor={isFun ? '#ff3e00' : '#58A6FF'}
          maskColor={isFun ? 'rgba(255, 251, 235, 0.7)' : 'rgba(13, 17, 23, 0.7)'}
          className={isFun ? '!bg-[#FFFFFF] !border-2 !border-[#000000] !shadow-[3px_3px_0px_#000000]' : '!bg-[#161B22] !border-[#30363D]'}
        />
      </ReactFlow>

      {/* Right-Side Node Inspector Panel (280px Drawer) */}
      {selectedNode && (
        <div className={`absolute top-0 right-0 bottom-0 w-80 shadow-2xl z-30 flex flex-col animate-slide-in font-sans ${
          isFun
            ? 'bg-[#FFFFFF] border-l-[3.5px] border-[#000000] text-[#050505]'
            : 'bg-[#161B22] border-l border-[#30363D] text-[#E6EDF3]'
        }`}>
          {/* Inspector Header */}
          <div className={`p-4 border-b flex items-center justify-between ${
            isFun ? 'bg-[#ff3e00] text-white border-b-[3.5px] border-[#000000]' : 'bg-[#1C2129] border-[#30363D]'
          }`}>
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 stroke-[2.5]" />
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider">
                Node Inspector
              </h4>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className={`p-1 rounded-[4px] border transition-fast cursor-pointer ${
                isFun
                  ? 'bg-[#FFFFFF] text-[#000000] border-2 border-[#000000] hover:bg-[#FEF3C7] shadow-[2px_2px_0px_#000000]'
                  : 'text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#0D1117] border-transparent'
              }`}
              title="Close Panel (ESC)"
            >
              <X className="w-4 h-4 stroke-[3]" />
            </button>
          </div>

          {/* Inspector Details Content */}
          <div className={`p-5 flex-1 overflow-y-auto space-y-4 text-xs ${isFun ? 'bg-[#FFFBEB]' : ''}`}>
            <div>
              <span className={`text-[10px] font-mono uppercase font-black block ${isFun ? 'text-[#ff3e00]' : 'text-[#8B949E]'}`}>
                NODE IDENTIFIER
              </span>
              <code className={`text-xs font-mono font-bold block mt-1 ${isFun ? 'text-[#050505]' : 'text-[#58A6FF]'}`}>
                {selectedNode.id}
              </code>
            </div>

            <div>
              <span className={`text-[10px] font-mono uppercase font-black block ${isFun ? 'text-[#ff3e00]' : 'text-[#8B949E]'}`}>
                FILE PATH
              </span>
              <div className={`p-2.5 rounded-[4px] border font-mono text-xs font-bold mt-1 ${
                isFun ? 'bg-[#FFFFFF] border-2 border-[#000000] text-[#050505] shadow-[2px_2px_0px_#000000]' : 'bg-[#0D1117] border-[#30363D] text-[#E6EDF3]'
              }`}>
                {selectedNode.file || selectedNode.label}
              </div>
            </div>

            <div>
              <span className={`text-[10px] font-mono uppercase font-black block ${isFun ? 'text-[#ff3e00]' : 'text-[#8B949E]'}`}>
                CONNECTED EDGES
              </span>
              <div className="space-y-1.5 mt-1 font-mono text-[11px]">
                {rawEdges.filter((e) => e.source === selectedNode.id || e.target === selectedNode.id).map((e, idx) => (
                  <div key={idx} className={`p-2 rounded-[4px] border flex items-center justify-between font-bold ${
                    isFun ? 'bg-[#FFFFFF] border-2 border-[#000000] text-[#050505]' : 'bg-[#0D1117] border-[#30363D] text-[#8B949E]'
                  }`}>
                    <span>{e.source}</span>
                    <span className={isFun ? 'text-[#ff3e00]' : 'text-[#58A6FF]'}>➔</span>
                    <span>{e.target}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className={`p-3 border-t text-[11px] font-mono ${
            isFun ? 'bg-[#FEF3C7] border-t-2 border-[#000000] text-[#050505] font-bold' : 'bg-[#1C2129] border-[#30363D] text-[#8B949E]'
          }`}>
            Press <code className={isFun ? 'text-[#ff3e00] font-black' : 'text-[#E6EDF3]'}>ESC</code> to dismiss
          </div>
        </div>
      )}
    </div>
  );
}
