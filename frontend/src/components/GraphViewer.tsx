'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { Network, Search, ZoomIn, ZoomOut, Maximize2, RefreshCw, X, ExternalLink } from 'lucide-react';
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
  const [data, setData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'faculty' | 'paper' | 'topic'>('all');
  const [topicQuery, setTopicQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  const loadGraph = useCallback(async (topic?: string) => {
    setLoading(true);
    setError('');
    try {
      const graphData = await api.graph(200, topic?.trim() || undefined);
      setData(graphData);
      setTimeout(() => {
        graphRef.current?.zoomToFit(400, 24);
      }, 300);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not load knowledge graph.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadGraph();
  }, [loadGraph]);

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
    void loadGraph(topicQuery);
  };

  const handleResetFilter = () => {
    setTopicQuery('');
    void loadGraph();
  };

  // Filter nodes according to type selector
  const filteredNodes = data.nodes.filter((node) => {
    if (typeFilter === 'all') return true;
    return node.type === typeFilter;
  });
  const filteredNodeIds = new Set(filteredNodes.map((n) => n.id));
  const filteredLinks = data.links.filter(
    (l) => {
      const sId = typeof l.source === 'object' ? (l.source as any).id : l.source;
      const tId = typeof l.target === 'object' ? (l.target as any).id : l.target;
      return filteredNodeIds.has(sId) && filteredNodeIds.has(tId);
    }
  );

  const filteredGraphData = {
    nodes: filteredNodes,
    links: filteredLinks,
  };

  const facultyCount = data.nodes.filter((n) => n.type === 'faculty').length;
  const paperCount = data.nodes.filter((n) => n.type === 'paper').length;
  const topicCount = data.nodes.filter((n) => n.type === 'topic').length;

  return (
    <div className="graph-container" ref={containerRef}>
      {/* Top Header & Toolbar */}
      <div className="graph-toolbar">
        <div className="graph-title-badge">
          <Network className="w-4 h-4 text-[#225bb2]" />
          <span>Public Knowledge Graph</span>
          <span className="count-badge">{filteredNodes.length} nodes · {filteredLinks.length} edges</span>
        </div>

        <form onSubmit={handleFilterSubmit} className="graph-search-form">
          <div className="input-with-icon">
            <Search className="w-3.5 h-3.5 text-[#536779]" />
            <input
              type="text"
              placeholder="Filter topic (e.g. sensor, AI)…"
              value={topicQuery}
              onChange={(e) => setTopicQuery(e.target.value)}
            />
          </div>
          <button type="submit" className="button small">Filter</button>
          {topicQuery && (
            <button type="button" className="button small" onClick={handleResetFilter}>
              Clear
            </button>
          )}
        </form>

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

        <div className="graph-controls">
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
            onClick={() => graphRef.current?.zoomToFit(400, 24)}
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button
            type="button"
            className="icon-button"
            title="Refresh"
            onClick={() => void loadGraph(topicQuery)}
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="graph-canvas-wrapper">
        {loading && (
          <div className="graph-overlay">
            <div className="spinner" />
            <p>Loading public knowledge graph…</p>
          </div>
        )}

        {error && !loading && (
          <div className="graph-overlay">
            <p className="alert error">{error}</p>
            <button type="button" className="primary" onClick={() => void loadGraph(topicQuery)}>
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
                : 'No public records found. Import public records or sample data to populate the graph.'}
            </p>
            {topicQuery && (
              <button type="button" className="button" onClick={handleResetFilter}>
                Clear Topic Filter
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
            nodeLabel={(node: any) => `${node.name || node.id} (${node.type})`}
            nodeColor={(node: any) => {
              const t = node.type?.toLowerCase() || '';
              if (t === 'faculty') return '#225bb2';
              if (t === 'paper') return '#14766d';
              if (t === 'topic') return '#d97706';
              return '#536779';
            }}
            nodeRelSize={6}
            linkColor={() => 'rgba(83, 103, 121, 0.25)'}
            linkWidth={1.5}
            backgroundColor="#ffffff"
            onNodeClick={(node: any) => setSelectedNode(node as GraphNode)}
            enableNodeDrag={true}
            enablePanInteraction={true}
            enableZoomInteraction={true}
          />
        )}
      </div>

      {/* Node Inspection Drawer */}
      {selectedNode && (
        <aside className="graph-node-drawer" aria-label="Node details">
          <div className="drawer-header">
            <span className={`tag ${selectedNode.type}`}>
              {selectedNode.type.toUpperCase()}
            </span>
            {selectedNode.evidence_kind && (
              <span className={`evidence ${selectedNode.evidence_kind === 'synthetic' ? 'synthetic' : ''}`}>
                {selectedNode.evidence_kind === 'synthetic' ? 'Synthetic sample' : 'Public evidence'}
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

          {selectedNode.origin && (
            <div className="drawer-origin">
              {safeOrigin(selectedNode.origin) ? (
                <a
                  href={safeOrigin(selectedNode.origin)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="external-link"
                >
                  <span>View public origin</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              ) : (
                <span className="muted">{selectedNode.origin}</span>
              )}
            </div>
          )}

          {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
            <div className="drawer-metadata">
              <h4>Structured facts</h4>
              {selectedNode.metadata.doi && (
                <p><strong>DOI:</strong> {selectedNode.metadata.doi}</p>
              )}
              {selectedNode.metadata.year && (
                <p><strong>Year:</strong> {selectedNode.metadata.year}</p>
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
                <p><strong>Department:</strong> {selectedNode.metadata.department}</p>
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

          <div className="drawer-actions">
            {selectedNode.type === 'topic' && onSearchTopic && (
              <button
                type="button"
                className="primary wide"
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
                {attachedSourceIds.includes(selectedNode.id) ? 'Attached to proposal' : 'Attach to open proposal'}
              </button>
            )}
          </div>
        </aside>
      )}
    </div>
  );
}
