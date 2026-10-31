import type { DraftJob, Proposal } from './api';

export function hasEdits(proposal: Proposal, title: string, content: string, sourceIds: string[]): boolean {
  const saved = proposal.selected_sources.map(source => source.id).sort();
  return proposal.title !== title || proposal.content !== content || saved.join(',') !== [...sourceIds].sort().join(',');
}

export function canApplyDraft(job: DraftJob, proposal: Proposal, dirty: boolean): boolean {
  return job.state === 'succeeded' && !!job.output && job.proposal_id === proposal.id && job.base_revision === proposal.revision && job.output.base_revision === proposal.revision && !dirty;
}

export function appendSuggestion(content: string, text: string): string {
  return content.trimEnd() ? `${content.trimEnd()}\n\n${text}` : text;
}

export function safeOrigin(origin: string): string | undefined {
  try { const url = new URL(origin); return ['https:', 'http:'].includes(url.protocol) ? url.href : undefined; } catch { return undefined; }
}
