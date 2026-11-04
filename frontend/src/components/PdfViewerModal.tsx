'use client';

import { useEffect, useState } from 'react';
import { X, ExternalLink, Download, FileText, Loader2 } from 'lucide-react';

type Props = {
  sourceId: string;
  title: string;
  onClose: () => void;
};

export default function PdfViewerModal({ sourceId, title, onClose }: Props) {
  const [loading, setLoading] = useState(true);
  const pdfUrl = `/api/v2/sources/${sourceId}/pdf`;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="pdf-modal-backdrop"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
      onClick={onClose}
    >
      <div
        className="pdf-modal-container"
        style={{
          width: '100%',
          maxWidth: '1100px',
          height: '90vh',
          background: '#ffffff',
          borderRadius: '12px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          border: '1px solid #cbd5e1',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* MODAL HEADER */}
        <div
          style={{
            padding: '12px 18px',
            borderBottom: '1px solid #e2e8f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: '#f8fafc',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
            <FileText className="w-4 h-4 text-rose-600 shrink-0" />
            <h3
              style={{
                fontSize: '13px',
                fontWeight: 600,
                color: '#0f172a',
                margin: 0,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
              title={title}
            >
              {title}
            </h3>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: '11px',
                color: '#3b82f6',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                textDecoration: 'none',
                fontWeight: 500,
                padding: '4px 8px',
                borderRadius: '4px',
                border: '1px solid #bfdbfe',
                background: '#eff6ff',
              }}
              title="Open full PDF in new tab"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Open Tab</span>
            </a>

            <a
              href={pdfUrl}
              download
              style={{
                fontSize: '11px',
                color: '#475569',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                textDecoration: 'none',
                fontWeight: 500,
                padding: '4px 8px',
                borderRadius: '4px',
                border: '1px solid #cbd5e1',
                background: '#ffffff',
              }}
              title="Download PDF file"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download</span>
            </a>

            <button
              type="button"
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '4px',
                borderRadius: '4px',
                color: '#64748b',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              title="Close PDF viewer (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* MODAL BODY WITH IFRAME */}
        <div style={{ flex: 1, position: 'relative', background: '#334155' }}>
          {loading && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                gap: '8px',
                zIndex: 1,
              }}
            >
              <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
              <span style={{ fontSize: '12px' }}>Loading document stream…</span>
            </div>
          )}

          <iframe
            src={pdfUrl}
            onLoad={() => setLoading(false)}
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
            }}
            title={title}
          />
        </div>
      </div>
    </div>
  );
}
