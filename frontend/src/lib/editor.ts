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
