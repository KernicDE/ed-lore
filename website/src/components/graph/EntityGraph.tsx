import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { forceCollide } from 'd3-force-3d';

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

// nodeVal matches getNodeVal below; visual radius = sqrt(val) * 4 (library nodeRelSize=4)
function getVal(node: GraphNode, mode: string): number {
  if (mode === 'mini') {
    if (node.depth === 0) return 4;
    if (node.depth === 2) return 1;
    return 2;
  }
  return Math.max(0.7, Math.log(node.mentions + 1) * 1.0);
}

function visRadius(node: GraphNode, mode: string): number {
  return Math.sqrt(getVal(node, mode)) * 4; // must match library nodeRelSize=4
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
  const hoveredIdRef = useRef<string | null>(null);
  const labelThresholdRef = useRef<number>(Infinity);
  const nodesRef = useRef<GraphNode[]>([]);

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

  // Top 10% by mentions get permanent labels
  const labelThreshold = useMemo(() => {
    if (mode !== 'full' || graphData.nodes.length === 0) return Infinity;
    const sorted = [...graphData.nodes].sort((a, b) => b.mentions - a.mentions);
    const cutoff = Math.max(0, Math.floor(sorted.length * 0.1) - 1);
    return sorted[cutoff]?.mentions ?? 0;
  }, [mode, graphData.nodes]);
  labelThresholdRef.current = labelThreshold;
  nodesRef.current = graphData.nodes as GraphNode[];

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
      return (sd === 2 || td === 2) ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.65)';
    }
    if (!hoveredId) return 'rgba(255,255,255,0.2)';
    if (s === hoveredId || t === hoveredId) return 'rgba(255,255,255,0.75)';
    return 'rgba(255,255,255,0.04)';
  }, [mode, hoveredId, depthMap]);

  const getNodeVal = useCallback((node: GraphNode): number => getVal(node, mode), [mode]);

  // Draw ALL labels after ALL nodes/links — avoids node circles covering labels.
  // onRenderFramePost fires once per frame after the full scene is painted.
  // Reads from refs so the stable callback always sees current values.
  const onRenderFramePost = useCallback((ctx: CanvasRenderingContext2D, globalScale: number) => {
    const hId = hoveredIdRef.current;
    const lThreshold = labelThresholdRef.current;
    const nodes = nodesRef.current as any[];
    if (nodes.length === 0) return;

    const fontSize = 11 / globalScale;
    const pad = 1.5 / globalScale;
    ctx.font = `${fontSize}px monospace`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    for (const node of nodes) {
      if (node.x == null || node.y == null) continue;
      const showLabel = mode === 'mini'
        ? (node.depth === 0 || node.depth === 1 || node.id === hId)
        : (node.mentions >= lThreshold || node.id === hId);
      if (!showLabel) continue;

      const label = (node.name as string).length > 22
        ? (node.name as string).slice(0, 20) + '…'
        : (node.name as string);
      const r = visRadius(node as GraphNode, mode);
      const tw = ctx.measureText(label).width;
      const yOff = node.y + r + 2 / globalScale;

      ctx.fillStyle = 'rgba(6,8,16,0.88)';
      ctx.fillRect(node.x - tw / 2 - pad, yOff, tw + pad * 2, fontSize + pad * 2);
      ctx.fillStyle = node.depth === 0 ? '#ffffff' : 'rgba(200,200,200,0.95)';
      ctx.fillText(label, node.x, yOff + pad * 0.5);
    }
  }, [mode]); // stable — reads all dynamic state from refs

  // Window-level capture: fires before d3-drag can stopPropagation, so ALL nodes are clickable
  useEffect(() => {
    let downX = 0, downY = 0;

    const onDown = (e: PointerEvent) => { downX = e.clientX; downY = e.clientY; };

    const onUp = (e: PointerEvent) => {
      const dx = e.clientX - downX;
      const dy = e.clientY - downY;
      if (dx * dx + dy * dy > 36) return; // > 6px = drag

      const fg = graphRef.current;
      const wrapper = wrapperRef.current;
      if (!fg || !wrapper) return;

      const rect = wrapper.getBoundingClientRect();
      if (e.clientX < rect.left || e.clientX > rect.right ||
          e.clientY < rect.top  || e.clientY > rect.bottom) return;

      const gc = fg.screen2GraphCoords(e.clientX - rect.left, e.clientY - rect.top);
      const zoom: number = fg.zoom() ?? 1;
      const minR = 8 / zoom;

      let found: GraphNode | null = null;
      let best = Infinity;
      for (const node of nodesRef.current as any[]) {
        if (node.x == null || node.y == null) continue;
        const ndx = node.x - gc.x;
        const ndy = node.y - gc.y;
        const r = Math.max(minR, visRadius(node as GraphNode, mode));
        const distSq = ndx * ndx + ndy * ndy;
        if (distSq <= r * r && distSq < best) { best = distSq; found = node as GraphNode; }
      }

      if (found) {
        if (found.type === 'arc') window.location.href = `${baseUrl}/arc/${found.id}/`;
        else window.location.href = `${baseUrl}/entity/${found.id}/`;
      }
    };

    window.addEventListener('pointerdown', onDown, { capture: true });
    window.addEventListener('pointerup', onUp, { capture: true });
    return () => {
      window.removeEventListener('pointerdown', onDown, { capture: true });
      window.removeEventListener('pointerup', onUp, { capture: true });
    };
  }, [mode, baseUrl]);

  // Manual hover detection — bypasses shadow canvas entirely
  const handlePointerMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const fg = graphRef.current;
    if (!fg || !wrapperRef.current) return;
    const rect = wrapperRef.current.getBoundingClientRect();
    const gc = fg.screen2GraphCoords(e.clientX - rect.left, e.clientY - rect.top);
    const zoom: number = fg.zoom() ?? 1;
    const minR = 6 / zoom; // 6px screen minimum

    let found: string | null = null;
    let best = Infinity;
    for (const node of graphData.nodes as any[]) {
      if (node.x == null || node.y == null) continue;
      const dx = node.x - gc.x;
      const dy = node.y - gc.y;
      const r = Math.max(minR, visRadius(node as GraphNode, mode));
      const distSq = dx * dx + dy * dy;
      if (distSq <= r * r && distSq < best) {
        best = distSq;
        found = node.id;
      }
    }

    if (found !== hoveredIdRef.current) {
      hoveredIdRef.current = found;
      setHoveredId(found);
    }
  }, [graphData.nodes, mode]);


  const configureForces = useCallback(() => {
    const fg = graphRef.current;
    if (!fg) return;

    if (mode === 'full') {
      // Charge only repels locally; center pulls everything toward origin
      fg.d3Force('charge')?.strength(-120).distanceMax(200);
      fg.d3Force('link')
        ?.strength(0.6)
        .distance((link: any) => Math.max(8, 50 / Math.log((link.weight || 1) + 2)));
      fg.d3Force('center')?.strength(0.15); // stronger pull keeps isolated nodes from drifting
    }

    // Collision force keeps nodes from overlapping (uses actual visual radius)
    fg.d3Force('collide', forceCollide((node: any) => visRadius(node as GraphNode, mode) + 2));
  }, [mode]);

  const handleEngineStop = useCallback(() => {
    const fg = graphRef.current;
    if (!fg || mode !== 'mini') return;
    fg.zoomToFit(300, 20);
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

      <div
        ref={wrapperRef}
        style={{ width: '100%', cursor: hoveredId ? 'pointer' : 'default' }}
        onMouseMove={handlePointerMove}
        onMouseLeave={() => { hoveredIdRef.current = null; setHoveredId(null); }}
      >
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
            nodeLabel={() => ''}
            onRenderFramePost={onRenderFramePost}
            linkColor={getLinkColor}
            linkWidth={(link: GraphLink) =>
              mode === 'mini'
                ? Math.max(1.5, Math.log(((link.weight as number) || 1) + 1) * 1.2)
                : Math.max(0.8, Math.log(((link.weight as number) || 1) + 1) * 0.65)
            }
            onNodeClick={() => null}
            onNodeHover={() => null}
            onEngineStart={configureForces}
            onEngineStop={handleEngineStop}
            backgroundColor="transparent"
            autoPauseRedraw={false}
            warmupTicks={mode === 'mini' ? 20 : 0}
            cooldownTicks={mode === 'mini' ? 80 : 200}
            d3AlphaDecay={mode === 'mini' ? 0.03 : 0.015}
            d3VelocityDecay={0.35}
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
