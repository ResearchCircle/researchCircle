'use client';

import { BookOpen, ExternalLink, FileText, Quote, Sparkles } from 'lucide-react';
import type { ChatCitation } from '@/lib/api';
import { safeOrigin } from '@/lib/editor';

function OriginLink({ value }: { value: string }) {
  const href = safeOrigin(value);
  return href ? (
    <a href={href} target="_blank" rel="noopener noreferrer" className="external-link">
      <span>View public origin</span>
      <ExternalLink className="w-3 h-3" />
    </a>
  ) : (
    <span className="muted">{value || 'No link'}</span>
  );
}

export default function CitationPanel({
  citations,
  selectedSourceId,
  onSelectSource,
  onViewPdf,
}: {
  citations: ChatCitation[];
  selectedSourceId?: string | null;
  onSelectSource?: (id: string) => void;
  onViewPdf?: (sourceId: string, title: string) => void;
}) {
  if (!citations || citations.length === 0) {
    return (
      <div className="citation-panel-empty">
        <div className="empty-icon-circle small">
          <BookOpen className="w-5 h-5 text-[#536779]" />
        </div>
        <h4>No Active Citations</h4>
        <p className="muted small">
          Ask questions in Research Chat. Grounded citations with verbatim source excerpts will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="citation-panel-container">
      <div className="citation-panel-header">
        <div className="header-title">
          <Sparkles className="w-4 h-4 text-[#14766d]" />
          <h4>Verified Citations ({citations.length})</h4>
        </div>
        <span className="count-pill">{citations.length}</span>
      </div>

      <div className="citation-cards-scroll">
        {citations.map((c, index) => {
          const isSelected = selectedSourceId === c.source_id;
          return (
            <article
              key={`${c.source_id}-${index}`}
              className={`citation-card ${isSelected ? 'highlighted' : ''}`}
              onClick={() => onSelectSource?.(c.source_id)}
            >
              <div className="citation-card-top">
                <span className="citation-index-badge">[{index + 1}]</span>
                <span className="version-tag">Ver {c.version.slice(0, 8)}</span>
              </div>

              <h5 className="citation-title">{c.title}</h5>

              {c.quote && (
                <div className="citation-quote-box">
                  <Quote className="w-3 h-3 text-[#14766d] shrink-0" />
                  <p className="quote-text">“{c.quote}”</p>
                </div>
              )}

              <div className="citation-card-footer" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px' }}>
                <OriginLink value={c.origin} />
                {onViewPdf && (
                  <button
                    type="button"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '11px',
                      color: '#0284c7',
                      background: '#f0f9ff',
                      border: '1px solid #bae6fd',
                      borderRadius: '4px',
                      padding: '2px 6px',
                      cursor: 'pointer',
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onViewPdf(c.source_id, c.title);
                    }}
                    title="Read full PDF paper"
                  >
                    <FileText className="w-3 h-3 text-sky-600" />
                    <span>Read PDF</span>
                  </button>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
