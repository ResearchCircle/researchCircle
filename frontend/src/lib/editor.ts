import type { DraftJob, Proposal, SourceRef } from './api';

export function hasEdits(proposal: Proposal, title: string, content: string, sourceIds: string[]): boolean {
  const saved = proposal.selected_sources.map(source => source.id).sort();
  return proposal.title !== title || proposal.content !== content || saved.join(',') !== [...sourceIds].sort().join(',');
}

function sameSourceRefs(left: SourceRef[], right: SourceRef[]): boolean {
  if (!Array.isArray(left) || !Array.isArray(right) || left.length !== right.length) return false;
  const valid = (refs: SourceRef[]) => refs.every(ref => ref && typeof ref.id === 'string' && typeof ref.version === 'string' && typeof ref.content_hash === 'string') && new Set(refs.map(ref => ref.id)).size === refs.length;
  if (!valid(left) || !valid(right)) return false;
  const expected = new Map(right.map(ref => [ref.id, ref]));
  return left.every(ref => expected.get(ref.id)?.version === ref.version && expected.get(ref.id)?.content_hash === ref.content_hash);
}

export function canApplyDraft(job: DraftJob, proposal: Proposal, dirty: boolean): boolean {
  return job.state === 'succeeded' && !!job.output && job.proposal_id === proposal.id && job.base_revision === proposal.revision && job.output.base_revision === proposal.revision && !dirty
    && sameSourceRefs(job.source_refs, proposal.selected_sources) && sameSourceRefs(job.source_refs, job.output.source_refs);
}

export function appendSuggestion(content: string, text: string): string {
  return content.trimEnd() ? `${content.trimEnd()}\n\n${text}` : text;
}

export function safeOrigin(origin: string): string | undefined {
  try { const url = new URL(origin); return ['https:', 'http:'].includes(url.protocol) ? url.href : undefined; } catch { return undefined; }
}

export function renderMarkdownSimple(markdown: string): string {
  if (!markdown) return '<p style="color:#94a3b8;font-style:italic;">No proposal content drafted yet. Use the formatting toolbar or insert a template to get started.</p>';
  const lines = markdown.split('\n');
  const htmlLines: string[] = [];
  let inCode = false;
  let inList = false;

  for (const line of lines) {
    if (line.startsWith('```')) {
      if (inCode) {
        htmlLines.push('</code></pre>');
        inCode = false;
      } else {
        htmlLines.push('<pre class="editor-code-block" style="background:#0f172a;color:#f8fafc;padding:12px;border-radius:6px;overflow-x:auto;margin:12px 0;"><code>');
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      htmlLines.push(line.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'));
      continue;
    }

    if (line.startsWith('# ')) {
      htmlLines.push(`<h1 class="preview-h1" style="font-size:22px;font-weight:700;color:#0f172a;margin:20px 0 10px;border-bottom:1px solid #e2e8f0;padding-bottom:6px;">${escapeAndFormat(line.slice(2))}</h1>`);
    } else if (line.startsWith('## ')) {
      htmlLines.push(`<h2 class="preview-h2" style="font-size:18px;font-weight:600;color:#1e293b;margin:16px 0 8px;">${escapeAndFormat(line.slice(3))}</h2>`);
    } else if (line.startsWith('### ')) {
      htmlLines.push(`<h3 class="preview-h3" style="font-size:15px;font-weight:600;color:#334155;margin:12px 0 6px;">${escapeAndFormat(line.slice(4))}</h3>`);
    } else if (line.startsWith('> ')) {
      htmlLines.push(`<blockquote class="preview-quote" style="border-left:3px solid #3b82f6;padding:6px 14px;background:#f8fafc;color:#475569;margin:10px 0;font-style:italic;">${escapeAndFormat(line.slice(2))}</blockquote>`);
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      if (!inList) {
        htmlLines.push('<ul class="preview-ul" style="list-style-type:disc;padding-left:22px;margin:8px 0;">');
        inList = true;
      }
      htmlLines.push(`<li style="margin-bottom:4px;color:#334155;">${escapeAndFormat(line.slice(2))}</li>`);
    } else if (/^\d+\.\s/.test(line)) {
      htmlLines.push(`<div class="preview-num-item" style="padding-left:6px;margin:4px 0;color:#334155;">${escapeAndFormat(line)}</div>`);
    } else if (!line.trim()) {
      if (inList) {
        htmlLines.push('</ul>');
        inList = false;
      }
      htmlLines.push('<div class="preview-spacer" style="height:10px;"></div>');
    } else {
      if (inList) {
        htmlLines.push('</ul>');
        inList = false;
      }
      htmlLines.push(`<p class="preview-p" style="margin:6px 0;line-height:1.6;color:#334155;">${escapeAndFormat(line)}</p>`);
    }
  }
  if (inList) htmlLines.push('</ul>');
  if (inCode) htmlLines.push('</code></pre>');
  return htmlLines.join('\n');
}

function escapeAndFormat(text: string): string {
  let s = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong style="font-weight:600;color:#0f172a;">$1</strong>');
  s = s.replace(/\*(.+?)\*/g, '<em>$1</em>');
  s = s.replace(/`([^`]+)`/g, '<code style="background:#f1f5f9;padding:2px 5px;border-radius:4px;font-size:12px;color:#0f766e;">$1</code>');
  return s;
}
