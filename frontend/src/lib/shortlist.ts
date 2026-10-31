import type { Proposal } from './api';

export function canChangeTeam(current: string, next: string, dirty: boolean, confirm: () => boolean): boolean {
  return current === next || !dirty || confirm();
}

export function canAttachToProposal(teamId: string, proposal: Pick<Proposal, 'team_id' | 'role'> | null): boolean {
  return !!proposal && proposal.team_id === teamId && (proposal.role === 'owner' || proposal.role === 'editor');
}

export function sourceKindLabel(kind: 'paper' | 'researcher', evidence: 'public' | 'synthetic'): string {
  return kind === 'researcher' ? evidence === 'synthetic' ? 'Researcher example' : 'Listed author' : 'Paper';
}

export type ShortlistDrafts = Record<string, Record<string, string>>;

export function editShortlistDraft(drafts: ShortlistDrafts, teamId: string, entryId: string, value: string, savedNote: string): ShortlistDrafts {
  const team = { ...drafts[teamId] };
  if (value === savedNote) delete team[entryId];
  else team[entryId] = value;
  return { ...drafts, [teamId]: team };
}

export function acknowledgeShortlistDraft(drafts: ShortlistDrafts, teamId: string, entryId: string, savedNote: string): ShortlistDrafts {
  return drafts[teamId]?.[entryId] === savedNote ? editShortlistDraft(drafts, teamId, entryId, savedNote, savedNote) : drafts;
}
