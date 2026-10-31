'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { api, type Proposal, type ShortlistEntry, type Team } from '@/lib/api';
import { safeOrigin } from '@/lib/editor';
import { RequestScope } from '@/lib/pursuits';
import { canAttachToProposal, sourceKindLabel } from '@/lib/shortlist';

type Props = {
  team: Team;
  proposal: Pick<Proposal, 'id' | 'team_id' | 'role'> | null;
  attachedSourceIds: string[];
  refreshVersion: number;
  workspaceBusy: boolean;
  noteDrafts: Record<string, string>;
  onNoteChange: (entryId: string, value: string, savedNote: string) => void;
  onNoteSaved: (entryId: string, savedNote: string) => void;
  onRemove: (entryId: string) => void;
  onAttach: (sourceId: string) => Promise<void>;
};

export default function ShortlistPanel(props: Props) {
  return <TeamShortlist key={props.team.id} {...props} />;
}

function TeamShortlist({ team, proposal, attachedSourceIds, refreshVersion, workspaceBusy, noteDrafts, onNoteChange, onNoteSaved, onRemove, onAttach }: Props) {
  const [items, setItems] = useState<ShortlistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const scope = useRef(new RequestScope());
  const editable = team.role === 'owner' || team.role === 'editor';
  const attachable = canAttachToProposal(team.id, proposal);
  const disabled = busy || workspaceBusy || loading;

  const refresh = useCallback(async () => {
    const requests = scope.current;
    const generation = requests.begin();
    setLoading(true); setError('');
    try {
      const result = await api.shortlist(team.id);
      if (!requests.current(generation)) return;
      setItems(result.items);
    } catch (error) {
      if (requests.current(generation)) { setItems([]); setError(error instanceof Error ? error.message : 'Could not load the team shortlist.'); }
    } finally { if (requests.current(generation)) { setLoading(false); setBusy(false); } }
  }, [team.id]);

  useEffect(() => {
    const requests = scope.current;
    void refresh();
    return () => requests.invalidate();
  }, [refresh, refreshVersion]);

  const run = async (action: (current: () => boolean) => Promise<void>) => {
    const requests = scope.current;
    const generation = requests.begin();
    setBusy(true); setError(''); setNotice('');
    try { await action(() => requests.current(generation)); }
    catch (error) { if (requests.current(generation)) setError(error instanceof Error ? error.message : 'The shortlist change failed.'); }
    finally { if (requests.current(generation)) setBusy(false); }
  };

  return <section className="discovery shortlist-panel" aria-labelledby="shortlist-heading">
    <div className="section-heading"><div><h2 id="shortlist-heading">Team shortlist</h2><p className="muted">Saved evidence for {team.name}. Save papers, author evidence, and sample candidates before starting a proposal.</p></div><button disabled={disabled} onClick={() => void refresh()}>Refresh shortlist</button></div>
    {loading && <p className="empty" role="status">Loading team shortlist…</p>}
    {busy && <p className="muted" role="status">Updating shortlist…</p>}
    {error && <p className="alert error" role="alert">{error}</p>}
    {notice && <p className="success" role="status">{notice}</p>}
    {!loading && !error && !items.length && <p className="empty">No saved items yet. Search below and choose Shortlist to save evidence for this team.</p>}
    {!loading && items.map(item => <article className="shortlist-item" key={item.id}>
      <div className="result-meta"><span className="tag">{sourceKindLabel(item.kind, item.evidence_kind)}</span><span className={`evidence ${item.evidence_kind === 'synthetic' ? 'synthetic' : ''}`}>{item.evidence_kind === 'synthetic' ? 'Synthetic sample' : 'Public evidence'}</span><small>Version {item.version}</small></div>
      <h3>{item.title}</h3><p className="shortlist-snippet">{item.snippet}</p>
      <p className="muted shortlist-origin">{item.origin}</p>{safeOrigin(item.origin) && <a href={safeOrigin(item.origin)} target="_blank" rel="noopener noreferrer">View shortlist source</a>}
      <label className="shortlist-note">Note for {item.title}<textarea rows={2} value={noteDrafts[item.id] ?? item.note} maxLength={2000} disabled={!editable || disabled} onChange={event => onNoteChange(item.id, event.target.value, item.note)} /></label>
      <div className="button-row">{editable && <><button disabled={disabled || (noteDrafts[item.id] ?? item.note) === item.note} onClick={() => void run(async current => {
        const saved = await api.updateShortlist(team.id, item.id, noteDrafts[item.id] ?? item.note);
        onNoteSaved(saved.id, saved.note);
        if (current()) { setItems(previous => previous.map(entry => entry.id === saved.id ? saved : entry)); setNotice('Shortlist note saved.'); }
      })}>Save note</button><button disabled={disabled} onClick={() => void run(async current => {
        await api.removeShortlist(team.id, item.id);
        onRemove(item.id);
        if (current()) { setItems(previous => previous.filter(entry => entry.id !== item.id)); setNotice('Item removed from this team shortlist.'); }
      })}>Remove from shortlist</button></>}
      <button disabled={disabled || !attachable || attachedSourceIds.includes(item.source_id)} onClick={() => void run(async () => { await onAttach(item.source_id); })}>{attachedSourceIds.includes(item.source_id) && attachable ? 'Attached to open proposal' : 'Attach saved source'}</button></div>
    </article>)}
    {!attachable && <p className="muted">Open an editable proposal in this team to attach a saved source.</p>}
    {!editable && <p className="muted">Viewer access. An owner or editor can curate this shortlist.</p>}
  </section>;
}
