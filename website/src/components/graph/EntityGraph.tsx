import { useState, useEffect, useRef, useMemo, useCallback } from 'react';

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  mentions: number;
  depth?: 0 | 1 | 2;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  weight: number;
}

export interface MiniGraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

interface EntityGraphProps {
  mode: 'mini' | 'full';
  miniData?: MiniGraphData;
  baseUrl?: string;
}

const TYPE_COLORS: Record<string, string> = {
  person:     '#ff8c00',
  faction:    '#00bfff',
  location:   '#44ff88',
  technology: '#ffcc00',
  arc:        '#aa44ff',
};

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function nodeId(n: string | GraphNode): string {
  return typeof n === 'object' ? n.id : n;
}

export default function EntityGraph({ mode, miniData, baseUrl = '' }: EntityGraphProps) {
  const [ForceGraph, setForceGraph] = useState<any>(null);
  const [fullData, setFullData] = useState<{ nodes: GraphNode[]; edges: { source: string; target: string; weight: number }[] } | null>(null);
  const [nodeCount, setNodeCount] = useState(200);
  const [typeFilter, setTypeFilter] = useState<Record<string, boolean>>({
    person: true, faction: true, location: true, technology: true,
  });
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(600);

  // Dynamic import — keeps SSR safe and defers the heavy library
  useEffect(() => {
    import('react-force-graph-2d').then((mod) => setForceGraph(() => mod.default));
  }, []);

  // Load full graph data only in full mode
  useEffect(() => {
    if (mode !== 'full') return;
    fetch(`${baseUrl}/data/graph-data.json`)
      .then((r) => r.json())
      .then(setFullData)
      .catch(() => setFullData({ nodes: [], edges: [] }));
  }, [mode, baseUrl]);

  // Track container width for responsive canvas
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      setWidth(entries[0].contentRect.width || 600);
    });
    ro.observe(containerRef.current);
    setWidth(containerRef.current.offsetWidth || 600);
    return () => ro.disconnect();
  }, []);

  const graphData = useMemo(() => {
    if (mode === 'mini') {
      return miniData ?? { nodes: [], links: [] };
    }
    if (!fullData) return { nodes: [], links: [] };
    const sorted = [...fullData.nodes]
      .filter((n) => typeFilter[n.type] !== false)
      .sort((a, b) => b.mentions - a.mentions)
      .slice(0, nodeCount);
    const ids = new Set(sorted.map((n) => n.id));
    return {
      nodes: sorted,
      links: fullData.edges
        .filter((e) => ids.has(e.source) && ids.has(e.target))
        .map((e) => ({ source: e.source, target: e.target, weight: e.weight })),
    };
  }, [mode, miniData, fullData, nodeCount, typeFilter]);

  // Precompute neighbour map for hover dimming in full mode
  const neighborMap = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const link of graphData.links) {
      const s = nodeId(link.source);
      const t = nodeId(link.target);
      if (!map.has(s)) map.set(s, new Set());
      if (!map.has(t)) map.set(t, new Set());
      map.get(s)!.add(t);
      map.get(t)!.add(s);
    }
    return map;
  }, [graphData.links]);

  // Precompute depth map for mini mode link dimming
  const depthMap = useMemo(() => {
    const map = new Map<string, number>();
    for (const node of graphData.nodes) {
      map.set(node.id, node.depth ?? 1);
    }
    return map;
  }, [graphData.nodes]);

  const getNodeColor = useCallback((node: GraphNode): string => {
    const base = TYPE_COLORS[node.type] || '#888888';
    if (mode === 'mini') {
      if (node.depth === 0) return '#ffffff';
      if (node.depth === 2) return hexToRgba(base, 0.35);
      return base;
    }
    if (!hoveredId) return base;
    if (node.id === hoveredId) return '#ffffff';
    if (neighborMap.get(hoveredId)?.has(node.id)) return base;
    return hexToRgba(base, 0.15);
  }, [mode, hoveredId, neighborMap]);

  const getLinkColor = useCallback((link: GraphLink): string => {
    const s = nodeId(link.source);
    const t = nodeId(link.target);
    if (mode === 'mini') {
      if ((depthMap.get(s) ?? 1) === 2 || (depthMap.get(t) ?? 1) === 2) {
        return 'rgba(255,255,255,0.07)';
      }
      return 'rgba(255,255,255,0.28)';
    }
    if (!hoveredId) return 'rgba(255,255,255,0.12)';
    if (s === hoveredId || t === hoveredId) return 'rgba(255,255,255,0.55)';
    return 'rgba(255,255,255,0.03)';
  }, [mode, hoveredId, depthMap]);

  const getNodeVal = useCallback((node: GraphNode): number => {
    if (mode === 'mini') {
      if (node.depth === 0) return 10;
      if (node.depth === 2) return 1.5;
      return 4;
    }
    return Math.max(1, Math.log(node.mentions + 1) * 2);
  }, [mode]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    if (node.type === 'arc') {
      window.location.href = `${baseUrl}/arc/${node.id}/`;
    } else {
      window.location.href = `${baseUrl}/entity/${node.id}/`;
    }
  }, [baseUrl]);

  const height = mode === 'mini' ? 340 : Math.max(500, (typeof window !== 'undefined' ? window.innerHeight : 800) - 180);

  const placeholder = (
    <div
      ref={containerRef}
      className="graph-placeholder"
      style={{ height }}
    >
      <span style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
        {mode === 'full' && !fullData ? 'Loading graph data…' : 'Initialising graph…'}
      </span>
    </div>
  );

  if (!ForceGraph) return placeholder;
  if (mode === 'full' && !fullData) return placeholder;

  return (
    <div>
      {mode === 'full' && (
        <div className="graph-controls">
          <div className="graph-controls-row">
            <label className="graph-control-label">
              Nodes: <strong>{nodeCount}</strong>
            </label>
            <input
              type="range"
              min={50}
              max={1110}
              step={10}
              value={nodeCount}
              onChange={(e) => setNodeCount(Number(e.target.value))}
              className="graph-slider"
            />
          </div>
          <div className="graph-type-filters">
            {(['person', 'faction', 'location', 'technology'] as const).map((t) => (
              <label key={t} className="graph-filter-label" style={{ color: TYPE_COLORS[t] }}>
                <input
                  type="checkbox"
                  checked={typeFilter[t] !== false}
                  onChange={(e) => setTypeFilter((f) => ({ ...f, [t]: e.target.checked }))}
                />
                {t}
              </label>
            ))}
          </div>
          <div className="graph-legend">
            {Object.entries(TYPE_COLORS).filter(([k]) => k !== 'arc').map(([type, color]) => (
              <span key={type} className="graph-legend-item">
                <span className="graph-legend-dot" style={{ background: color }} />
                {type}
              </span>
            ))}
          </div>
        </div>
      )}
      <div ref={containerRef}>
        <ForceGraph
          graphData={graphData}
          width={width}
          height={height}
          nodeId="id"
          nodeColor={getNodeColor}
          nodeVal={getNodeVal}
          nodeLabel={(n: GraphNode) => `${n.name} (${n.mentions} mentions)`}
          linkColor={getLinkColor}
          linkWidth={(link: GraphLink) => Math.max(0.5, Math.log((link.weight as number || 1) + 1) * 0.3)}
          onNodeClick={handleNodeClick}
          onNodeHover={(node: GraphNode | null) => setHoveredId(node?.id ?? null)}
          backgroundColor="transparent"
          cooldownTicks={mode === 'mini' ? 80 : 150}
          d3AlphaDecay={mode === 'mini' ? 0.04 : 0.02}
          d3VelocityDecay={0.35}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          minZoom={0.1}
          maxZoom={10}
        />
      </div>
    </div>
  );
}
