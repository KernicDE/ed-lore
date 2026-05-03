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
  height?: number;
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

function resolveId(n: string | GraphNode): string {
  return typeof n === 'object' ? n.id : n;
}

// Visual radius in graph units for a given node
function nodeRadius(node: GraphNode, mode: string): number {
  if (mode === 'mini') {
    if (node.depth === 0) return Math.sqrt(8) * 2;
    if (node.depth === 2) return Math.sqrt(2) * 2;
    return Math.sqrt(4) * 2;
  }
  return Math.sqrt(Math.max(1.5, Math.log(node.mentions + 1) * 2)) * 2;
}

export default function EntityGraph({ mode, miniData, baseUrl = '', height: heightProp }: EntityGraphProps) {
  const [ForceGraph, setForceGraph] = useState<any>(null);
  const [fullData, setFullData] = useState<{ nodes: GraphNode[]; edges: { source: string; target: string; weight: number }[] } | null>(null);
  const [nodeCount, setNodeCount] = useState(1000);
  const [typeFilter, setTypeFilter] = useState<Record<string, boolean>>({
    person: true, faction: true, location: true, technology: true,
  });
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    import('react-force-graph-2d').then((mod) => setForceGraph(() => mod.default));
  }, []);

  useEffect(() => {
    if (mode !== 'full') return;
    fetch(`${baseUrl}/data/graph-data.json`)
      .then((r) => r.json())
      .then(setFullData)
      .catch(() => setFullData({ nodes: [], edges: [] }));
  }, [mode, baseUrl]);

  useEffect(() => {
    if (!wrapperRef.current) return;
    const measure = () => {
      const w = wrapperRef.current?.offsetWidth;
      if (w && w > 0) setWidth(w);
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(wrapperRef.current);
    return () => ro.disconnect();
  }, []);

  const graphData = useMemo(() => {
    if (mode === 'mini') return miniData ?? { nodes: [], links: [] };
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

  const neighborMap = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const link of graphData.links) {
      const s = resolveId(link.source);
      const t = resolveId(link.target);
      if (!map.has(s)) map.set(s, new Set());
      if (!map.has(t)) map.set(t, new Set());
      map.get(s)!.add(t);
      map.get(t)!.add(s);
    }
    return map;
  }, [graphData.links]);

  const depthMap = useMemo(() => {
    const map = new Map<string, number>();
    for (const node of graphData.nodes) map.set(node.id, node.depth ?? 1);
    return map;
  }, [graphData.nodes]);

  // Threshold for full-mode labels: top ~10% by mention count
  const labelThreshold = useMemo(() => {
    if (mode !== 'full' || graphData.nodes.length === 0) return Infinity;
    const sorted = [...graphData.nodes].sort((a, b) => b.mentions - a.mentions);
    const cutoff = Math.max(0, Math.floor(sorted.length * 0.1) - 1);
    return sorted[cutoff]?.mentions ?? 0;
  }, [mode, graphData.nodes]);

  const getNodeColor = useCallback((node: GraphNode): string => {
    const base = TYPE_COLORS[node.type] || '#888888';
    if (mode === 'mini') {
      if (node.depth === 0) return '#ffffff';
      if (node.depth === 2) return hexToRgba(base, 0.4);
      return base;
    }
    if (!hoveredId) return base;
    if (node.id === hoveredId) return '#ffffff';
    if (neighborMap.get(hoveredId)?.has(node.id)) return base;
    return hexToRgba(base, 0.12);
  }, [mode, hoveredId, neighborMap]);

  const getLinkColor = useCallback((link: GraphLink): string => {
    const s = resolveId(link.source);
    const t = resolveId(link.target);
    if (mode === 'mini') {
      const sd = depthMap.get(s) ?? 1;
      const td = depthMap.get(t) ?? 1;
      return (sd === 2 || td === 2) ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.6)';
    }
    if (!hoveredId) return 'rgba(255,255,255,0.18)';
    if (s === hoveredId || t === hoveredId) return 'rgba(255,255,255,0.7)';
    return 'rgba(255,255,255,0.04)';
  }, [mode, hoveredId, depthMap]);

  const getNodeVal = useCallback((node: GraphNode): number => {
    if (mode === 'mini') {
      if (node.depth === 0) return 8;
      if (node.depth === 2) return 2;
      return 4;
    }
    return Math.max(1.5, Math.log(node.mentions + 1) * 2);
  }, [mode]);

  // Labels drawn on top of the default circle (nodeCanvasObjectMode="after")
  // ctx is NOT pre-translated — use node.x, node.y as origin
  const nodeCanvasObject = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const showLabel = mode === 'mini'
      ? (node.depth === 0 || node.depth === 1)
      : node.mentions >= labelThreshold;
    if (!showLabel) return;

    const label = node.name.length > 20 ? node.name.slice(0, 18) + '…' : node.name;
    const r = nodeRadius(node, mode);

    // Keep font at ~11px on screen regardless of zoom
    const fontSize = 11 / globalScale;
    ctx.font = `${fontSize}px monospace`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    const textWidth = ctx.measureText(label).width;
    const pad = 1.5 / globalScale;
    const yOff = node.y + r + 1.5 / globalScale;
    const bh = fontSize + pad * 2;

    ctx.fillStyle = 'rgba(6, 8, 16, 0.85)';
    ctx.fillRect(node.x - textWidth / 2 - pad, yOff, textWidth + pad * 2, bh);

    ctx.fillStyle = mode === 'mini' && node.depth === 0 ? '#ffffff' : 'rgba(200,200,200,0.95)';
    ctx.fillText(label, node.x, yOff + pad * 0.5);
  }, [mode, labelThreshold]);

  // Hit area — ctx is NOT pre-translated; enforce minimum 8px screen radius at any zoom
  const nodePointerAreaPaint = useCallback((node: any, color: string, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const val = getNodeVal(node as GraphNode);
    const minScreenPx = 8;
    const radius = Math.max(minScreenPx / globalScale, Math.sqrt(val) * 2);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(node.x ?? 0, node.y ?? 0, radius, 0, 2 * Math.PI);
    ctx.fill();
  }, [getNodeVal]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    if (node.type === 'arc') {
      window.location.href = `${baseUrl}/arc/${node.id}/`;
    } else {
      window.location.href = `${baseUrl}/entity/${node.id}/`;
    }
  }, [baseUrl]);

  const configureForces = useCallback(() => {
    const fg = graphRef.current;
    if (!fg || mode !== 'full') return;
    // Strong local repulsion keeps nodes apart; weight-based link distances cluster tightly connected nodes
    fg.d3Force('charge')?.strength(-250).distanceMax(120);
    fg.d3Force('link')
      ?.strength(0.4)
      .distance((link: any) => Math.max(5, 80 / Math.log((link.weight || 1) + 2)));
  }, [mode]);

  const handleEngineStop = useCallback(() => {
    const fg = graphRef.current;
    if (!fg || mode !== 'mini') return;
    fg.zoomToFit(300, 16);
  }, [mode]);

  const height = heightProp ?? (mode === 'mini' ? 340 : Math.max(500, (typeof window !== 'undefined' ? window.innerHeight : 800) - 180));
  const maxNodes = fullData?.nodes.length ?? 3484;

  const isReady = ForceGraph && width > 0 && (mode !== 'full' || fullData !== null);

  return (
    <div>
      {mode === 'full' && (
        <div className="graph-controls">
          <div className="graph-controls-row">
            <label className="graph-control-label">
              Nodes: <strong>{nodeCount}</strong>
            </label>
            <input
              type="range" min={50} max={maxNodes} step={10}
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

      <div ref={wrapperRef} style={{ width: '100%' }}>
        {!isReady ? (
          <div className="graph-placeholder" style={{ height }}>
            <span style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
              {mode === 'full' && !fullData ? 'Loading graph data…' : 'Initialising graph…'}
            </span>
          </div>
        ) : (
          <ForceGraph
            ref={graphRef}
            graphData={graphData}
            width={width}
            height={height}
            nodeId="id"
            nodeColor={getNodeColor}
            nodeVal={getNodeVal}
            nodeLabel={(n: GraphNode) => `${n.name} (${n.mentions} mentions)`}
            nodeCanvasObjectMode="after"
            nodeCanvasObject={nodeCanvasObject}
            nodePointerAreaPaint={nodePointerAreaPaint}
            linkColor={getLinkColor}
            linkWidth={(link: GraphLink) =>
              mode === 'mini'
                ? Math.max(1.5, Math.log(((link.weight as number) || 1) + 1) * 1.2)
                : Math.max(0.8, Math.log(((link.weight as number) || 1) + 1) * 0.6)
            }
            onNodeClick={handleNodeClick}
            onNodeHover={(node: GraphNode | null) => setHoveredId(node?.id ?? null)}
            onEngineStart={configureForces}
            onEngineStop={handleEngineStop}
            backgroundColor="transparent"
            autoPauseRedraw={false}
            warmupTicks={mode === 'mini' ? 80 : 150}
            cooldownTicks={mode === 'mini' ? 50 : 100}
            d3AlphaDecay={mode === 'mini' ? 0.05 : 0.025}
            d3VelocityDecay={0.4}
            enableNodeDrag={true}
            enableZoomInteraction={true}
            minZoom={0.05}
            maxZoom={12}
          />
        )}
      </div>
    </div>
  );
}
