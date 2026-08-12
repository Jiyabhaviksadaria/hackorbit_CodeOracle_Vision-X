import React, { useState, useMemo } from 'react';
import { GitGraph, Info, FileCode } from 'lucide-react';

export function DepGraphView({ depGraph }) {
  const [selectedNodeId, setSelectedNodeId] = useState(null);

  const nodes = depGraph?.nodes || [];
  const edges = depGraph?.edges || [];

  const layoutNodes = useMemo(() => {
    if (nodes.length === 0) return [];
    const width = 600;
    const height = 380;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.35;

    return nodes.map((node, index) => {
      const angle = (index / nodes.length) * 2 * Math.PI - Math.PI / 2;
      return {
        ...node,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });
  }, [nodes]);

  const selectedNode = useMemo(() => {
    return layoutNodes.find((n) => n.id === selectedNodeId) || null;
  }, [layoutNodes, selectedNodeId]);

  if (!depGraph || nodes.length === 0) {
    return (
      <div className="p-8 text-center bg-[#0D1117] border border-[#30363D] rounded-[6px] text-[#8B949E] text-xs font-mono">
        No dependency graph payload returned.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Topology Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#30363D]">
        <div className="flex items-center gap-2">
          <GitGraph className="w-4 h-4 text-[#58A6FF]" />
          <h3 className="text-sm font-semibold text-[#E6EDF3]">
            Dependency Graph Topology
          </h3>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono text-[#8B949E]">
          <span>Nodes: <strong className="text-[#E6EDF3]">{nodes.length}</strong></span>
          <span>Edges: <strong className="text-[#E6EDF3]">{edges.length}</strong></span>
        </div>
      </div>

      {/* Main Graph Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Graph Canvas */}
        <div className="lg:col-span-2 bg-[#0D1117] border border-[#30363D] rounded-[6px] p-4 relative overflow-hidden flex items-center justify-center min-h-[380px]">
          <svg viewBox="0 0 600 380" className="w-full h-auto max-h-[380px] select-none">
            <defs>
              <marker
                id="arrowhead-default"
                markerWidth="8"
                markerHeight="6"
                refX="18"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#30363D" />
              </marker>
              <marker
                id="arrowhead-accent"
                markerWidth="8"
                markerHeight="6"
                refX="18"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#58A6FF" />
              </marker>
            </defs>

            {/* Edges */}
            {edges.map((edge, idx) => {
              const src = layoutNodes.find((n) => n.id === edge.source);
              const tgt = layoutNodes.find((n) => n.id === edge.target);
              if (!src || !tgt) return null;

              const isHighlighted =
                selectedNodeId &&
                (edge.source === selectedNodeId || edge.target === selectedNodeId);

              return (
                <line
                  key={`edge-${idx}`}
                  x1={src.x}
                  y1={src.y}
                  x2={tgt.x}
                  y2={tgt.y}
                  stroke={isHighlighted ? '#58A6FF' : '#30363D'}
                  strokeWidth={isHighlighted ? 2 : 1}
                  markerEnd={isHighlighted ? 'url(#arrowhead-accent)' : 'url(#arrowhead-default)'}
                />
              );
            })}

            {/* Nodes */}
            {layoutNodes.map((node) => {
              const isSelected = node.id === selectedNodeId;

              return (
                <g
                  key={node.id}
                  onClick={() => setSelectedNodeId(isSelected ? null : node.id)}
                  className="cursor-pointer group"
                >
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={isSelected ? 18 : 14}
                    fill={isSelected ? '#1C2129' : '#161B22'}
                    stroke={isSelected ? '#58A6FF' : '#30363D'}
                    strokeWidth={isSelected ? 2 : 1}
                    className="transition-fast group-hover:stroke-[#58A6FF]"
                  />
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={4}
                    fill={isSelected ? '#58A6FF' : '#8B949E'}
                  />
                  <text
                    x={node.x}
                    y={node.y + 30}
                    textAnchor="middle"
                    fill={isSelected ? '#58A6FF' : '#8B949E'}
                    fontSize="11"
                    fontFamily="JetBrains Mono, monospace"
                    fontWeight={isSelected ? 'bold' : 'normal'}
                  >
                    {node.label || node.id}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Node Inspector Drawer */}
        <div className="bg-[#161B22] border border-[#30363D] rounded-[6px] p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-1.5 pb-2 mb-3 border-b border-[#30363D]">
              <Info className="w-4 h-4 text-[#58A6FF]" />
              <h4 className="text-xs font-semibold text-[#E6EDF3] uppercase tracking-wider">
                Node Properties
              </h4>
            </div>

            {selectedNode ? (
              <div className="space-y-3 font-mono text-xs">
                <div>
                  <span className="text-[10px] text-[#8B949E] uppercase block">Node ID</span>
                  <code className="text-[#58A6FF]">{selectedNode.id}</code>
                </div>

                <div>
                  <span className="text-[10px] text-[#8B949E] uppercase block">Label</span>
                  <p className="text-[#E6EDF3] font-semibold">{selectedNode.label}</p>
                </div>

                {selectedNode.file && (
                  <div>
                    <span className="text-[10px] text-[#8B949E] uppercase block mb-1">File Path</span>
                    <div className="flex items-center gap-1.5 text-[#E6EDF3] bg-[#0D1117] p-2 rounded-[4px] border border-[#30363D] break-all">
                      <FileCode className="w-3.5 h-3.5 text-[#8B949E] shrink-0" />
                      <span>{selectedNode.file}</span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-[#8B949E] font-mono py-8 text-center">
                Select a topology node to view exact attributes.
              </p>
            )}
          </div>

          {selectedNodeId && (
            <button
              onClick={() => setSelectedNodeId(null)}
              className="mt-4 w-full py-1.5 bg-[#0D1117] hover:bg-[#1C2129] text-[#8B949E] hover:text-[#E6EDF3] text-xs font-mono rounded-[4px] border border-[#30363D] transition-fast"
            >
              Clear Selection
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
