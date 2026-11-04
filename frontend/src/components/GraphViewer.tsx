'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import {
  Network,
  Search,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  X,
  ExternalLink,
  Target,
  Focus,
  Layers,
  RotateCcw,
  BookOpen,
  Star,
  Calendar,
  User,
  Moon,
  Sun,
  ChevronRight,
} from 'lucide-react';
import { api, type GraphData, type GraphNode } from '@/lib/api';
import { safeOrigin } from '@/lib/editor';

// Safe dynamic import for browser-only react-force-graph
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
});

interface GraphViewerProps {
  onSearchTopic?: (topic: string) => void;
  onAttachSource?: (sourceId: string) => void;
  attachedSourceIds?: string[];
  proposalOpen?: boolean;
}

export default function GraphViewer({
  onSearchTopic,
  onAttachSource,
  attachedSourceIds = [],
  proposalOpen = false,
}: GraphViewerProps) {
  const [data, setData] = useState<GraphData>({ nodes: [], links: [], clusters: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'faculty' | 'paper' | 'topic'>('all');
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null);
  const [topicQuery, setTopicQuery] = useState('');
  const [searchDropdownOpen, setSearchDropdownOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [centerNodeId, setCenterNodeId] = useState<string | null>(null);
  const [hops, setHops] = useState<number>(2);
  const [nodeLimit, setNodeLimit] = useState<number>(2500);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const lastClickRef = useRef<{ id: string; time: number }>({ id: '', time: 0 });

  const loadGraph = useCallback(
    async (
      topic?: string,
      centerId?: string | null,
      hopsCount = 2,
      limit = 300
    ) => {
      setLoading(true);
      setError('');
      try {
        const graphData = await api.graph(
          limit,
          topic?.trim() || undefined,
          centerId || undefined,
          hopsCount
        );
        setData(graphData);
        setTimeout(() => {
          graphRef.current?.zoomToFit(400, 32);
        }, 350);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Could not load knowledge graph.');
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    void loadGraph(undefined, undefined, hops, nodeLimit);
  }, [loadGraph, nodeLimit]);

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      if (entries[0]) {
        setDimensions({
          width: entries[0].contentRect.width,
          height: entries[0].contentRect.height,
        });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchDropdownOpen(false);
    void loadGraph(topicQuery, centerNodeId, hops, nodeLimit);
  };

  const handleResetFilter = () => {
    setTopicQuery('');
    setSelectedCluster(null);
    setSearchDropdownOpen(false);
    void loadGraph('', centerNodeId, hops, nodeLimit);
  };

  const handleFocusEgo = (nodeId: string) => {
    setCenterNodeId(nodeId);
    setSelectedCluster(null);
    setSearchDropdownOpen(false);
    void loadGraph(topicQuery, nodeId, hops, nodeLimit);
  };

  const handleExitEgo = () => {
    setCenterNodeId(null);
    void loadGraph(topicQuery, null, hops, nodeLimit);
  };

  const handleHopsChange = (newHops: number) => {
    setHops(newHops);
    if (centerNodeId) {
      void loadGraph(topicQuery, centerNodeId, newHops, nodeLimit);
    }
  };

  const handleLimitChange = (newLimit: number) => {
    setNodeLimit(newLimit);
    void loadGraph(topicQuery, centerNodeId, hops, newLimit);
  };

  // Fixed Cluster Selection with Smooth Camera Fly-To Bounding Box
  const handleClusterSelect = (clusterName: string | null) => {
    const nextCluster = selectedCluster === clusterName ? null : clusterName;
    setSelectedCluster(nextCluster);

    if (nextCluster) {
      const clusterNodes = data.nodes.filter(
        (n) => n.cluster?.toLowerCase() === nextCluster.toLowerCase()
      );
      if (clusterNodes.length > 0) {
        const xs = clusterNodes.map((n) => n.x ?? 0);
        const ys = clusterNodes.map((n) => n.y ?? 0);
        const minX = Math.min(...xs), maxX = Math.max(...xs);
        const minY = Math.min(...ys), maxY = Math.max(...ys);
        const cx = (minX + maxX) / 2;
        const cy = (minY + maxY) / 2;
        graphRef.current?.centerAt(cx, cy, 500);
        graphRef.current?.zoom(1.8, 500);
      }
    } else {
      graphRef.current?.zoomToFit(500, 32);
    }
  };

  const handleFlyToNode = (node: GraphNode) => {
    setSelectedNode(node);
    setSearchDropdownOpen(false);
    if (node.x !== undefined && node.y !== undefined) {
      graphRef.current?.centerAt(node.x, node.y, 600);
      graphRef.current?.zoom(2.4, 600);
    }
  };

  const handleNodeClick = (node: any) => {
    const now = Date.now();
    if (lastClickRef.current.id === node.id && now - lastClickRef.current.time < 350) {
      handleFocusEgo(node.id);
      lastClickRef.current = { id: '', time: 0 };
      return;
    }
    lastClickRef.current = { id: node.id, time: now };
    setSelectedNode(node as GraphNode);
  };

  // Search autocomplete candidates
  const searchMatches = topicQuery.trim()
    ? data.nodes
        .filter((n) => n.name.toLowerCase().includes(topicQuery.trim().toLowerCase()))
        .slice(0, 6)
    : [];

  // Filter nodes according to type and cluster selectors (matched by cluster name)
  const filteredNodes = data.nodes.filter((node) => {
    if (typeFilter !== 'all' && node.type !== typeFilter) return false;
    if (selectedCluster && node.cluster?.toLowerCase() !== selectedCluster.toLowerCase()) return false;
    return true;
  });

  const filteredNodeIds = new Set(filteredNodes.map((n) => n.id));
  const filteredLinks = data.links.filter((l) => {
    const sId = typeof l.source === 'object' ? (l.source as any).id : l.source;
    const tId = typeof l.target === 'object' ? (l.target as any).id : l.target;
    return filteredNodeIds.has(sId) && filteredNodeIds.has(tId);
  });

  const filteredGraphData = {
    nodes: filteredNodes,
    links: filteredLinks,
  };

  const facultyCount = data.nodes.filter((n) => n.type === 'faculty').length;
  const paperCount = data.nodes.filter((n) => n.type === 'paper').length;
  const topicCount = data.nodes.filter((n) => n.type === 'topic').length;

  // Modern High-Performance Canvas Renderer with Avatars & Auras
  const drawNode = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const isCenter = Boolean(node.is_center);
      const isSelected = selectedNode?.id === node.id;

      let r = 5;
      if (isCenter) r = 10;
      else if (node.type === 'faculty') r = 7.5;
      else if (node.type === 'paper') r = 5.5;
      else if (node.type === 'topic') r = 4.5;
      if (isSelected) r += 3;

      const baseColor =
        node.type === 'faculty'
          ? (isDarkMode ? '#3b82f6' : '#2563eb')
          : node.type === 'paper'
          ? (isDarkMode ? '#10b981' : '#0f766e')
          : node.type === 'topic'
          ? '#d97706'
          : '#64748b';

      const nodeColor = node.cluster_color || baseColor;

      ctx.save();

      // Soft Atmospheric Aura
      ctx.beginPath();
      ctx.arc(node.x, node.y, r + (isCenter ? 6 : 3.5), 0, 2 * Math.PI, false);
      ctx.fillStyle =
        node.type === 'faculty'
          ? (isDarkMode ? 'rgba(59, 130, 246, 0.25)' : 'rgba(37, 99, 235, 0.15)')
          : node.type === 'paper'
          ? (isDarkMode ? 'rgba(16, 185, 129, 0.25)' : 'rgba(15, 118, 110, 0.15)')
          : 'rgba(217, 119, 6, 0.15)';
      ctx.fill();

      // Center Node Radar Halo
      if (isCenter) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, r + 7, 0, 2 * Math.PI, false);
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = Math.max(1.5, 2.5 / globalScale);
        ctx.setLineDash([4 / globalScale, 3 / globalScale]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Selected Node Halo
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, r + 4, 0, 2 * Math.PI, false);
        ctx.strokeStyle = isDarkMode ? '#60a5fa' : '#1d4ed8';
        ctx.lineWidth = Math.max(1.5, 2.5 / globalScale);
        ctx.stroke();
      }

      // Main Node Shape
      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
      ctx.fillStyle = nodeColor;
      ctx.fill();
      ctx.lineWidth = Math.max(1, 1.6 / globalScale);
      ctx.strokeStyle = isDarkMode ? '#1e293b' : '#ffffff';
      ctx.stroke();

      // Avatar Initials on Faculty Nodes
      if (node.type === 'faculty' && node.name && globalScale >= 0.8) {
        const initials = String(node.name)
          .split(' ')
          .map((p) => p[0])
          .filter(Boolean)
          .slice(0, 2)
          .join('')
          .toUpperCase();
        const initSize = Math.max(6, 7 / globalScale);
        ctx.font = `700 ${initSize}px -apple-system, BlinkMacSystemFont, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#ffffff';
        ctx.fillText(initials, node.x, node.y);
      }

      // Semantic Zoom Level-Of-Detail (LOD) Labels
      const shouldDrawLabel = globalScale >= 1.05 || isCenter || isSelected;
      if (shouldDrawLabel && node.name) {
        const rawName = String(node.name);
        const label = rawName.length > 34 ? rawName.slice(0, 32) + '…' : rawName;
        const fontSize = Math.max(8, (isCenter ? 12 : 10) / globalScale);
        ctx.font = `${isCenter ? '650' : '500'} ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;

        const textWidth = ctx.measureText(label).width;
        const textHeight = fontSize;
        const padX = 5 / globalScale;
        const padY = 2.5 / globalScale;
        const rectX = node.x - textWidth / 2 - padX;
        const rectY = node.y + r + 3.5 / globalScale;
        const rectW = textWidth + padX * 2;
        const rectH = textHeight + padY * 2;

        // Label pill background
        ctx.fillStyle = isDarkMode
          ? isCenter
            ? 'rgba(69, 10, 10, 0.95)'
            : 'rgba(15, 23, 42, 0.92)'
          : isCenter
          ? 'rgba(254, 242, 242, 0.96)'
          : node.type === 'paper'
          ? 'rgba(240, 253, 250, 0.95)'
          : 'rgba(255, 255, 255, 0.95)';
        ctx.fillRect(rectX, rectY, rectW, rectH);

        ctx.strokeStyle = isDarkMode
          ? isCenter
            ? 'rgba(239, 68, 68, 0.5)'
            : 'rgba(51, 65, 85, 0.8)'
          : isCenter
          ? 'rgba(220, 38, 38, 0.35)'
          : node.type === 'paper'
          ? 'rgba(15, 118, 110, 0.3)'
          : 'rgba(0, 0, 0, 0.12)';
        ctx.lineWidth = 0.6 / globalScale;
        ctx.strokeRect(rectX, rectY, rectW, rectH);

        // Text label
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = isDarkMode
          ? isCenter
            ? '#fca5a5'
            : '#f1f5f9'
          : isCenter
          ? '#991b1b'
          : node.type === 'paper'
          ? '#0f766e'
          : '#0f172a';
        ctx.fillText(label, node.x, rectY + rectH / 2);
      }

      ctx.restore();
    },
    [selectedNode, isDarkMode]
  );

  const paintPointerArea = useCallback((node: any, color: string, ctx: CanvasRenderingContext2D) => {
    const r = node.is_center ? 14 : 9;
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();
  }, []);

  return (
    <div className={`graph-container ${isDarkMode ? 'dark' : ''}`} ref={containerRef}>
      {/* Top Header & Toolbar */}
      <div className="graph-toolbar">
        <div className="graph-title-badge">
          <Network className={`w-4 h-4 ${isDarkMode ? 'text-blue-400' : 'text-[#225bb2]'}`} />
          <span>Knowledge Graph</span>
          <span className="count-badge">
            {filteredNodes.length} nodes · {filteredLinks.length} edges
          </span>
        </div>

        {/* Live Search Autocomplete Form */}
        <div className="graph-search-container">
          <form onSubmit={handleFilterSubmit} className="graph-search-form">
            <div className="input-with-icon">
              <Search className="w-3.5 h-3.5 text-[#536779]" />
              <input
                type="text"
                placeholder="Search faculty or paper…"
                value={topicQuery}
                onChange={(e) => {
                  setTopicQuery(e.target.value);
                  setSearchDropdownOpen(true);
                }}
                onFocus={() => setSearchDropdownOpen(true)}
              />
            </div>
            <button type="submit" className="button small">Filter</button>
            {topicQuery && (
              <button type="button" className="button small" onClick={handleResetFilter}>
                Clear
              </button>
            )}
          </form>

          {/* Autocomplete Dropdown with Direct Fly-To */}
          {searchDropdownOpen && searchMatches.length > 0 && (
            <div className="graph-search-dropdown">
              {searchMatches.map((match) => (
                <div
                  key={match.id}
                  className="graph-search-item"
                  onClick={() => handleFlyToNode(match)}
                >
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontWeight: 600 }}>{match.name}</span>
                    {match.metadata?.faculty_author && (
                      <span className="muted" style={{ fontSize: 11 }}>
                        By {match.metadata.faculty_author}
                      </span>
                    )}
                  </div>
                  <span className={`item-type ${match.type}`}>{match.type}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Type Filters */}
        <div className="graph-type-filters">
          <button
            type="button"
            className={`filter-chip ${typeFilter === 'all' ? 'active' : ''}`}
            onClick={() => setTypeFilter('all')}
          >
            All ({data.nodes.length})
          </button>
          <button
            type="button"
            className={`filter-chip faculty ${typeFilter === 'faculty' ? 'active' : ''}`}
            onClick={() => setTypeFilter('faculty')}
          >
            Faculty ({facultyCount})
          </button>
          <button
            type="button"
            className={`filter-chip paper ${typeFilter === 'paper' ? 'active' : ''}`}
            onClick={() => setTypeFilter('paper')}
          >
            Papers ({paperCount})
          </button>
          <button
            type="button"
            className={`filter-chip topic ${typeFilter === 'topic' ? 'active' : ''}`}
            onClick={() => setTypeFilter('topic')}
          >
            Topics ({topicCount})
          </button>
        </div>

        {/* Payload Density Limit Selector */}
        <div className="graph-type-filters" style={{ borderLeft: '1px solid #cbd5e1', paddingLeft: 8 }}>
          <span className="muted" style={{ fontSize: 11 }}>Density:</span>
          {[150, 300, 500].map((l) => (
            <button
              key={l}
              type="button"
              className={`filter-chip ${nodeLimit === l ? 'active' : ''}`}
              style={{ minHeight: 24, padding: '1px 7px', fontSize: 10 }}
              onClick={() => handleLimitChange(l)}
            >
              {l}
            </button>
          ))}
        </div>

        <div className="graph-controls">
          {/* Node Budget Selector */}
          <select
            value={nodeLimit}
            onChange={(e) => handleLimitChange(Number(e.target.value))}
            className="graph-limit-select"
            title="Adjust node density and budget"
            style={{
              fontSize: '11px',
              padding: '4px 8px',
              borderRadius: '6px',
              border: isDarkMode ? '1px solid rgba(255,255,255,0.15)' : '1px solid #cbd5e1',
              background: isDarkMode ? '#1e293b' : '#ffffff',
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              fontWeight: 500,
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <option value={300}>300 nodes</option>
            <option value={600}>600 nodes</option>
            <option value={1200}>1,200 nodes</option>
            <option value={2500}>2,500 nodes (Full Corpus)</option>
          </select>

          {/* Theme Switcher Toggle */}
          <button
            type="button"
            className="icon-button"
            title={isDarkMode ? 'Light Canvas' : 'Dark Obsidian Canvas'}
            onClick={() => setIsDarkMode(!isDarkMode)}
          >
            {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
          </button>

          <button
            type="button"
            className="icon-button"
            title="Zoom In"
            onClick={() => graphRef.current?.zoom(graphRef.current.zoom() * 1.3, 250)}
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            type="button"
            className="icon-button"
            title="Zoom Out"
            onClick={() => graphRef.current?.zoom(graphRef.current.zoom() / 1.3, 250)}
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            type="button"
            className="icon-button"
            title="Fit to Screen"
            onClick={() => graphRef.current?.zoomToFit(400, 32)}
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button
            type="button"
            className="icon-button"
            title="Refresh"
            onClick={() => void loadGraph(topicQuery, centerNodeId, hops, nodeLimit)}
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Ego-Network Focus Banner */}
      {(centerNodeId || data.center_node) && (
        <div className="graph-ego-banner">
          <div className="graph-ego-info">
            <Target className="w-4 h-4 text-blue-600 flex-shrink-0" />
            <span>
              Ego-network centered on{' '}
              <strong>
                {data.center_node?.name || selectedNode?.name || centerNodeId}
              </strong>
            </span>
            <span className="count-badge">
              {filteredNodes.length} connected nodes within {hops} hops
            </span>
            <div className="graph-ego-hops">
              <span className="muted" style={{ fontSize: 11 }}>Depth:</span>
              {[1, 2, 3].map((h) => (
                <button
                  key={h}
                  type="button"
                  className={hops === h ? 'active' : ''}
                  onClick={() => handleHopsChange(h)}
                >
                  {h} {h === 1 ? 'hop' : 'hops'}
                </button>
              ))}
            </div>
          </div>
          <button type="button" className="button small" onClick={handleExitEgo}>
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset to Global Graph</span>
          </button>
        </div>
      )}

      {/* Hierarchical Community Clusters Chips with Bounding-Box Zoom */}
      {data.clusters && data.clusters.length > 0 && (
        <div className="graph-cluster-chips">
          <span className="cluster-label">
            <Layers className="w-3.5 h-3.5 text-slate-500" />
            <span>Clusters:</span>
          </span>
          <button
            type="button"
            className={`cluster-chip ${selectedCluster === null ? 'active' : ''}`}
            onClick={() => handleClusterSelect(null)}
          >
            All Clusters ({data.nodes.length})
          </button>
          {data.clusters.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`cluster-chip ${selectedCluster === c.name ? 'active' : ''}`}
              onClick={() => handleClusterSelect(c.name)}
            >
              <span className="cluster-dot" style={{ backgroundColor: c.color }} />
              <span>{c.name}</span>
              <span className="cluster-count">({c.count})</span>
            </button>
          ))}
        </div>
      )}

      {/* Main Canvas Area with Dynamic Curved Links & Particles */}
      <div className="graph-canvas-wrapper">
        {loading && (
          <div className="graph-overlay">
            <div className="spinner" />
            <p>Rendering interactive knowledge graph…</p>
          </div>
        )}

        {error && !loading && (
          <div className="graph-overlay">
            <p className="alert error">{error}</p>
            <button
              type="button"
              className="primary"
              onClick={() => void loadGraph(topicQuery, centerNodeId, hops, nodeLimit)}
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && filteredNodes.length === 0 && (
          <div className="graph-overlay empty-state">
            <Network className="w-8 h-8 text-[#536779]" />
            <h3>No graph relationships found</h3>
            <p className="muted">
              {topicQuery
                ? `No nodes match topic "${topicQuery}". Try clearing the filter.`
                : selectedCluster
                ? `No nodes found in cluster "${selectedCluster}".`
                : 'No public records found. Import public records or sample data to populate the graph.'}
            </p>
            {(topicQuery || selectedCluster) && (
              <button type="button" className="button" onClick={handleResetFilter}>
                Clear Filters
              </button>
            )}
          </div>
        )}

        {!loading && !error && dimensions.width > 0 && dimensions.height > 0 && (
          <ForceGraph2D
            ref={graphRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={filteredGraphData}
            nodeCanvasObject={drawNode}
            nodeCanvasObjectMode={() => 'replace'}
            nodePointerAreaPaint={paintPointerArea}
            nodeLabel={(node: any) =>
              `${node.name || node.id} (${node.type})${
                node.cluster ? ` · ${node.cluster}` : ''
              }`
            }
            linkCurvature={0.08}
            linkColor={(link: any) => {
              const rel = link.relationship;
              if (isDarkMode) {
                if (rel === 'authored') return 'rgba(45, 212, 191, 0.45)';
                if (rel === 'co_authorship') return 'rgba(129, 140, 248, 0.4)';
                if (rel === 'addresses') return 'rgba(245, 158, 11, 0.45)';
                if (rel === 'researches') return 'rgba(96, 165, 250, 0.4)';
                if (rel === 'shares_concept') return 'rgba(56, 189, 248, 0.35)';
                if (rel === 'shared_interest') return 'rgba(192, 132, 252, 0.35)';
                return 'rgba(148, 163, 184, 0.2)';
              }
              if (rel === 'authored') return 'rgba(15, 118, 110, 0.45)';
              if (rel === 'co_authorship') return 'rgba(79, 70, 229, 0.35)';
              if (rel === 'addresses') return 'rgba(217, 119, 6, 0.4)';
              if (rel === 'researches') return 'rgba(37, 99, 235, 0.35)';
              if (rel === 'shares_concept') return 'rgba(2, 132, 199, 0.3)';
              if (rel === 'shared_interest') return 'rgba(124, 58, 237, 0.3)';
              return 'rgba(100, 116, 139, 0.22)';
            }}
            linkWidth={(link: any) =>
              link.relationship === 'authored' ? 1.6 : link.relationship === 'co_authorship' ? 1.4 : 1.1
            }
            linkDirectionalParticles={(link: any) =>
              link.relationship === 'authored' ? 2 : link.relationship === 'addresses' || link.relationship === 'researches' ? 1 : 0
            }
            linkDirectionalParticleWidth={1.5}
            linkDirectionalParticleSpeed={0.0035}
            linkDirectionalParticleColor={(link: any) => {
              const rel = link.relationship;
              if (rel === 'authored') return isDarkMode ? '#2dd4bf' : '#0d9488';
              if (rel === 'addresses') return isDarkMode ? '#fbbf24' : '#d97706';
              if (rel === 'researches') return isDarkMode ? '#60a5fa' : '#2563eb';
              return isDarkMode ? '#818cf8' : '#6366f1';
            }}
            backgroundColor={isDarkMode ? '#090d16' : '#ffffff'}
            warmupTicks={0}
            cooldownTicks={40}
            cooldownTime={1200}
            onNodeClick={handleNodeClick}
            enableNodeDrag={true}
            enablePanInteraction={true}
            enableZoomInteraction={true}
          />
        )}
      </div>

      {/* Modern Detailed Node Inspection Drawer */}
      {selectedNode && (
        <aside className="graph-node-drawer" aria-label="Node details">
          <div className="drawer-header">
            <span className={`tag ${selectedNode.type}`}>
              {selectedNode.type === 'faculty' && '🎓 '}
              {selectedNode.type === 'paper' && '📄 '}
              {selectedNode.type === 'topic' && '🏷️ '}
              {selectedNode.type.toUpperCase()}
            </span>
            {selectedNode.evidence_kind && (
              <span
                className={`evidence ${
                  selectedNode.evidence_kind === 'synthetic' ? 'synthetic' : ''
                }`}
              >
                {selectedNode.evidence_kind === 'synthetic'
                  ? 'Synthetic sample'
                  : 'Public evidence'}
              </span>
            )}
            <button
              type="button"
              className="close-button"
              aria-label="Close details"
              onClick={() => setSelectedNode(null)}
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <h3 className="drawer-title">{selectedNode.name}</h3>

          {/* Quick stats badges row */}
          <div className="drawer-stats-row">
            {selectedNode.metadata?.year && (
              <span className="drawer-stat-badge year">
                <Calendar className="w-3 h-3" />
                <span>{selectedNode.metadata.year}</span>
              </span>
            )}
            {selectedNode.metadata?.citations !== undefined && (
              <span className="drawer-stat-badge citations">
                <Star className="w-3 h-3" />
                <span>{selectedNode.metadata.citations} citations</span>
              </span>
            )}
            {selectedNode.metadata?.faculty_author && (
              <span className="drawer-stat-badge">
                <User className="w-3 h-3" />
                <span>{selectedNode.metadata.faculty_author}</span>
              </span>
            )}
          </div>

          {selectedNode.cluster && (
            <div className="drawer-cluster">
              <span
                className="cluster-dot"
                style={{
                  backgroundColor: selectedNode.cluster_color || '#2563eb',
                }}
              />
              <span>{selectedNode.cluster}</span>
            </div>
          )}

          {selectedNode.origin && (
            <div className="drawer-origin">
              {safeOrigin(selectedNode.origin) ? (
                <a
                  href={safeOrigin(selectedNode.origin)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="external-link"
                >
                  <span>
                    {selectedNode.type === 'paper' ? 'View Google Scholar / DOI' : 'View faculty profile'}
                  </span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              ) : (
                <span className="muted">{selectedNode.origin}</span>
              )}
            </div>
          )}

          {/* Abstract reader card for papers */}
          {selectedNode.metadata?.abstract && (
            <div className="drawer-abstract">
              <h4>
                <BookOpen className="w-3 h-3 inline mr-1" />
                Abstract
              </h4>
              <p>{selectedNode.metadata.abstract}</p>
            </div>
          )}

          {/* Structured metadata facts */}
          {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
            <div className="drawer-metadata">
              <h4>Metadata & Provenance</h4>
              {selectedNode.metadata.doi && (
                <p>
                  <strong>DOI:</strong> {selectedNode.metadata.doi}
                </p>
              )}
              {selectedNode.metadata.authors && (
                <p>
                  <strong>Authors:</strong>{' '}
                  {Array.isArray(selectedNode.metadata.authors)
                    ? selectedNode.metadata.authors.join(', ')
                    : selectedNode.metadata.authors}
                </p>
              )}
              {selectedNode.metadata.department && (
                <p>
                  <strong>Department:</strong> {selectedNode.metadata.department}
                </p>
              )}
              {selectedNode.metadata.interests && (
                <p>
                  <strong>Research areas:</strong>{' '}
                  {Array.isArray(selectedNode.metadata.interests)
                    ? selectedNode.metadata.interests.join(', ')
                    : selectedNode.metadata.interests}
                </p>
              )}
            </div>
          )}

          {/* Connected Links / Relationships preview */}
          {(() => {
            const connectedLinks = filteredLinks.filter(
              (l: any) =>
                (typeof l.source === 'object' ? l.source.id : l.source) === selectedNode.id ||
                (typeof l.target === 'object' ? l.target.id : l.target) === selectedNode.id
            );
            if (connectedLinks.length === 0) return null;
            return (
              <div className="drawer-connections" style={{ marginTop: '12px', marginBottom: '12px' }}>
                <h4 style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b', marginBottom: '6px' }}>
                  Connections ({connectedLinks.length})
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '140px', overflowY: 'auto' }}>
                  {connectedLinks.slice(0, 10).map((l: any, idx: number) => {
                    const isSrc = (typeof l.source === 'object' ? l.source.id : l.source) === selectedNode.id;
                    const other = isSrc
                      ? typeof l.target === 'object'
                        ? l.target.name || l.target.id
                        : l.target
                      : typeof l.source === 'object'
                      ? l.source.name || l.source.id
                      : l.source;
                    return (
                      <div
                        key={idx}
                        style={{
                          fontSize: '11px',
                          padding: '4px 6px',
                          borderRadius: '4px',
                          background: isDarkMode ? 'rgba(255,255,255,0.05)' : '#f1f5f9',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <span style={{ fontWeight: 600, color: isDarkMode ? '#93c5fd' : '#2563eb' }}>
                          {l.relationship}
                        </span>
                        <span
                          style={{
                            color: isDarkMode ? '#cbd5e1' : '#475569',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            maxWidth: '160px',
                          }}
                        >
                          {other}
                        </span>
                      </div>
                    );
                  })}
                  {connectedLinks.length > 10 && (
                    <span style={{ fontSize: '10px', color: '#94a3b8', fontStyle: 'italic' }}>
                      + {connectedLinks.length - 10} more connections
                    </span>
                  )}
                </div>
              </div>
            );
          })()}

          <div className="drawer-actions">
            {/* Ego-Network neighborhood exploration button */}
            <button
              type="button"
              className="button primary wide"
              onClick={() => handleFocusEgo(selectedNode.id)}
              disabled={centerNodeId === selectedNode.id}
            >
              <Focus className="w-3.5 h-3.5 mr-1" />
              <span>
                {centerNodeId === selectedNode.id
                  ? 'Currently Center Node'
                  : selectedNode.type === 'faculty'
                  ? 'Explore Faculty Publications (2 Hops)'
                  : 'Explore Paper Ego-Network (2 Hops)'}
              </span>
            </button>

            {selectedNode.type === 'topic' && onSearchTopic && (
              <button
                type="button"
                className="button wide"
                onClick={() => onSearchTopic(selectedNode.name)}
              >
                Search topic in Discovery
              </button>
            )}

            {selectedNode.type !== 'topic' && onAttachSource && proposalOpen && (
              <button
                type="button"
                className="button wide"
                disabled={attachedSourceIds.includes(selectedNode.id)}
                onClick={() => onAttachSource(selectedNode.id)}
              >
                {attachedSourceIds.includes(selectedNode.id)
                  ? 'Attached to proposal'
                  : 'Attach to open proposal'}
              </button>
            )}
          </div>
        </aside>
      )}
    </div>
  );
}
