'use client';

import { useEffect, useState, type FormEvent } from 'react';
import Link from 'next/link';
import { ApiError, api, type CollaboratorCoverage, type CollaboratorMatch, type Team } from '@/lib/api';
import { safeOrigin } from '@/lib/editor';

export default function CollaboratorsPage() {
  const [loading, setLoading] = useState(true);
  const [signedIn, setSignedIn] = useState(false);
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useState('');
  const [idea, setIdea] = useState('');
  const [matches, setMatches] = useState<CollaboratorMatch[] | null>(null);
  const [coverage, setCoverage] = useState<CollaboratorCoverage | null>(null);
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let active = true;
    Promise.all([api.me(), api.teams()]).then(([, result]) => {
      if (!active) return;
      setSignedIn(true);
      setTeams(result.items);
      setTeamId(result.items[0]?.id ?? '');
    }).catch(err => {
      if (!active) return;
      if (!(err instanceof ApiError && err.status === 401)) {
        setError(err instanceof Error ? err.message : 'Could not open collaborator matching.');
      }
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const findMatches = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError('');
    setNotice('');
    setMatches(null);
    setCoverage(null);
    try {
      const result = await api.matchCollaborators(idea.trim());
      setMatches(result.items);
      setCoverage(result.coverage);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Collaborator search failed.');
    } finally {
      setBusy(false);
    }
  };

  const shortlist = async (match: CollaboratorMatch) => {
    const team = teams.find(item => item.id === teamId);
    if (!team || team.role === 'viewer' || match.candidate_status === 'synthetic_example') return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const rationale = `Match evidence: ${match.evidence_terms.join(', ')}. Keyword overlap only; profile currentness and availability are unknown.`;
      const saved = await api.addShortlist(team.id, match.source_id, rationale);
      setSavedIds(previous => [...previous, match.source_id]);
      setNotice(saved.note === rationale
        ? 'Profile saved with its source-term rationale in the team note. No invitation was sent.'
        : 'Profile is already on your team shortlist. No invitation was sent.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save this profile.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <main className="auth-shell"><p role="status">Opening collaborator matching…</p></main>;
  if (!signedIn) return <main className="auth-shell"><section className="auth-panel">
    <h1>Sign in to find collaborators</h1>
    <p className="muted">Collaborator matching uses your public researcher catalog.</p>
    {error && <p className="alert error" role="alert">{error}</p>}
    <Link href="/">Go to Research Circle sign in</Link>
  </section></main>;

  const selectedTeam = teams.find(team => team.id === teamId);
  return <div className="workspace">
    <header className="topbar">
      <Link className="brand" href="/"><span className="brand-mark small">rc</span><span>Research Circle<small>Evidence-backed collaborator discovery</small></span></Link>
      <Link href="/">Back to workspace</Link>
    </header>
    <main id="main" className="discovery" aria-labelledby="matching-heading">
      <div className="section-heading"><div>
        <h1 id="matching-heading">Find research collaborators</h1>
        <p className="muted">Describe the idea. Matches show the exact overlapping terms and source profile.</p>
      </div></div>
      <form className="search-form" onSubmit={findMatches}>
        <label className="grow">Research idea
          <textarea value={idea} onChange={event => setIdea(event.target.value)} required maxLength={1000} rows={3}
            placeholder="For example: AI, machine learning, or natural language processing" />
        </label>
        <button className="primary" disabled={busy || !idea.trim()}>{busy ? 'Finding matches…' : 'Find matches'}</button>
      </form>
      <p className="muted">Matching uses exact profile terms plus transparent AI, ML, NLP, and RAG abbreviation expansions. It is not semantic and does not estimate expertise, availability, or willingness to collaborate.</p>
      <div className="search-form">
        <label className="grow">Save profiles to team
          <select value={teamId} disabled={busy || !teams.length} onChange={event => setTeamId(event.target.value)}>
            {!teams.length && <option value="">Create a team in your workspace first</option>}
            {teams.map(team => <option key={team.id} value={team.id}>{team.name} ({team.role})</option>)}
          </select>
        </label>
      </div>
      {selectedTeam?.role === 'viewer' && <p className="muted">Viewer access cannot edit the team shortlist.</p>}
      {error && <p className="alert error" role="alert">{error}</p>}
      {notice && <p className="success" role="status">{notice}</p>}
      {coverage && <aside className="coverage-note" role="status">
        <strong>Catalog coverage:</strong> checked {coverage.eligible_profile_count} imported RIT directory profiles; {coverage.matching_profile_count} matched.
        {coverage.uncovered_terms.length > 0 && <p>No imported profile facts matched: {coverage.uncovered_terms.join(', ')}.</p>}
        <p>{coverage.note}</p>
      </aside>}
      {matches && !matches.length && <p className="empty" role="status">No imported RIT directory profile facts matched this idea. Check the catalog coverage above; a missing match means this small imported set has no matching evidence, not that no researcher works on the topic.</p>}
      {matches && <div className="search-results" aria-live="polite">
        {matches.map(match => {
          const href = safeOrigin(match.origin);
          const synthetic = match.candidate_status === 'synthetic_example';
          const snapshot = match.candidate_status === 'snapshot_profile';
          const saved = savedIds.includes(match.source_id);
          return <article className="search-result" key={match.source_id}>
            <div className="result-meta">
              <span className="tag">{synthetic ? 'Synthetic demo example' : snapshot ? 'RIT directory snapshot' : 'Official profile facts'}</span>
              <span className={`evidence ${synthetic ? 'synthetic' : ''}`}>{synthetic ? 'Not a real person' : snapshot ? 'Profile currentness unknown' : 'Availability unknown'}</span>
            </div>
            <h2>{match.title}</h2>
            <p>{match.snippet}</p>
            <p className="match-reason">{match.reason}</p>
            <p className="muted">Idea terms matched: {match.matched_terms.join(', ')} · Profile terms: {match.evidence_terms.join(', ')} · Lexical coverage: {Math.round(match.idea_coverage * 100)}%</p>
            <div className="result-actions">
              {href ? <a href={href} target="_blank" rel="noopener noreferrer">Inspect source</a> : <span className="muted">No external source URL</span>}
              {synthetic
                ? <span className="muted">Example only · cannot shortlist</span>
                : <button disabled={busy || !selectedTeam || selectedTeam.role === 'viewer' || saved}
                    onClick={() => void shortlist(match)}>{saved ? 'Saved to shortlist' : 'Save to team shortlist'}</button>}
            </div>
          </article>;
        })}
      </div>}
      <p className="muted">Saving a profile only adds it to your team shortlist. It does not contact or enroll the researcher.</p>
    </main>
  </div>;
}
