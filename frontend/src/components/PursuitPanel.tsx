'use client';

import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { api, type Eligibility, type Opportunity, type Outcome, type OutcomeState, type Proposal, type Pursuit, type PursuitState } from '@/lib/api';
import { safeOrigin } from '@/lib/editor';
import { isTerminal, localDeadline, outcomeAttempt, RequestScope, type OutcomeAttempt } from '@/lib/pursuits';

type Props = { proposal: Pick<Proposal, 'id' | 'team_id' | 'role'> };
const failure = (error: unknown) => error instanceof Error ? error.message : 'The request failed. Try again.';
const timestamp = (value: string) => new Date(value).toLocaleString();

// A new proposal gets a new form instance before any asynchronous reads finish.
export default function PursuitPanel({ proposal }: Props) {
  return <ProposalPursuit key={proposal.id} proposal={proposal} />;
}

function ProposalPursuit({ proposal }: Props) {
  const [loading, setLoading] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [pursuit, setPursuit] = useState<Pursuit | null>(null);
  const [outcomes, setOutcomes] = useState<Outcome[]>([]);
  const [opportunityId, setOpportunityId] = useState('');
  const [state, setState] = useState<PursuitState>('draft');
  const [title, setTitle] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [deadline, setDeadline] = useState('');
  const [notes, setNotes] = useState('');
  const [eligibility, setEligibility] = useState<Eligibility>('unknown');
  const [outcome, setOutcome] = useState<OutcomeState>('won');
  const [awardReference, setAwardReference] = useState('');
  const [timezone, setTimezone] = useState('your browser timezone');
  const requests = useRef(new RequestScope());
  const attempt = useRef<OutcomeAttempt | null>(null);
  const terminal = isTerminal(pursuit?.state) || outcomes.length > 0;
  const editable = proposal.role === 'owner' || proposal.role === 'editor';
  const locked = loading || !loaded || busy || !editable || terminal;
  const progressValue = terminal ? pursuit?.state ?? outcomes[0]?.outcome : state;
  const opportunity = opportunities.find(item => item.id === opportunityId);

  const refresh = useCallback(async () => {
    const scope = requests.current;
    const generation = scope.begin();
    setLoading(true); setLoaded(false); setError('');
    try {
      const [opportunityList, current, outcomeList] = await Promise.all([api.opportunities(), api.pursuit(proposal.id), api.outcomes(proposal.id)]);
      if (!scope.current(generation)) return;
      setOpportunities(opportunityList.items.filter(item => item.team_id === proposal.team_id));
      setPursuit(current.pursuit); setOutcomes(outcomeList.items); setLoaded(true);
      setOpportunityId(current.pursuit?.opportunity_id ?? '');
      setState(current.pursuit && !isTerminal(current.pursuit.state) ? current.pursuit.state as PursuitState : 'draft');
      setTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone);
    } catch (error) { if (scope.current(generation)) setError(failure(error)); }
    finally { if (scope.current(generation)) { setLoading(false); setBusy(false); } }
  }, [proposal.id, proposal.team_id]);

  useEffect(() => {
    const scope = requests.current;
    void refresh();
    return () => scope.invalidate();
  }, [refresh]);

  const run = async (action: (current: () => boolean) => Promise<void>) => {
    const scope = requests.current;
    const generation = scope.begin();
    setBusy(true); setError(''); setNotice('');
    try { await action(() => scope.current(generation)); }
    catch (error) { if (scope.current(generation)) setError(failure(error)); }
    finally { if (scope.current(generation)) setBusy(false); }
  };
  const submit = (event: FormEvent, action: (current: () => boolean) => Promise<void>) => {
    event.preventDefault(); void run(action);
  };

  return <section className="discovery pursuit-panel" aria-labelledby="pursuit-heading">
    <div className="section-heading"><div><h2 id="pursuit-heading">Opportunity and outcome</h2><p className="muted">Keep a manual record of this proposal’s progress.</p></div><button disabled={busy || loading} onClick={() => void refresh()}>Refresh tracking</button></div>
    <p className="muted">Recording “submitted” here does not submit anything to a funding portal. Unknown results remain submitted until you record an outcome.</p>
    {loading && <p role="status" className="empty">Loading proposal tracking…</p>}
    {busy && <p role="status" className="muted">Saving tracking record…</p>}
    {error && <p className="alert error" role="alert">{error}</p>}
    {notice && <p className="success" role="status">{notice}</p>}
    {!loading && loaded && <>
      <p className="tracking-status">Current status: <strong>{pursuit?.state ?? 'Not tracked'}</strong></p>
      <form onSubmit={event => submit(event, async current => {
        const saved = await api.updatePursuit(proposal.id, { state, opportunity_id: opportunityId || null });
        if (!current()) return;
        setPursuit(saved.pursuit); setNotice('Proposal progress saved.');
      })}>
        <fieldset disabled={locked} className="tracking-fields"><label>Linked opportunity<select value={opportunityId} onChange={event => setOpportunityId(event.target.value)}><option value="">No linked opportunity</option>{opportunities.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label><label>Proposal progress<select value={progressValue} onChange={event => setState(event.target.value as PursuitState)}>{terminal && <option value={progressValue}>Final outcome: {progressValue}</option>}<option value="draft">Draft</option><option value="shortlisted">Shortlisted</option><option value="collaborating">Collaborating</option><option value="submitted">Submitted (manually recorded)</option></select></label></fieldset>
        <button className="tracking-save" disabled={locked}>Save proposal progress</button>
      </form>
      {opportunity && <div className="opportunity-summary"><h3>{opportunity.title}</h3><p>Eligibility: {opportunity.eligibility === 'unknown' ? 'Unknown; verify with the opportunity provider' : opportunity.eligibility}</p><p>{opportunity.deadline ? `Deadline: ${timestamp(opportunity.deadline)} (your local time)${opportunity.deadline_timezone ? `; recorded timezone ${opportunity.deadline_timezone}` : ''}` : 'Deadline: unknown'}</p>{opportunity.source_url && safeOrigin(opportunity.source_url) && <a href={safeOrigin(opportunity.source_url)} target="_blank" rel="noopener noreferrer">View opportunity source</a>}{opportunity.notes && <p className="tracking-notes">{opportunity.notes}</p>}</div>}
      {!terminal && editable && <details className="tracking-create"><summary>Add a manual opportunity</summary><form onSubmit={event => submit(event, async current => {
        const saved = await api.createOpportunity({ team_id: proposal.team_id, title: title.trim(), source_url: sourceUrl.trim() || null, ...localDeadline(deadline), notes, eligibility });
        if (!current()) return;
        setOpportunities(previous => [...previous, saved]); setOpportunityId(saved.id);
        setTitle(''); setSourceUrl(''); setDeadline(''); setNotes(''); setEligibility('unknown');
        setNotice('Opportunity added to your team. Save proposal progress to link it to this proposal.');
      })}><fieldset disabled={busy || loading} className="tracking-form"><label>Opportunity title<input value={title} onChange={event => setTitle(event.target.value)} required maxLength={300} /></label><label>Opportunity source URL (optional)<input type="url" pattern="https?://.*" value={sourceUrl} onChange={event => setSourceUrl(event.target.value)} placeholder="https://…" maxLength={2000} /></label><label>Deadline (optional, {timezone})<input type="datetime-local" value={deadline} onChange={event => setDeadline(event.target.value)} /></label><p className="muted">Leave blank when unknown. The entered time uses your browser’s detected timezone ({timezone}).</p><label>Eligibility<select value={eligibility} onChange={event => setEligibility(event.target.value as Eligibility)}><option value="unknown">Unknown</option><option value="eligible">Eligible (manually verified)</option><option value="ineligible">Ineligible (manually verified)</option></select></label><label>Opportunity notes<textarea rows={3} value={notes} onChange={event => setNotes(event.target.value)} maxLength={10000} /></label></fieldset><button disabled={busy || loading || !title.trim()}>Add opportunity</button></form></details>}
      <div className="outcome-record"><h3>Record an outcome</h3>{terminal ? <p className="muted">A final outcome has been recorded. Progress and outcome records are read-only.</p> : <><p className="muted">Record submission first. A result is never inferred from a missing response.</p><form onSubmit={event => submit(event, async current => {
        const reference = awardReference.trim() || null;
        const retry = outcomeAttempt(attempt.current, proposal.id, outcome, reference, crypto.randomUUID());
        attempt.current = retry;
        const stored = await api.recordOutcome(proposal.id, { outcome, award_reference: reference, idempotency_key: retry.key });
        if (!current()) return;
        setOutcomes(previous => [...previous.filter(item => item.id !== stored.id), stored]);
        setPursuit(previous => previous ? { ...previous, state: stored.outcome } : previous);
        setNotice('Outcome recorded.');
        try {
          const updated = await api.pursuit(proposal.id);
          if (current()) setPursuit(updated.pursuit);
        } catch { if (current()) setError('Outcome recorded, but its history could not be refreshed. Use Refresh tracking to load the saved history.'); }
      })}><fieldset disabled={locked || pursuit?.state !== 'submitted'} className="tracking-fields"><label>Outcome<select value={outcome} onChange={event => setOutcome(event.target.value as OutcomeState)}><option value="won">Won</option><option value="lost">Lost</option><option value="withdrawn">Withdrawn</option></select></label><label>Award or decision reference (optional)<input value={awardReference} onChange={event => setAwardReference(event.target.value)} maxLength={1000} /></label></fieldset><button disabled={locked || pursuit?.state !== 'submitted'}>Record final outcome</button></form></>}
        {outcomes.map(record => <article className="outcome-item" key={record.id}><strong>{record.outcome}</strong><span className="muted">Recorded {timestamp(record.recorded_at)}</span>{record.award_reference && <p>{record.award_reference}</p>}</article>)}
      </div>
      {pursuit && <details className="tracking-history"><summary>Progress history ({pursuit.history.length})</summary>{pursuit.history.length ? <ol>{pursuit.history.map(item => <li key={item.id}><span>{item.from_state ?? 'Not tracked'} → {item.to_state}</span><small>{timestamp(item.recorded_at)}</small></li>)}</ol> : <p className="muted">No state changes recorded.</p>}</details>}
      {!editable && <p className="muted">Viewer access. An owner or editor can update this tracking record.</p>}
    </>}
  </section>;
}
