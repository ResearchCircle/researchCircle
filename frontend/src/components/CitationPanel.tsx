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
        <h4>No citations yet</h4>
        <p className="muted small">
          When you ask a question in Research Chat, the exact passages used to answer it will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="citation-panel-container">
      <div className="citation-panel-header">
        <div className="header-title">
          <Sparkles className="w-4 h-4 text-[#14766d]" />
          <h4>Sources ({citations.length})</h4>
        </div>
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
                <span className="citation-index-badge">{index + 1}</span>
                <h5 className="citation-title">{c.title}</h5>
              </div>

              {c.quote && (
                <div className="citation-quote-box">
                  <Quote className="w-3 h-3 text-[#14766d] shrink-0" aria-hidden="true" />
                  <p className="quote-text">{c.quote}</p>
                </div>
              )}

              <div className="citation-card-footer">
                <OriginLink value={c.origin} />
                {onViewPdf && c.has_pdf && (
                  <button
                    type="button"
                    className="citation-pdf-button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onViewPdf(c.source_id, c.title);
                    }}
                    title="Read full PDF paper"
                  >
                    <FileText className="w-3 h-3" aria-hidden="true" />
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
