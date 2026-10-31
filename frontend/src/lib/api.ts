export type User = { id: string; email: string; name: string };
export type Team = { id: string; name: string; role: 'owner' | 'editor' | 'viewer' };
export type Invitation = { id: string; team_id: string; team_name: string; role: string };
export type SourceRef = { id: string; version: string; content_hash: string };
export type SourceSnapshot = SourceRef & { title: string; origin: string; text: string; proposal_id: string | null; is_public: boolean };
export type Proposal = { id: string; team_id: string; title: string; content: string; revision: number; role: Team['role']; selected_sources: SourceRef[]; updated_at: string };
export type SearchResult = SourceRef & { source_id: string; title: string; snippet: string; origin: string; score: number; reason: string; kind: 'paper' | 'researcher'; evidence_kind: 'public' | 'synthetic'; text: string };
export type SearchPage = { items: SearchResult[]; degraded: boolean; next_cursor: string | null };
export type Citation = { source_id: string; version: string; content_hash: string; title: string; origin: string; quote: string };
export type DraftResult = { text: string; citations: Citation[]; base_revision: number; source_refs: SourceRef[]; model_id: string | null; insufficient_evidence: boolean; finish_reason: string };
export type DraftJob = { id: string; proposal_id: string; base_revision: number; source_refs: SourceRef[]; state: 'queued' | 'running' | 'succeeded' | 'failed'; output: DraftResult | null; error: { code: string; message: string; retryable?: boolean } | null; created_at: string; started_at: string | null; finished_at: string | null };
export type SaveInput = { expected_revision: number; title: string; content: string; selected_source_ids: string[] };

export type ShortlistEntry = { id: string; team_id: string; source_id: string; version: string; content_hash: string; title: string; snippet: string; origin: string; kind: 'paper' | 'researcher'; evidence_kind: 'public' | 'synthetic'; note: string; created_at: string; created_by: string };

export type Eligibility = 'unknown' | 'eligible' | 'ineligible';
export type PursuitState = 'draft' | 'shortlisted' | 'collaborating' | 'submitted';
export type OutcomeState = 'won' | 'lost' | 'withdrawn';
export type OpportunityInput = { team_id: string; title: string; source_url: string | null; deadline: string | null; deadline_timezone: string | null; notes: string; eligibility: Eligibility };
export type Opportunity = OpportunityInput & { id: string; created_at: string };
export type Pursuit = { id: string; proposal_id: string; opportunity_id: string | null; state: PursuitState | OutcomeState; updated_at: string; history: { id: string; from_state: string | null; to_state: string; user_id: string; recorded_at: string }[] };
export type Outcome = { id: string; pursuit_id: string; outcome: OutcomeState; award_reference: string | null; recorded_at: string };
export type OutcomeInput = { outcome: OutcomeState; idempotency_key: string; award_reference: string | null };

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public retryable = false) { super(message); this.name = 'ApiError'; }
}

async function responseFor(path: string, options: RequestInit = {}): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(`/api/v2${path}`, { ...options, credentials: 'same-origin', cache: 'no-store', headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers } });
  } catch {
    throw new ApiError(0, 'network_error', 'Could not reach the server. Check your connection and try again.', true);
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body?.error?.code ?? 'request_failed', body?.error?.message ?? `Request failed (${response.status}).`, body?.error?.retryable ?? false);
  }
  return response;
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await responseFor(path, options);
  return response.status === 204 ? undefined as T : response.json();
}
const post = <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
export const api = {
  shortlist: (teamId: string) => request<{ items: ShortlistEntry[] }>(`/teams/${teamId}/shortlist`),
  addShortlist: (teamId: string, sourceId: string, note?: string) => post<ShortlistEntry>(`/teams/${teamId}/shortlist`, { source_id: sourceId, ...(note === undefined ? {} : { note }) }),
  updateShortlist: (teamId: string, entryId: string, note: string) => request<ShortlistEntry>(`/teams/${teamId}/shortlist/${entryId}`, { method: 'PATCH', body: JSON.stringify({ note }) }),
  removeShortlist: (teamId: string, entryId: string) => request<void>(`/teams/${teamId}/shortlist/${entryId}`, { method: 'DELETE' }),
  opportunities: () => request<{ items: Opportunity[] }>('/opportunities'),
  createOpportunity: (body: OpportunityInput) => post<Opportunity>('/opportunities', body),
  pursuit: (id: string) => request<{ pursuit: Pursuit | null }>(`/proposals/${id}/pursuit`),
  updatePursuit: (id: string, body: { state: PursuitState; opportunity_id: string | null }) => request<{ pursuit: Pursuit }>(`/proposals/${id}/pursuit`, { method: 'PUT', body: JSON.stringify(body) }),
  outcomes: (id: string) => request<{ items: Outcome[] }>(`/proposals/${id}/outcomes`),
  recordOutcome: (id: string, body: OutcomeInput) => post<Outcome>(`/proposals/${id}/outcomes`, body),
  me: () => request<{ user: User }>('/auth/me'),
  authenticate: (mode: 'login' | 'register', body: { email: string; password: string; name?: string }) => post<{ user: User }>(`/auth/${mode}`, body),
  logout: () => post<void>('/auth/logout'),
  teams: () => request<{ items: Team[] }>('/teams'),
  createTeam: (name: string) => post<Team>('/teams', { name }),
  invite: (team: string, email: string, role: 'editor' | 'viewer') => post(`/teams/${team}/invitations`, { email, role }),
  invitations: () => request<{ items: Invitation[] }>('/invitations'),
  accept: (id: string) => post<{ team_id: string }>(`/invitations/${id}/accept`),
  proposals: () => request<{ items: Proposal[] }>('/proposals'),
  createProposal: (team_id: string, title: string) => post<Proposal>('/proposals', { team_id, title, content: '' }),
  proposal: (id: string) => request<Proposal>(`/proposals/${id}`),
  save: (id: string, body: SaveInput) => request<Proposal>(`/proposals/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  exportMarkdown: async (id: string) => (await responseFor(`/proposals/${id}/export`)).blob(),
  sources: (id: string) => request<{ items: SourceSnapshot[] }>(`/proposals/${id}/sources`),
  addSource: (id: string, body: { title: string; text: string; origin: string }) => post<SourceSnapshot>(`/proposals/${id}/sources`, body),
  attach: (id: string, source_id: string) => post<SourceSnapshot>(`/proposals/${id}/sources/attach`, { source_id }),
  search: (q: string) => request<SearchPage>(`/search?q=${encodeURIComponent(q)}`),
  jobs: (id: string) => request<{ items: DraftJob[] }>(`/proposals/${id}/jobs`),
  draft: (id: string, body: { section: string; instruction: string; source_ids: string[] }) => post<DraftJob>(`/proposals/${id}/jobs`, body),
  job: (id: string) => request<DraftJob>(`/jobs/${id}`),
  cancel: (id: string) => post<DraftJob>(`/jobs/${id}/cancel`),
};
