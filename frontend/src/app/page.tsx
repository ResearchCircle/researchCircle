'use client';

import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { api, ApiError, type DraftJob, type Invitation, type Proposal, type SearchPage, type SourceSnapshot, type Team, type User } from '@/lib/api';
import { appendSuggestion, canApplyDraft, hasEdits, safeOrigin } from '@/lib/editor';
import PursuitPanel from '@/components/PursuitPanel';
import ShortlistPanel from '@/components/ShortlistPanel';
import { canChangeTeam, canAttachToProposal, sourceKindLabel, editShortlistDraft, acknowledgeShortlistDraft, type ShortlistDrafts } from '@/lib/shortlist';

function Origin({ value }: { value: string }) {
  const href = safeOrigin(value);
  return href ? <a href={href} target="_blank" rel="noopener noreferrer">View source</a> : <span className="muted">{value || 'No external link'}</span>;
}
function message(error: unknown) { return error instanceof Error ? error.message : 'The request failed. Try again.'; }

export default function Workspace() {
  const [checking, setChecking] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useState('');
  const [teamName, setTeamName] = useState('');
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'editor' | 'viewer'>('editor');
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [newTitle, setNewTitle] = useState('');
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [sources, setSources] = useState<SourceSnapshot[]>([]);
  const [jobs, setJobs] = useState<DraftJob[]>([]);
  const [jobId, setJobId] = useState('');
  const [conflict, setConflict] = useState<Proposal | null>(null);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchPage | null>(null);
  const [sourceTitle, setSourceTitle] = useState('');
  const [sourceText, setSourceText] = useState('');
  const [sourceOrigin, setSourceOrigin] = useState('');
  const [section, setSection] = useState('Research approach');
  const [instruction, setInstruction] = useState('');
  const [pollError, setPollError] = useState('');
  const [shortlistVersion, setShortlistVersion] = useState(0);
  const [shortlistDrafts, setShortlistDrafts] = useState<ShortlistDrafts>({});
  const shortlistDirty = Object.values(shortlistDrafts).some(notes => Object.keys(notes).length > 0);
  const dirty = !!proposal && hasEdits(proposal, title, content, selected);
  const editable = proposal?.role !== 'viewer';
  const job = jobs.find(item => item.id === jobId) ?? jobs[0];
  const opening = useRef(0);
  const selectedTeam = teams.find(team => team.id === teamId);

  const clearEditor = useCallback(() => {
    ++opening.current;
    setProposal(null); setTitle(''); setContent(''); setSelected([]);
    setSources([]); setJobs([]); setJobId(''); setConflict(null); setPollError('');
    setSourceTitle(''); setSourceText(''); setSourceOrigin('');
    setSection('Research approach'); setInstruction(''); setNewTitle(''); setInviteEmail('');
  }, []);

  const refreshLists = useCallback(async () => {
    const [teamList, proposalList, inbox] = await Promise.all([api.teams(), api.proposals(), api.invitations()]);
    setTeams(teamList.items); setProposals(proposalList.items); setInvitations(inbox.items);
    setTeamId(previous => teamList.items.some(item => item.id === previous) ? previous : teamList.items[0]?.id ?? '');
  }, []);

  useEffect(() => {
    let active = true;
    api.me().then(result => { if (active) setUser(result.user); }).catch(err => {
      if (active && !(err instanceof ApiError && err.status === 401)) setError(message(err));
    }).finally(() => { if (active) setChecking(false); });
    return () => { active = false; };
  }, []);
  useEffect(() => { if (user) refreshLists().catch(err => setError(message(err))); }, [user, refreshLists]);
  useEffect(() => {
    if (!dirty && !shortlistDirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty, shortlistDirty]);

  const run = async (action: () => Promise<void>) => {
    setBusy(true); setError(''); setNotice('');
    try { await action(); } catch (err) { setError(message(err)); } finally { setBusy(false); }
  };
  const install = (next: Proposal) => {
    setProposal(next); setTitle(next.title); setContent(next.content);
    setSelected(next.selected_sources.map(source => source.id)); setConflict(null);
    setProposals(previous => [next, ...previous.filter(item => item.id !== next.id)]);
  };
  const openProposal = async (id: string) => {
    const requestId = ++opening.current;
    const [next, sourceList, jobList] = await Promise.all([api.proposal(id), api.sources(id), api.jobs(id)]);
    if (requestId !== opening.current) return;
    install(next); setSources(sourceList.items); setJobs(jobList.items); setJobId(jobList.items[0]?.id ?? ''); setPollError('');
  };
  const confirmDiscard = () => window.confirm('Discard unsaved changes and continue? Copy your text first if you want to keep it.');
  const guardEdits = () => !dirty || confirmDiscard();
  const activateTeam = (nextTeamId: string) => {
    if (nextTeamId !== teamId) { clearEditor(); setTeamId(nextTeamId); setError(''); setNotice(''); }
  };
  const changeTeam = (nextTeamId: string) => {
    if (canChangeTeam(teamId, nextTeamId, dirty, confirmDiscard)) activateTeam(nextTeamId);
  };
  const showConflict = async (proposalId: string, explanation: string) => {
    setError(`${explanation} Your edits and drafting instruction are still here. Compare the saved revision before continuing.`);
    try { setConflict(await api.proposal(proposalId)); }
    catch { setError(`${explanation} Your edits and instruction are still here, but the saved revision could not be loaded. Copy your text, then reopen the proposal.`); }
  };
  const save = async (nextContent = content) => {
    if (!proposal) return;
    try {
      const saved = await api.save(proposal.id, { expected_revision: proposal.revision, title, content: nextContent, selected_source_ids: selected });
      install(saved); setNotice(`Saved revision ${saved.revision}.`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        await showConflict(proposal.id, 'Another member saved a newer revision.');
      } else throw err;
    }
  };
  const requestDraft = async () => {
    if (!proposal) return;
    try {
      const next = await api.draft(proposal.id, { expected_revision: proposal.revision, section, instruction, source_ids: selected });
      setJobs(previous => [next, ...previous]); setJobId(next.id); setNotice('Draft queued. You can keep working while it runs.');
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) await showConflict(proposal.id, `Draft was not queued. ${error.message}`);
      else throw error;
    }
  };
  const copy = async (value: string) => { await navigator.clipboard.writeText(value); setNotice('Copied to clipboard.'); };

  const activeJobIds = jobs.filter(item => item.state === 'queued' || item.state === 'running').map(item => item.id).join(',');
  useEffect(() => {
    if (!activeJobIds) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const updated = await Promise.all(activeJobIds.split(',').map(id => api.job(id)));
        if (!active) return;
        setJobs(previous => previous.map(item => updated.find(next => next.id === item.id) ?? item)); setPollError('');
      } catch (err) { if (active) setPollError(message(err)); }
      if (active) timer = setTimeout(poll, 2000);
    };
    timer = setTimeout(poll, 1500);
    return () => { active = false; clearTimeout(timer); };
  }, [activeJobIds]);

  const submit = (event: FormEvent, action: () => Promise<void>) => { event.preventDefault(); void run(action); };

  if (checking) return <main className="auth-shell"><p role="status">Opening your workspace…</p></main>;
  if (!user) return <main className="auth-shell">
    <div className="auth-intro"><div className="brand-mark">trb</div><p className="brand-name">Tiger Research Buddy</p><h1>Good research starts<br />with shared evidence.</h1><p>Find sources, develop a proposal with your team, and review cited draft suggestions in one workspace.</p><div className="auth-note">Your research, from first source to saved proposal.</div></div>
    <section className="auth-panel" aria-labelledby="auth-title"><h2 id="auth-title">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2><p className="muted">{mode === 'login' ? 'Sign in to your research workspace.' : 'Use your name so teammates can find you.'}</p>
      {error && <div className="alert error" role="alert">{error}</div>}
      <form onSubmit={event => submit(event, async () => {
        const result = await api.authenticate(mode, { email, password, ...(mode === 'register' ? { name } : {}) });
        setUser(result.user); setPassword('');
      })}>
        {mode === 'register' && <label>Your name<input autoComplete="name" value={name} onChange={event => setName(event.target.value)} required maxLength={100} /></label>}
        <label>Email<input type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} required /></label>
        <label>Password<input type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength={mode === 'register' ? 12 : undefined} maxLength={1024} value={password} onChange={event => setPassword(event.target.value)} required />{mode === 'register' && <span className="muted">Use at least 12 characters.</span>}</label>
        <button className="primary wide" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}</button>
      </form>
      <button className="text-button" disabled={busy} onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}>{mode === 'login' ? 'New here? Create an account' : 'Already have an account? Sign in'}</button>
    </section>
  </main>;

  return <div className="workspace">
    <header className="topbar"><a className="brand" href="#main"><span className="brand-mark small">trb</span><span>Tiger Research Buddy<small>Research workspace</small></span></a><div className="account"><span>{user.name}<small>{user.email}</small></span><button disabled={busy} onClick={() => { if ((!dirty && !shortlistDirty) || confirmDiscard()) void run(async () => { await api.logout(); setShortlistDrafts({}); clearEditor(); setTeamId(''); setUser(null); setProposal(null); setTeams([]); setProposals([]); setInvitations([]); setSources([]); setJobs([]); setResults(null); setConflict(null); setTitle(''); setContent(''); setSelected([]); setSourceTitle(''); setSourceText(''); setSourceOrigin(''); setInstruction(''); setQuery(''); setInviteEmail(''); setNewTitle(''); setTeamName(''); setNotice(''); }); }}>Sign out</button></div></header>
    <div className="feedback" aria-live="polite">{busy && <span role="status">Working…</span>}{notice && <span className="success" role="status">{notice}</span>}{error && <div className="alert error" role="alert">{error}<button aria-label="Dismiss error" onClick={() => setError('')}>×</button></div>}</div>
    <div className="workspace-grid">
      <aside className="navigation" aria-label="Teams and proposals">
        <div className="section-heading"><h2>Your workspace</h2><button className="text-button" disabled={busy} onClick={() => void run(refreshLists)}>Refresh</button></div>
        <label>Team<select value={teamId} disabled={busy} onChange={event => changeTeam(event.target.value)}><option value="" disabled>Choose a team</option>{teams.map(team => <option key={team.id} value={team.id}>{team.name} ({team.role})</option>)}</select></label>
        {!teams.length && <p className="empty">Create a team to start a proposal, or accept an invitation.</p>}
        <details><summary>Create a team</summary><form onSubmit={event => { event.preventDefault(); if (guardEdits()) void run(async () => { const team = await api.createTeam(teamName); setTeamName(''); await refreshLists(); activateTeam(team.id); setNotice('Team created.'); }); }}><label>Team name<input value={teamName} onChange={event => setTeamName(event.target.value)} required maxLength={160} /></label><button disabled={busy}>Create team</button></form></details>
        {teams.find(team => team.id === teamId)?.role === 'owner' && <details><summary>Invite a teammate</summary><form onSubmit={event => submit(event, async () => { await api.invite(teamId, inviteEmail, inviteRole); setInviteEmail(''); setNotice('Invitation sent. Your teammate can accept it in their workspace.'); })}><p className="muted">Invite an existing account by email.</p><label>Teammate email<input type="email" value={inviteEmail} onChange={event => setInviteEmail(event.target.value)} required /></label><label>Access<select value={inviteRole} onChange={event => setInviteRole(event.target.value as 'editor' | 'viewer')}><option value="editor">Editor</option><option value="viewer">Viewer</option></select></label><button disabled={busy}>Send invitation</button></form></details>}
        {invitations.length > 0 && <section className="inbox"><h3>Invitations</h3>{invitations.map(invite => <div key={invite.id}><p>{invite.team_name}<small>{invite.role} access</small></p><button disabled={busy} onClick={() => { if (canChangeTeam(teamId, invite.team_id, dirty, confirmDiscard)) void run(async () => { const accepted = await api.accept(invite.id); await refreshLists(); activateTeam(accepted.team_id); setNotice('Invitation accepted.'); }); }}>Accept</button></div>)}</section>}
        <div className="nav-divider" />
        <h2>Proposals</h2><p className="muted">Saved work in your selected team.</p>
        <nav aria-label="Saved proposals">{proposals.filter(item => item.team_id === teamId).map(item => <button className={`proposal-link ${item.id === proposal?.id ? 'active' : ''}`} aria-current={item.id === proposal?.id ? 'page' : undefined} disabled={busy} key={item.id} onClick={() => { if (guardEdits()) void run(() => openProposal(item.id)); }}><span>{item.title}</span><small>Revision {item.revision}</small></button>)}</nav>
        {!proposals.some(item => item.team_id === teamId) && <p className="empty">No saved proposals in this team yet.</p>}
        <form className="new-proposal" onSubmit={event => { event.preventDefault(); if (guardEdits()) void run(async () => { const next = await api.createProposal(teamId, newTitle); await openProposal(next.id); setNewTitle(''); }); }}><label>New proposal title<input value={newTitle} onChange={event => setNewTitle(event.target.value)} required maxLength={240} /></label><button className="primary wide" disabled={busy || !teamId || teams.find(team => team.id === teamId)?.role === 'viewer'}>Create proposal</button></form>
      </aside>
      <main id="main" className="main-column">
        {proposal ? <section className="editor-panel" aria-labelledby="editor-heading"><div className="section-heading"><div><h1 id="editor-heading">Proposal editor</h1><p className="muted">{teams.find(team => team.id === proposal.team_id)?.name ?? 'Team proposal'} · {proposal.role} access</p></div><span className={`save-status ${dirty ? 'unsaved' : ''}`}>{dirty ? 'Unsaved changes' : `Saved · revision ${proposal.revision}`}</span></div>
          <fieldset disabled={busy || !editable} className="editor-fields"><label>Proposal title<input className="title-input" value={title} onChange={event => setTitle(event.target.value)} maxLength={240} required /></label><label>Proposal content<span className="label-note">Markdown supported</span><textarea className="proposal-content" value={content} onChange={event => setContent(event.target.value)} placeholder="Outline your question, approach, and expected contribution…" /></label></fieldset>
          <div className="editor-actions"><button className="primary" disabled={busy || !editable || !dirty || !title.trim() || !!conflict} onClick={() => void run(() => save())}>Save changes</button><button disabled={busy} onClick={() => void run(async () => { const blob = await api.exportMarkdown(proposal.id); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `proposal-${proposal.id}.md`; document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); setNotice('Markdown export downloaded from the saved proposal.'); })}>Export saved Markdown</button><span className="muted">{content.length.toLocaleString()} characters</span></div>
          {dirty && <p className="muted">Export uses the last saved revision. Save your edits first to include them.</p>}
          {!editable && <p className="muted">You have viewer access. Your team owner can invite you as an editor.</p>}
          {conflict && <section className="conflict" aria-labelledby="conflict-heading"><h2 id="conflict-heading">Review the newer revision</h2><p>Your edits remain in the editor. The server has revision {conflict.revision}.</p><details><summary>Compare saved text</summary><h3>{conflict.title}</h3><pre>{conflict.content || '(Empty proposal)'}</pre></details><div className="button-row"><button disabled={busy} onClick={() => void run(() => copy(`# ${title}\n\n${content}`))}>Copy my edits</button><button disabled={busy} onClick={() => { install(conflict); setNotice('Loaded the saved revision.'); }}>Discard mine and load saved</button><button disabled={busy} onClick={() => { setProposal(conflict); setConflict(null); setNotice('Your edits are kept. Reconcile them in the editor, then save against the latest revision.'); }}>Keep my edits for reconciliation</button></div></section>}
        </section> : <section className="workspace-empty"><span className="paper-symbol" aria-hidden="true">≡</span><h1>A place for your next research question.</h1><p>Create a team and proposal, then bring in evidence from discovery or your own source text.</p><p className="muted">Your changes are saved only when you choose Save changes.</p></section>}
        {proposal && <PursuitPanel proposal={proposal} />}
        {selectedTeam && <ShortlistPanel team={selectedTeam} proposal={proposal} attachedSourceIds={sources.map(source => source.id)} refreshVersion={shortlistVersion} workspaceBusy={busy} noteDrafts={shortlistDrafts[teamId] ?? {}} onNoteChange={(entryId, value, savedNote) => setShortlistDrafts(previous => editShortlistDraft(previous, teamId, entryId, value, savedNote))} onNoteSaved={(entryId, savedNote) => setShortlistDrafts(previous => acknowledgeShortlistDraft(previous, teamId, entryId, savedNote))} onRemove={entryId => setShortlistDrafts(previous => { const notes = { ...previous[teamId] }; delete notes[entryId]; return { ...previous, [teamId]: notes }; })} onAttach={sourceId => run(async () => { if (!proposal || !canAttachToProposal(teamId, proposal)) return; const source = await api.attach(proposal.id, sourceId); setSources(previous => [...previous.filter(item => item.id !== source.id), source]); setNotice('Saved source attached to the open proposal.'); })} />}
        <section className="discovery" aria-labelledby="discovery-heading"><div className="section-heading"><div><h2 id="discovery-heading">Discover evidence</h2><p className="muted">Search public papers, listed authors, and clearly marked researcher examples.</p></div><span className="tag">Public and sample corpus</span></div><form className="search-form" onSubmit={event => submit(event, async () => { setResults(await api.search(query)); })}><label className="grow">Research topic<input value={query} onChange={event => setQuery(event.target.value)} placeholder="Try retrieval, collaboration, or climate" required /></label><button className="primary" disabled={busy}>Search</button></form>
          {results?.degraded && <p className="alert warning">Search is running with limited evidence. Check the source and match reason before using a result.</p>}
          {results && !results.items.length && <p className="empty">No results for this query. Try a broader research topic.</p>}
          <div className="search-results">{results?.items.map(result => <article className="search-result" key={result.id}><div className="result-meta"><span className="tag">{sourceKindLabel(result.kind, result.evidence_kind)}</span><span className={`evidence ${result.evidence_kind === 'synthetic' ? 'synthetic' : ''}`}>{result.evidence_kind === 'synthetic' ? 'Synthetic sample' : 'Public evidence'}</span></div><h3>{result.title}</h3><p>{result.snippet}</p><p className="match-reason">{result.reason}</p><div className="result-actions"><Origin value={result.origin} /><div className="button-row"><button disabled={busy || !selectedTeam || selectedTeam.role === 'viewer'} onClick={() => void run(async () => { await api.addShortlist(teamId, result.source_id); setShortlistVersion(previous => previous + 1); setNotice('Saved to the team shortlist.'); })}>Shortlist</button><button disabled={busy || !canAttachToProposal(teamId, proposal) || sources.some(source => source.id === result.source_id)} onClick={() => void run(async () => { if (!proposal) return; const source = await api.attach(proposal.id, result.source_id); setSources(previous => [...previous.filter(item => item.id !== source.id), source]); setNotice('Source attached. Select it in Evidence to include it in a draft.'); })}>{sources.some(source => source.id === result.source_id) ? 'Attached' : 'Attach to proposal'}</button></div></div></article>)}</div>
        </section>
      </main>
      <aside className="evidence-column" aria-label="Proposal evidence and draft suggestions"><section><div className="section-heading"><h2>Evidence</h2><span className="count">{sources.length}</span></div><p className="muted">Attach sources, then select the evidence your draft should use.</p>
        {!proposal && <p className="empty">Open a proposal to attach sources.</p>}{proposal && !sources.length && <p className="empty">No sources attached yet. Attach a search result or add your own text.</p>}
        {sources.map(source => <article className="source" key={source.id}><label className="checkbox-label"><input type="checkbox" disabled={busy || !editable} checked={selected.includes(source.id)} onChange={event => setSelected(previous => event.target.checked ? [...previous, source.id] : previous.filter(id => id !== source.id))} /><span>{source.title}<small>{source.is_public ? 'Public source' : 'Proposal source'} · version {source.version}</small></span></label><details><summary>Inspect source text</summary><pre>{source.text}</pre><Origin value={source.origin} /></details></article>)}
        {proposal && editable && <details className="manual-source"><summary>Add source text</summary><form onSubmit={event => submit(event, async () => { const added = await api.addSource(proposal.id, { title: sourceTitle, text: sourceText, origin: sourceOrigin }); setSources(previous => [...previous.filter(item => item.id !== added.id), added]); setSourceTitle(''); setSourceText(''); setSourceOrigin(''); setNotice('Source attached to this proposal.'); })}><label>Source title<input value={sourceTitle} onChange={event => setSourceTitle(event.target.value)} required /></label><label>Origin or URL<input value={sourceOrigin} onChange={event => setSourceOrigin(event.target.value)} placeholder="Document name or source URL" required /></label><label>Source text<textarea value={sourceText} onChange={event => setSourceText(event.target.value)} required rows={6} /></label><button disabled={busy}>Attach source text</button></form></details>}
        {proposal && dirty && <p className="muted">Source selections are pending until you save.</p>}
      </section><section className="draft-section"><h2>Draft with evidence</h2><p className="muted">Request a suggestion from selected sources. Review it before adding it to your proposal.</p><form onSubmit={event => submit(event, requestDraft)}><label>Section<input maxLength={200} value={section} onChange={event => setSection(event.target.value)} required disabled={!proposal || !editable || busy} /></label><label>Drafting instruction<textarea rows={4} maxLength={8000} value={instruction} onChange={event => setInstruction(event.target.value)} placeholder="Explain the proposed approach and its supporting evidence." required disabled={!proposal || !editable || busy} /></label><button className="primary wide" disabled={busy || !proposal || !editable || dirty || !!conflict || !selected.length || jobs.some(item => item.state === 'queued' || item.state === 'running')}>Request draft</button></form>{dirty && <p className="muted">Save your proposal and source selections before requesting a draft.</p>}{!selected.length && proposal && <p className="muted">Select at least one source to request a cited draft.</p>}
      </section>
      {jobs.length > 0 && <section className="job-section"><h2>Draft suggestions</h2><label>Job history<select value={job?.id ?? ''} onChange={event => setJobId(event.target.value)}>{jobs.map(item => <option value={item.id} key={item.id}>{item.state} · revision {item.base_revision} · {new Date(item.created_at).toLocaleTimeString()}</option>)}</select></label>{pollError && <p className="alert error" role="alert">Status refresh failed: {pollError} Retrying…</p>}{job && <><div className="job-status" role="status"><span className={`status-dot ${job.state}`} />{job.state === 'failed' && job.error?.code === 'cancelled' ? 'Cancelled' : job.state}<span className="muted">Based on revision {job.base_revision}</span></div>{(job.state === 'queued' || job.state === 'running') && <button disabled={busy} onClick={() => void run(async () => { const next = await api.cancel(job.id); setJobs(previous => previous.map(item => item.id === next.id ? next : item)); })}>Cancel draft</button>}{job.error && <p className="alert error" role="alert">{job.error.message}</p>}{job.output && <><div className="suggestion-text">{job.output.text}</div>{job.output.insufficient_evidence && <p className="alert warning">The draft reports insufficient evidence. Check its claims against the sources.</p>}<div className="button-row"><button disabled={busy} onClick={() => void run(() => copy(job.output!.text))}>Copy suggestion</button><button className="primary" disabled={busy || !editable || !proposal || !!conflict || !canApplyDraft(job, proposal, dirty)} onClick={() => void run(async () => { if (proposal && canApplyDraft(job, proposal, dirty)) await save(appendSuggestion(content, job.output!.text)); })}>Append suggestion and save</button></div>{proposal && !canApplyDraft(job, proposal, dirty) && <p className="alert warning">This suggestion cannot be applied directly because its proposal revision or source versions differ, or there are unsaved edits. Copy it and reconcile the text in the editor.</p>}<h3 className="citations-heading">Supporting citations</h3>{!job.output.citations.length && <p className="muted">No citations were returned.</p>}{job.output.citations.map((citation, index) => <blockquote className="citation" key={`${citation.source_id}-${index}`}><p>“{citation.quote}”</p><footer><strong>{citation.title}</strong><small>Version {citation.version}</small><Origin value={citation.origin} /></footer></blockquote>)}</>}</>}</section>}
      </aside>
    </div>
  </div>;
}
