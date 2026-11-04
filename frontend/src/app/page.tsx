'use client';

import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import Link from 'next/link';
import {
  FileText,
  Users,
  Network,
  Search,
  Sparkles,
  ShieldCheck,
  Layers,
  ArrowRight,
  ExternalLink,
  Plus,
  Trash2,
  Download,
  Save,
  CheckCircle2,
  Clock,
  AlertCircle,
  HelpCircle,
  BookOpen,
  MessageSquare,
  Bold,
  Italic,
  List,
  ListOrdered,
  Quote,
  Code,
  Heading1,
  Heading2,
  Eye,
  Edit3,
  Columns,
  X,
  ChevronRight,
  ChevronLeft,
} from 'lucide-react';
import {
  api,
  ApiError,
  type ChatCitation,
  type CollaboratorCoverage,
  type CollaboratorMatch,
  type DraftJob,
  type Invitation,
  type Proposal,
  type SearchPage,
  type SourceSnapshot,
  type Team,
  type User,
} from '@/lib/api';
import { appendSuggestion, canApplyDraft, hasEdits, safeOrigin, renderMarkdownSimple } from '@/lib/editor';
import PursuitPanel from '@/components/PursuitPanel';
import ShortlistPanel from '@/components/ShortlistPanel';
import TeamMembersPanel from '@/components/TeamMembersPanel';
import GraphViewer from '@/components/GraphViewer';
import ChatInterface from '@/components/ChatInterface';
import CitationPanel from '@/components/CitationPanel';
import {
  canChangeTeam,
  canAttachToProposal,
  sourceKindLabel,
  editShortlistDraft,
  acknowledgeShortlistDraft,
  type ShortlistDrafts,
} from '@/lib/shortlist';

function OriginLink({ value }: { value: string }) {
  const href = safeOrigin(value);
  return href ? (
    <a href={href} target="_blank" rel="noopener noreferrer" className="origin-link">
      <span>View public origin</span>
      <ExternalLink className="w-3 h-3" />
    </a>
  ) : (
    <span className="muted">{value || 'No external link'}</span>
  );
}

function formatError(error: unknown) {
  return error instanceof Error ? error.message : 'The request failed. Please try again.';
}

type ViewTab = 'workspace' | 'collaborators' | 'graph' | 'search' | 'chat';

export default function App() {
  const [checking, setChecking] = useState(true);
  const [user, setUser] = useState<User | null>(null);

  // Auth form states
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  // App navigation & status
  const [currentView, setCurrentView] = useState<ViewTab>('workspace');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  // Team states
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useState('');
  const [teamName, setTeamName] = useState('');
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'editor' | 'viewer'>('editor');

  // Proposal states
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [newTitle, setNewTitle] = useState('');
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [sources, setSources] = useState<SourceSnapshot[]>([]);
  const [conflict, setConflict] = useState<Proposal | null>(null);

  // Right sidebar tab in Workspace
  const [workspaceRightTab, setWorkspaceRightTab] = useState<'evidence' | 'ai'>('evidence');
  const [workspaceLeftTab, setWorkspaceLeftTab] = useState<'proposals' | 'team' | 'shortlist'>('proposals');
  const [editorMode, setEditorMode] = useState<'edit' | 'split' | 'preview'>('edit');
  const [evidenceCollapsed, setEvidenceCollapsed] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const insertFormatting = (prefix: string, suffix: string = '') => {
    const el = textareaRef.current;
    if (!el) {
      setContent((prev) => `${prev}\n${prefix}${suffix}`);
      return;
    }
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const selectedText = content.substring(start, end) || 'text';
    const replacement = `${prefix}${selectedText}${suffix}`;
    const nextContent = content.substring(0, start) + replacement + content.substring(end);
    setContent(nextContent);
    setTimeout(() => {
      el.focus();
      el.setSelectionRange(start + prefix.length, start + prefix.length + selectedText.length);
    }, 10);
  };

  const insertTemplate = (templateType: 'nsf' | 'nih' | 'darpa') => {
    let templateText = '';
    if (templateType === 'nsf') {
      templateText = `# Project Description\n\n## 1. Overview and Objectives\n[State the overarching goals, hypotheses, and primary research questions of the proposed project.]\n\n## 2. Intellectual Merit\n[Detail the scientific significance, novelty, and technological innovation.]\n\n## 3. Proposed Research Methodology & Work Plan\n[Provide the detailed experimental design, algorithms, baseline metrics, and validation.]\n\n## 4. Broader Impacts\n[Describe the societal benefits, education/outreach, student training, and dissemination.]\n\n## 5. Timeline and Key Milestones\n- Year 1: Baseline development and dataset curation.\n- Year 2: Algorithmic prototyping and empirical validation.\n- Year 3: System deployment, user studies, and final evaluation.`;
    } else if (templateType === 'nih') {
      templateText = `# Specific Aims\n\n## Significance & Background\n[Briefly summarize the critical biomedical or algorithmic challenge.]\n\n## Specific Aim 1\n[Formulate Aim 1, testable hypothesis, and anticipated research milestone.]\n\n## Specific Aim 2\n[Formulate Aim 2, experimental protocol, and expected outcomes.]\n\n## Innovation & Potential Pitfalls\n[Highlight conceptual innovations, potential pitfalls, and alternative strategies.]`;
    } else if (templateType === 'darpa') {
      templateText = `# Technical Proposal & Approach\n\n## 1. Executive Summary & Problem Statement\n[Define the critical operational challenge and state-of-the-art limitations.]\n\n## 2. Proposed Technical Breakthrough\n[Describe the transformative technology, architecture, and expected performance gains.]\n\n## 3. Measurable Technical Milestones\n- Month 6: Proof-of-concept prototype demonstrating 2x efficiency.\n- Month 12: Laboratory validation and stress testing under adversarial conditions.\n- Month 18: Full system demonstration and transition plan.\n\n## 4. Risk Mitigation Matrix\n[Identify high-risk technical barriers and corresponding mitigation protocols.]`;
    }
    if (!content.trim()) {
      setContent(templateText);
    } else {
      setContent((prev) => `${prev.trimEnd()}\n\n${templateText}`);
    }
  };

  // Manual source state
  const [sourceTitle, setSourceTitle] = useState('');
  const [sourceText, setSourceText] = useState('');
  const [sourceOrigin, setSourceOrigin] = useState('');

  // Drafting states
  const [section, setSection] = useState('Research approach');
  const [instruction, setInstruction] = useState('');
  const [jobs, setJobs] = useState<DraftJob[]>([]);
  const [jobId, setJobId] = useState('');
  const [pollError, setPollError] = useState('');

  // Shortlist states
  const [shortlistVersion, setShortlistVersion] = useState(0);
  const [shortlistDrafts, setShortlistDrafts] = useState<ShortlistDrafts>({});

  // Discovery search states
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchPage | null>(null);

  // Collaborator matching states
  const [collaboratorIdea, setCollaboratorIdea] = useState('');
  const [collaboratorMatches, setCollaboratorMatches] = useState<CollaboratorMatch[] | null>(null);
  const [collaboratorCoverage, setCollaboratorCoverage] = useState<CollaboratorCoverage | null>(null);
  const [matchingBusy, setMatchingBusy] = useState(false);
  const [savedCollaboratorIds, setSavedCollaboratorIds] = useState<string[]>([]);
  const [chatCitations, setChatCitations] = useState<ChatCitation[]>([]);

  const opening = useRef(0);
  const selectedTeam = teams.find((team) => team.id === teamId);
  const dirty = !!proposal && hasEdits(proposal, title, content, selected);
  const shortlistDirty = Object.values(shortlistDrafts).some((notes) => Object.keys(notes).length > 0);
  const editable = proposal?.role !== 'viewer';
  const job = jobs.find((item) => item.id === jobId) ?? jobs[0];

  const clearEditor = useCallback(() => {
    ++opening.current;
    setProposal(null);
    setTitle('');
    setContent('');
    setSelected([]);
    setSources([]);
    setJobs([]);
    setJobId('');
    setConflict(null);
    setPollError('');
    setSourceTitle('');
    setSourceText('');
    setSourceOrigin('');
    setSection('Research approach');
    setInstruction('');
    setNewTitle('');
    setInviteEmail('');
  }, []);

  const refreshLists = useCallback(async () => {
    const [teamList, proposalList, inbox] = await Promise.all([
      api.teams(),
      api.proposals(),
      api.invitations(),
    ]);
    setTeams(teamList.items);
    setProposals(proposalList.items);
    setInvitations(inbox.items);
    setTeamId((previous) =>
      teamList.items.some((item) => item.id === previous)
        ? previous
        : teamList.items[0]?.id ?? ''
    );
  }, []);

  useEffect(() => {
    let active = true;
    api
      .me()
      .then((result) => {
        if (active) setUser(result.user);
      })
      .catch((err) => {
        if (active && !(err instanceof ApiError && err.status === 401)) {
          setError(formatError(err));
        }
      })
      .finally(() => {
        if (active) setChecking(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (user) {
      void refreshLists().catch((err) => setError(formatError(err)));
    }
  }, [user, refreshLists]);

  useEffect(() => {
    if (!dirty && !shortlistDirty) return;
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty, shortlistDirty]);

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await action();
    } catch (err) {
      setError(formatError(err));
    } finally {
      setBusy(false);
    }
  };

  const install = (next: Proposal) => {
    setProposal(next);
    setTitle(next.title);
    setContent(next.content);
    setSelected(next.selected_sources.map((source) => source.id));
    setConflict(null);
    setProposals((previous) => [next, ...previous.filter((item) => item.id !== next.id)]);
  };

  const openProposal = async (id: string) => {
    const requestId = ++opening.current;
    const [next, sourceList, jobList] = await Promise.all([
      api.proposal(id),
      api.sources(id),
      api.jobs(id),
    ]);
    if (requestId !== opening.current) return;
    install(next);
    setSources(sourceList.items);
    setJobs(jobList.items);
    setJobId(jobList.items[0]?.id ?? '');
    setPollError('');
    setCurrentView('workspace');
  };

  const confirmDiscard = () =>
    window.confirm('Discard unsaved changes and continue? Copy your text first if you want to keep it.');

  const guardEdits = () => !dirty || confirmDiscard();

  const activateTeam = (nextTeamId: string) => {
    if (nextTeamId !== teamId) {
      clearEditor();
      setTeamId(nextTeamId);
      setError('');
      setNotice('');
    }
  };

  const changeTeam = (nextTeamId: string) => {
    if (canChangeTeam(teamId, nextTeamId, dirty, confirmDiscard)) {
      activateTeam(nextTeamId);
    }
  };

  const save = async (nextContent = content) => {
    if (!proposal) return;
    try {
      const saved = await api.save(proposal.id, {
        expected_revision: proposal.revision,
        title,
        content: nextContent,
        selected_source_ids: selected,
      });
      install(saved);
      setNotice(`Saved revision ${saved.revision}.`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        try {
          const latest = await api.proposal(proposal.id);
          setConflict(latest);
          setError('Another member saved a newer revision. Review the differences below.');
        } catch {
          setError('Another member saved a newer revision. Please copy your edits and reload.');
        }
      } else {
        throw err;
      }
    }
  };

  const requestDraft = async () => {
    if (!proposal) return;
    try {
      const next = await api.draft(proposal.id, {
        expected_revision: proposal.revision,
        section,
        instruction,
        source_ids: selected,
      });
      setJobs((previous) => [next, ...previous]);
      setJobId(next.id);
      setWorkspaceRightTab('ai');
      setNotice('Draft queued with Meta Llama model. You can keep editing while it runs.');
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setError(`Draft was not queued: ${error.message}`);
      } else {
        throw error;
      }
    }
  };

  // Poll active draft jobs
  const activeJobIds = jobs
    .filter((item) => item.state === 'queued' || item.state === 'running')
    .map((item) => item.id)
    .join(',');

  useEffect(() => {
    if (!activeJobIds) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const updated = await Promise.all(activeJobIds.split(',').map((id) => api.job(id)));
        if (!active) return;
        setJobs((previous) =>
          previous.map((item) => updated.find((next) => next.id === item.id) ?? item)
        );
        setPollError('');
      } catch (err) {
        if (active) setPollError(formatError(err));
      }
      if (active) timer = setTimeout(poll, 2000);
    };
    timer = setTimeout(poll, 1500);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [activeJobIds]);

  const copyToClipboard = async (value: string) => {
    await navigator.clipboard.writeText(value);
    setNotice('Copied to clipboard.');
  };

  const handleSearchSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    await run(async () => {
      setResults(await api.search(query.trim()));
    });
  };

  const handleCollaboratorMatch = async (idea: string) => {
    if (!idea.trim()) return;
    setMatchingBusy(true);
    setError('');
    setNotice('');
    try {
      const result = await api.matchCollaborators(idea.trim());
      setCollaboratorMatches(result.items);
      setCollaboratorCoverage(result.coverage);
    } catch (err) {
      setError(formatError(err));
    } finally {
      setMatchingBusy(false);
    }
  };

  const shortlistCollaborator = async (match: CollaboratorMatch) => {
    if (!selectedTeam || selectedTeam.role === 'viewer') return;
    await run(async () => {
      const rationale = `Match evidence: ${match.evidence_terms.join(', ')}. Overlapping terms: ${match.matched_terms.join(', ')}.`;
      await api.addShortlist(selectedTeam.id, match.source_id, rationale);
      setSavedCollaboratorIds((prev) => [...prev, match.source_id]);
      setShortlistVersion((prev) => prev + 1);
      setNotice(`Saved ${match.title} to team shortlist.`);
    });
  };

  // -------------------------------------------------------------
  // VIEW: LANDING & AUTH PAGE (When not signed in)
  // -------------------------------------------------------------
  if (checking) {
    return (
      <main className="auth-shell">
        <div className="spinner" />
        <p role="status">Initializing Research Workspace…</p>
      </main>
    );
  }

  if (!user) {
    return (
      <div className="landing-page">
        {/* Navigation Bar */}
        <header className="landing-topbar">
          <div className="brand">
            <span className="brand-mark small">trb</span>
            <div>
              <strong>Tiger Research Buddy</strong>
              <small>RIT Academic Research Platform</small>
            </div>
          </div>
          <div className="landing-topbar-actions">
            <a href="#features" className="button text-button">Features</a>
            <a href="#auth" className="button primary">Sign In / Register</a>
          </div>
        </header>

        {/* Hero Section */}
        <section className="landing-hero">
          <div className="landing-hero-content">
            <div className="hero-pill">
              <Sparkles className="w-4 h-4 text-[#225bb2]" />
              <span>Evidence-Grounded AI Research Co-Authoring</span>
            </div>
            <h1>
              From First Research Idea<br />to Funded, Cited Proposal.
            </h1>
            <p className="hero-description">
              Tiger Research Buddy unites RIT faculty discovery, institutional knowledge graphs,
              and hallucination-free Meta Llama AI drafting—validating every claim word-for-word against verified sources.
            </p>
            <div className="hero-actions">
              <a href="#auth" className="button primary large">
                <span>Start Researching</span>
                <ArrowRight className="w-4 h-4" />
              </a>
              <a href="#features" className="button large">
                Explore Core Capabilities
              </a>
            </div>
          </div>

          {/* Auth Card */}
          <div id="auth" className="landing-auth-card">
            <div className="auth-tabs">
              <button
                type="button"
                className={`auth-tab ${authMode === 'login' ? 'active' : ''}`}
                onClick={() => {
                  setAuthMode('login');
                  setError('');
                }}
              >
                Sign In
              </button>
              <button
                type="button"
                className={`auth-tab ${authMode === 'register' ? 'active' : ''}`}
                onClick={() => {
                  setAuthMode('register');
                  setError('');
                }}
              >
                Create Account
              </button>
            </div>

            {error && (
              <div className="alert error" role="alert">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form
              onSubmit={(e) => {
                e.preventDefault();
                void run(async () => {
                  const res = await api.authenticate(authMode, {
                    email,
                    password,
                    ...(authMode === 'register' ? { name } : {}),
                  });
                  setUser(res.user);
                  setPassword('');
                });
              }}
            >
              {authMode === 'register' && (
                <label>
                  Full name
                  <input
                    type="text"
                    placeholder="e.g. Dr. Alex River"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    maxLength={100}
                  />
                </label>
              )}
              <label>
                Academic email
                <input
                  type="email"
                  placeholder="name@rit.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  minLength={authMode === 'register' ? 12 : undefined}
                  maxLength={1024}
                  required
                />
                {authMode === 'register' && (
                  <span className="muted">Minimum 12 characters.</span>
                )}
              </label>
              <button className="primary wide" disabled={busy}>
                {busy ? 'Verifying credentials…' : authMode === 'login' ? 'Sign In to Workspace' : 'Create Free Account'}
              </button>
            </form>
          </div>
        </section>

        {/* Feature Grid Section */}
        <section id="features" className="landing-features">
          <div className="features-header">
            <h2>Engineered for Transparent Research Collaboration</h2>
            <p className="muted">
              Built on verified public university records, revision-locked proposals, and strict quotation bounds.
            </p>
          </div>

          <div className="feature-cards-grid">
            <article className="feature-card">
              <div className="feature-icon-wrapper faculty">
                <Users className="w-6 h-6 text-[#225bb2]" />
              </div>
              <h3>Faculty Collaborator Matching</h3>
              <p>
                Describe your research hypothesis or grant scope. The platform computes term coverage across RIT faculty profiles and publications, showing exact matched evidence without fabricating unearned connections.
              </p>
            </article>

            <article className="feature-card">
              <div className="feature-icon-wrapper graph">
                <Network className="w-6 h-6 text-[#14766d]" />
              </div>
              <h3>Public Knowledge Graph</h3>
              <p>
                Explore interdisciplinary relationships visually. Inspect actual co-authorship networks, university departments, and research clusters with direct provenance links.
              </p>
            </article>

            <article className="feature-card">
              <div className="feature-icon-wrapper ai">
                <Sparkles className="w-6 h-6 text-[#d97706]" />
              </div>
              <h3>Evidence-Grounded AI Drafting</h3>
              <p>
                Powered by Meta Llama API. Every generated claim is validated word-for-word against your selected sources. If a quote is not found verbatim in the evidence, the draft is rejected before it can pollute your proposal.
              </p>
            </article>

            <article className="feature-card">
              <div className="feature-icon-wrapper workspace">
                <FileText className="w-6 h-6 text-[#4f46e5]" />
              </div>
              <h3>Collaborative Workspace & Grants</h3>
              <p>
                Co-author with your research team. Enforce role boundaries (Owner, Editor, Viewer), resolve simultaneous edit conflicts safely, and manage submissions across the full grant pursuit lifecycle.
              </p>
            </article>
          </div>
        </section>

        <footer className="landing-footer">
          <p>© 2026 Tiger Research Buddy · ResearchCircle · RIT Research Platform</p>
        </footer>
      </div>
    );
  }

  // -------------------------------------------------------------
  // VIEW: AUTHENTICATED APPLICATION
  // -------------------------------------------------------------
  return (
    <div className="workspace-app">
      {/* Top Application Bar */}
      <header className="app-topbar">
        <div className="brand" onClick={() => setCurrentView('workspace')} style={{ cursor: 'pointer' }}>
          <span className="brand-mark small">trb</span>
          <div className="brand-titles">
            <strong>Tiger Research Buddy</strong>
            <small>Research Workspace</small>
          </div>
        </div>

        {/* Primary Navigation Tabs */}
        <nav className="main-nav-tabs" aria-label="Main Navigation">
          <button
            type="button"
            className={`nav-tab ${currentView === 'workspace' ? 'active' : ''}`}
            onClick={() => setCurrentView('workspace')}
          >
            <FileText className="w-4 h-4" />
            <span>Workspace & Editor</span>
            {proposal && <span className="tab-badge active-proposal">{proposal.title.slice(0, 18)}…</span>}
          </button>
          <button
            type="button"
            className={`nav-tab ${currentView === 'collaborators' ? 'active' : ''}`}
            onClick={() => setCurrentView('collaborators')}
          >
            <Users className="w-4 h-4" />
            <span>Find Collaborators</span>
          </button>
          <button
            type="button"
            className={`nav-tab ${currentView === 'graph' ? 'active' : ''}`}
            onClick={() => setCurrentView('graph')}
          >
            <Network className="w-4 h-4" />
            <span>Knowledge Graph</span>
          </button>
          <button
            type="button"
            className={`nav-tab ${currentView === 'search' ? 'active' : ''}`}
            onClick={() => setCurrentView('search')}
          >
            <Search className="w-4 h-4" />
            <span>Literature Search</span>
          </button>
          <button
            type="button"
            className={`nav-tab ${currentView === 'chat' ? 'active' : ''}`}
            onClick={() => setCurrentView('chat')}
          >
            <MessageSquare className="w-4 h-4" />
            <span>Research Chat</span>
            {chatCitations.length > 0 && (
              <span className="tab-badge">{chatCitations.length} citations</span>
            )}
          </button>
        </nav>

        {/* Right Header Section: Active Team Switcher & User Menu */}
        <div className="topbar-user-area">
          <div className="team-picker">
            <span className="team-picker-label">Team:</span>
            <select
              value={teamId}
              disabled={busy}
              onChange={(e) => changeTeam(e.target.value)}
              className="team-select"
            >
              <option value="" disabled>Choose a team</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.role})
                </option>
              ))}
            </select>
          </div>

          <div className="user-profile">
            <div className="user-info">
              <span className="user-name">{user.name}</span>
              <small className="user-email">{user.email}</small>
            </div>
            <button
              type="button"
              className="logout-button"
              disabled={busy}
              onClick={() => {
                if ((!dirty && !shortlistDirty) || confirmDiscard()) {
                  void run(async () => {
                    await api.logout();
                    setShortlistDrafts({});
                    clearEditor();
                    setTeamId('');
                    setUser(null);
                  });
                }
              }}
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* Global Notice / Error Alerts */}
      <div className="feedback-banner" aria-live="polite">
        {busy && <span className="status-pill working">Processing…</span>}
        {notice && (
          <span className="status-pill success">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {notice}
          </span>
        )}
        {error && (
          <div className="alert error banner-alert" role="alert">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
            <button type="button" aria-label="Dismiss error" onClick={() => setError('')}>×</button>
          </div>
        )}
      </div>

      {/* ------------------------------------------------------------- */}
      {/* VIEW 1: PROPOSALS & WORKSPACE                                  */}
      {/* ------------------------------------------------------------- */}
      {currentView === 'workspace' && (
        <div className="workspace-tri-grid">
          {/* Left Column: Teams, Members, & Proposals */}
          <aside className="workspace-sidebar" aria-label="Teams and proposals">
            <div className="workspace-sidebar-tabs">
              <button
                type="button"
                className={`sidebar-tab-btn ${workspaceLeftTab === 'proposals' ? 'active' : ''}`}
                onClick={() => setWorkspaceLeftTab('proposals')}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Proposals ({proposals.filter((item) => item.team_id === teamId).length})</span>
              </button>
              <button
                type="button"
                className={`sidebar-tab-btn ${workspaceLeftTab === 'team' ? 'active' : ''}`}
                onClick={() => setWorkspaceLeftTab('team')}
              >
                <Users className="w-3.5 h-3.5" />
                <span>Team & Access</span>
              </button>
              <button
                type="button"
                className={`sidebar-tab-btn ${workspaceLeftTab === 'shortlist' ? 'active' : ''}`}
                onClick={() => setWorkspaceLeftTab('shortlist')}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Shortlist</span>
              </button>
            </div>

            {/* TAB 1: PROPOSALS */}
            {workspaceLeftTab === 'proposals' && (
              <div className="sidebar-section">
                <div className="sidebar-header">
                  <h3>Team Proposals</h3>
                  <span className="count-pill">
                    {proposals.filter((item) => item.team_id === teamId).length}
                  </span>
                </div>

                <div className="proposals-list" role="list">
                  {proposals
                    .filter((item) => item.team_id === teamId)
                    .map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        className={`proposal-item ${item.id === proposal?.id ? 'active' : ''}`}
                        disabled={busy}
                        onClick={() => {
                          if (guardEdits()) void run(() => openProposal(item.id));
                        }}
                      >
                        <FileText className="w-4 h-4 shrink-0" />
                        <div className="proposal-item-text">
                          <span className="proposal-title">{item.title}</span>
                          <small className="muted">Revision {item.revision}</small>
                        </div>
                      </button>
                    ))}

                  {!proposals.some((item) => item.team_id === teamId) && (
                    <p className="empty">No proposals in this team yet.</p>
                  )}
                </div>

                <form
                  className="new-proposal-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (guardEdits()) {
                      void run(async () => {
                        const next = await api.createProposal(teamId, newTitle);
                        await openProposal(next.id);
                        setNewTitle('');
                      });
                    }
                  }}
                >
                  <input
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="New proposal title…"
                    required
                    maxLength={240}
                    disabled={!teamId || selectedTeam?.role === 'viewer'}
                  />
                  <button
                    type="submit"
                    className="primary wide"
                    disabled={busy || !teamId || selectedTeam?.role === 'viewer'}
                  >
                    <Plus className="w-4 h-4" />
                    <span>Create Proposal</span>
                  </button>
                </form>
              </div>
            )}

            {/* TAB 2: TEAM & ACCESS */}
            {workspaceLeftTab === 'team' && (
              <div className="sidebar-section">
                <div className="sidebar-header">
                  <h3>Teams & Access</h3>
                  <button type="button" className="text-button" onClick={() => void run(refreshLists)}>
                    Refresh
                  </button>
                </div>

                {selectedTeam && user && (
                  <TeamMembersPanel
                    key={selectedTeam.id}
                    team={selectedTeam}
                    currentUserId={user.id}
                    onChanged={refreshLists}
                    beforeSelfChange={() => (!dirty && !shortlistDirty) || confirmDiscard()}
                  />
                )}

                {selectedTeam?.role === 'owner' && (
                  <details className="accordion-card">
                    <summary>Invite a teammate</summary>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        void run(async () => {
                          await api.invite(teamId, inviteEmail, inviteRole);
                          setInviteEmail('');
                          setNotice('Invitation sent.');
                        });
                      }}
                    >
                      <label>
                        Email address
                        <input
                          type="email"
                          value={inviteEmail}
                          onChange={(e) => setInviteEmail(e.target.value)}
                          placeholder="colleague@rit.edu"
                          required
                        />
                      </label>
                      <label>
                        Role access
                        <select
                          value={inviteRole}
                          onChange={(e) => setInviteRole(e.target.value as 'editor' | 'viewer')}
                        >
                          <option value="editor">Editor (Can edit & draft)</option>
                          <option value="viewer">Viewer (Read-only)</option>
                        </select>
                      </label>
                      <button disabled={busy} className="button small">Send Invite</button>
                    </form>
                  </details>
                )}

                <details className="accordion-card">
                  <summary>Create another team</summary>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      if (guardEdits()) {
                        void run(async () => {
                          const t = await api.createTeam(teamName);
                          setTeamName('');
                          await refreshLists();
                          activateTeam(t.id);
                          setNotice('Team created.');
                        });
                      }
                    }}
                  >
                    <input
                      value={teamName}
                      onChange={(e) => setTeamName(e.target.value)}
                      placeholder="Team name"
                      required
                      maxLength={160}
                    />
                    <button disabled={busy} className="button small">Create</button>
                  </form>
                </details>

                {invitations.length > 0 && (
                  <div className="invitations-box">
                    <h4>Pending Invitations ({invitations.length})</h4>
                    {invitations.map((invite) => (
                      <div key={invite.id} className="invite-row">
                        <span>{invite.team_name} ({invite.role})</span>
                        <button
                          type="button"
                          className="button small"
                          onClick={() => {
                            if (canChangeTeam(teamId, invite.team_id, dirty, confirmDiscard)) {
                              void run(async () => {
                                const accepted = await api.accept(invite.id);
                                await refreshLists();
                                activateTeam(accepted.team_id);
                                setNotice('Invitation accepted.');
                              });
                            }
                          }}
                        >
                          Accept
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: SHORTLIST */}
            {workspaceLeftTab === 'shortlist' && selectedTeam && (
              <div className="sidebar-section">
                <ShortlistPanel
                  team={selectedTeam}
                  proposal={proposal}
                  attachedSourceIds={sources.map((s) => s.id)}
                  refreshVersion={shortlistVersion}
                  workspaceBusy={busy}
                  noteDrafts={shortlistDrafts[teamId] ?? {}}
                  onNoteChange={(entryId, val, savedNote) =>
                    setShortlistDrafts((prev) => editShortlistDraft(prev, teamId, entryId, val, savedNote))
                  }
                  onNoteSaved={(entryId, savedNote) =>
                    setShortlistDrafts((prev) => acknowledgeShortlistDraft(prev, teamId, entryId, savedNote))
                  }
                  onRemove={(entryId) =>
                    setShortlistDrafts((prev) => {
                      const notes = { ...prev[teamId] };
                      delete notes[entryId];
                      return { ...prev, [teamId]: notes };
                    })
                  }
                  onAttach={(sourceId) =>
                    run(async () => {
                      if (!proposal || !canAttachToProposal(teamId, proposal)) return;
                      const source = await api.attach(proposal.id, sourceId);
                      setSources((prev) => [...prev.filter((i) => i.id !== source.id), source]);
                      setNotice('Shortlisted source attached to proposal.');
                    })
                  }
                />
              </div>
            )}
          </aside>

          {/* Center Column: Focused Proposal Editor */}
          <main id="main" className="workspace-editor-canvas">
            {proposal ? (
              <div className="editor-card">
                <div className="editor-top-controls">
                  <div>
                    <span className="badge team-badge">
                      {selectedTeam?.name ?? 'Team proposal'} · {proposal.role} access
                    </span>
                    <span className={`save-status-pill ${dirty ? 'unsaved' : 'saved'}`}>
                      {dirty ? '● Unsaved changes' : `✓ Saved · Revision ${proposal.revision}`}
                    </span>
                  </div>

                  <div className="editor-btn-group">
                    <button
                      type="button"
                      className="primary"
                      disabled={busy || !editable || !dirty || !title.trim() || !!conflict}
                      onClick={() => void run(() => save())}
                    >
                      <Save className="w-4 h-4" />
                      <span>Save changes</span>
                    </button>
                    <button
                      type="button"
                      className="button"
                      disabled={busy}
                      onClick={() =>
                        void run(async () => {
                          const blob = await api.exportMarkdown(proposal.id);
                          const url = URL.createObjectURL(blob);
                          const link = document.createElement('a');
                          link.href = url;
                          link.download = `proposal-${proposal.id}.md`;
                          document.body.appendChild(link);
                          link.click();
                          link.remove();
                          setTimeout(() => URL.revokeObjectURL(url), 1000);
                          setNotice('Exported Markdown downloaded.');
                        })
                      }
                    >
                      <Download className="w-4 h-4" />
                      <span>Export Markdown</span>
                    </button>
                  </div>
                </div>

                {/* Revision Conflict Banner */}
                {conflict && (
                  <section className="conflict-banner" role="alert">
                    <h4>Revision Conflict Detected</h4>
                    <p>Another collaborator saved revision {conflict.revision}. Your changes are preserved in the editor.</p>
                    <details>
                      <summary>Compare with server version</summary>
                      <h5>Server Revision ({conflict.title}):</h5>
                      <pre>{conflict.content || '(Empty content)'}</pre>
                    </details>
                    <div className="conflict-actions">
                      <button type="button" onClick={() => void copyToClipboard(`# ${title}\n\n${content}`)}>
                        Copy my edits
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          install(conflict);
                          setNotice('Loaded the server revision.');
                        }}
                      >
                        Discard mine and load server
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setProposal(conflict);
                          setConflict(null);
                          setNotice('Reconcile changes and save against latest revision.');
                        }}
                      >
                        Keep my edits for reconciliation
                      </button>
                    </div>
                  </section>
                )}

                {/* Title & Body Inputs */}
                <div className="editor-inputs">
                  <label className="title-field">
                    <span>Proposal title</span>
                    <input
                      className="title-input-large"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      maxLength={240}
                      required
                      disabled={busy || !editable}
                      placeholder="Title of research proposal…"
                    />
                  </label>

                  {/* Document Metrics & Mode Bar */}
                  <div className="editor-metrics-bar">
                    <div className="metrics-group">
                      <span className="metric-item">
                        <strong>{content.trim() ? content.trim().split(/\s+/).length : 0}</strong> words
                      </span>
                      <span className="metric-divider">·</span>
                      <span className="metric-item">
                        <strong>{((content.trim() ? content.trim().split(/\s+/).length : 0) / 500).toFixed(1)}</strong> pages
                      </span>
                      <span className="metric-divider">·</span>
                      <span className="metric-item">
                        <strong>{content.length.toLocaleString()}</strong> characters
                      </span>
                      <span className="metric-divider">·</span>
                      <span className="metric-item">
                        <strong>{Math.max(1, Math.ceil((content.trim() ? content.trim().split(/\s+/).length : 0) / 200))}</strong> min read
                      </span>
                    </div>

                    <div className="editor-mode-switcher">
                      <button
                        type="button"
                        className={`mode-btn ${editorMode === 'edit' ? 'active' : ''}`}
                        onClick={() => setEditorMode('edit')}
                        title="Editor only"
                      >
                        <Edit3 className="w-3 h-3" />
                        <span>Edit</span>
                      </button>
                      <button
                        type="button"
                        className={`mode-btn ${editorMode === 'split' ? 'active' : ''}`}
                        onClick={() => setEditorMode('split')}
                        title="Split view (Editor + Live Preview)"
                      >
                        <Columns className="w-3 h-3" />
                        <span>Split</span>
                      </button>
                      <button
                        type="button"
                        className={`mode-btn ${editorMode === 'preview' ? 'active' : ''}`}
                        onClick={() => setEditorMode('preview')}
                        title="Formatted manuscript preview"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Preview</span>
                      </button>
                    </div>
                  </div>

                  {/* Formatting Toolbar & Template Inserter */}
                  {editorMode !== 'preview' && (
                    <div className="editor-toolbar">
                      <div className="toolbar-btn-group">
                        <button type="button" className="toolbar-btn" onClick={() => insertFormatting('**', '**')} title="Bold">
                          <Bold className="w-3.5 h-3.5" />
                        </button>
                        <button type="button" className="toolbar-btn" onClick={() => insertFormatting('*', '*')} title="Italic">
                          <Italic className="w-3.5 h-3.5" />
                        </button>
                        <button type="button" className="toolbar-btn" onClick={() => insertFormatting('## ')} title="Heading 2">
                          <Heading1 className="w-3.5 h-3.5" />
                        </button>
                        <button type="button" className="toolbar-btn" onClick={() => insertFormatting('### ')} title="Heading 3">
                          <Heading2 className="w-3.5 h-3.5" />
                        </button>
                        <button type="button" className="toolbar-btn" onClick={() => insertFormatting('- ')} title="Bullet list">
                          <List className="w-3.5 h-3.5" />
                        </button>
                        <button type="button" className="toolbar-btn" onClick={() => insertFormatting('1. ')} title="Numbered list">
                          <ListOrdered className="w-3.5 h-3.5" />
                        </button>
                        <button type="button" className="toolbar-btn" onClick={() => insertFormatting('> ')} title="Blockquote">
                          <Quote className="w-3.5 h-3.5" />
                        </button>
                        <button type="button" className="toolbar-btn" onClick={() => insertFormatting('```\n', '\n```')} title="Code or equation block">
                          <Code className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <div className="toolbar-templates-dropdown">
                        <select
                          onChange={(e) => {
                            if (e.target.value) {
                              insertTemplate(e.target.value as any);
                              e.target.value = '';
                            }
                          }}
                          defaultValue=""
                          className="template-select"
                        >
                          <option value="" disabled>+ Insert Grant Template…</option>
                          <option value="nsf">NSF Project Description (Intellectual Merit & Broader Impacts)</option>
                          <option value="nih">NIH Specific Aims (Significance & Innovation)</option>
                          <option value="darpa">DoD / DARPA Technical Approach & Milestones</option>
                        </select>
                      </div>
                    </div>
                  )}

                  {/* Dynamic Canvas: Edit / Split / Preview */}
                  {editorMode === 'edit' && (
                    <textarea
                      ref={textareaRef}
                      className="content-textarea"
                      value={content}
                      onChange={(e) => setContent(e.target.value)}
                      disabled={busy || !editable}
                      placeholder="Draft your proposal introduction, methodology, and aims here. You can request cited suggestions from the Evidence sidebar on the right…"
                      rows={22}
                    />
                  )}

                  {editorMode === 'split' && (
                    <div className="editor-split-container">
                      <textarea
                        ref={textareaRef}
                        className="content-textarea"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        disabled={busy || !editable}
                        placeholder="Draft markdown text here…"
                        rows={22}
                      />
                      <div
                        className="editor-preview-pane"
                        dangerouslySetInnerHTML={{ __html: renderMarkdownSimple(content) }}
                      />
                    </div>
                  )}

                  {editorMode === 'preview' && (
                    <div
                      className="editor-preview-standalone"
                      dangerouslySetInnerHTML={{ __html: renderMarkdownSimple(content) }}
                    />
                  )}
                </div>

                {/* Grant Pursuit Tracking */}
                <div className="editor-pursuit-section">
                  <PursuitPanel proposal={proposal} />
                </div>
              </div>
            ) : (
              <div className="no-proposal-empty-state">
                <div className="empty-icon-circle">
                  <FileText className="w-8 h-8 text-[#225bb2]" />
                </div>
                <h2>Select or Create a Research Proposal</h2>
                <p className="muted">
                  Choose a proposal from the left sidebar to start editing, or create a new proposal.
                  You can also explore collaborator recommendations or search the literature.
                </p>
                <div className="empty-quick-actions">
                  <button type="button" className="button" onClick={() => setCurrentView('collaborators')}>
                    <Users className="w-4 h-4" />
                    <span>Find Collaborators</span>
                  </button>
                  <button type="button" className="button" onClick={() => setCurrentView('graph')}>
                    <Network className="w-4 h-4" />
                    <span>Explore Knowledge Graph</span>
                  </button>
                </div>
              </div>
            )}
          </main>

          {/* Right Column: Evidence & AI Assistant */}
          <aside className="workspace-evidence-sidebar" aria-label="Evidence and AI Assistant">
            <div className="sidebar-tab-switcher">
              <button
                type="button"
                className={`sidebar-tab ${workspaceRightTab === 'evidence' ? 'active' : ''}`}
                onClick={() => setWorkspaceRightTab('evidence')}
              >
                <span>Attached Evidence ({sources.length})</span>
              </button>
              <button
                type="button"
                className={`sidebar-tab ${workspaceRightTab === 'ai' ? 'active' : ''}`}
                onClick={() => setWorkspaceRightTab('ai')}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Meta Llama Assistant</span>
              </button>
            </div>

            {/* TAB: ATTACHED EVIDENCE */}
            {workspaceRightTab === 'evidence' && (
              <div className="sidebar-tab-content">
                <div className="tab-instructions">
                  <p className="muted">
                    Sources selected below will ground AI draft suggestions. Every claim is strictly validated against these documents.
                  </p>
                </div>

                {!proposal && <p className="empty">Open a proposal to view attached sources.</p>}
                {proposal && sources.length === 0 && (
                  <p className="empty">No evidence attached yet. Search literature or add custom text below.</p>
                )}

                <div className="sources-checklist">
                  {sources.map((s) => (
                    <article key={s.id} className="evidence-item-card">
                      <label className="evidence-checkbox-label">
                        <input
                          type="checkbox"
                          disabled={busy || !editable}
                          checked={selected.includes(s.id)}
                          onChange={(e) =>
                            setSelected((prev) =>
                              e.target.checked ? [...prev, s.id] : prev.filter((id) => id !== s.id)
                            )
                          }
                        />
                        <div className="evidence-meta">
                          <strong>{s.title}</strong>
                          <small>
                            {s.is_public ? 'Public literature' : 'Proposal source'} · Version {s.version}
                          </small>
                        </div>
                      </label>
                      <details className="source-preview-details">
                        <summary>View text excerpt</summary>
                        <pre>{s.text}</pre>
                        <OriginLink value={s.origin} />
                      </details>
                    </article>
                  ))}
                </div>

                {proposal && editable && (
                  <details className="accordion-card mt-4">
                    <summary>Add custom source text</summary>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        void run(async () => {
                          const added = await api.addSource(proposal.id, {
                            title: sourceTitle,
                            text: sourceText,
                            origin: sourceOrigin,
                          });
                          setSources((prev) => [...prev.filter((i) => i.id !== added.id), added]);
                          setSourceTitle('');
                          setSourceText('');
                          setSourceOrigin('');
                          setNotice('Source attached.');
                        });
                      }}
                    >
                      <input
                        value={sourceTitle}
                        onChange={(e) => setSourceTitle(e.target.value)}
                        placeholder="Source title or label"
                        required
                      />
                      <input
                        value={sourceOrigin}
                        onChange={(e) => setSourceOrigin(e.target.value)}
                        placeholder="DOI or document URL"
                        required
                      />
                      <textarea
                        value={sourceText}
                        onChange={(e) => setSourceText(e.target.value)}
                        placeholder="Paste document text or excerpt…"
                        rows={5}
                        required
                      />
                      <button className="button small">Attach text</button>
                    </form>
                  </details>
                )}
              </div>
            )}

            {/* TAB: META LLAMA AI DRAFTING */}
            {workspaceRightTab === 'ai' && (
              <div className="sidebar-tab-content">
                <div className="ai-assistant-header">
                  <div className="ai-model-tag">
                    <Sparkles className="w-3.5 h-3.5 text-[#225bb2]" />
                    <span>Meta Llama 3.3 (70B) Grounded</span>
                  </div>
                  <p className="muted">
                    Request a cited section. Quotes are checked word-for-word against selected sources.
                  </p>
                </div>

                <form
                  className="draft-prompt-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void requestDraft();
                  }}
                >
                  <label>
                    Target section
                    <input
                      value={section}
                      onChange={(e) => setSection(e.target.value)}
                      placeholder="e.g. Methodology, Objectives"
                      required
                      disabled={!proposal || !editable || busy}
                    />
                  </label>
                  <div className="co-pilot-prompts-row">
                    <span style={{ fontSize: '11px', fontWeight: 600, color: '#64748b' }}>Quick Prompts:</span>
                    <button
                      type="button"
                      className="co-pilot-chip"
                      onClick={() => {
                        setSection('Technical Approach & Methodology');
                        setInstruction('Draft a rigorous methodology section synthesizing the key experimental techniques, architectures, and baseline evaluations from the selected evidence sources.');
                      }}
                    >
                      <Sparkles className="w-3 h-3 text-blue-500" />
                      <span>Methodology from Evidence</span>
                    </button>
                    <button
                      type="button"
                      className="co-pilot-chip"
                      onClick={() => {
                        setSection('Intellectual Merit');
                        setInstruction('Draft the Intellectual Merit section highlighting the novelty, technological gap, and primary scientific breakthroughs addressed in this proposal.');
                      }}
                    >
                      <Sparkles className="w-3 h-3 text-amber-500" />
                      <span>Intellectual Merit</span>
                    </button>
                    <button
                      type="button"
                      className="co-pilot-chip"
                      onClick={() => {
                        setSection('Broader Impacts');
                        setInstruction('Draft the Broader Impacts section detailing the educational outreach, student training, and societal benefits of the proposed research.');
                      }}
                    >
                      <Sparkles className="w-3 h-3 text-emerald-500" />
                      <span>Broader Impacts</span>
                    </button>
                  </div>

                  <label>
                    Drafting prompt
                    <textarea
                      value={instruction}
                      onChange={(e) => setInstruction(e.target.value)}
                      placeholder="Describe what to draft based on the selected evidence…"
                      rows={4}
                      maxLength={8000}
                      required
                      disabled={!proposal || !editable || busy}
                    />
                  </label>
                  <button
                    className="primary wide"
                    disabled={
                      busy ||
                      !proposal ||
                      !editable ||
                      dirty ||
                      !!conflict ||
                      selected.length === 0 ||
                      jobs.some((item) => item.state === 'queued' || item.state === 'running')
                    }
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>Generate Cited Draft</span>
                  </button>
                  {dirty && <p className="muted small">Save proposal changes before generating a draft.</p>}
                  {selected.length === 0 && proposal && (
                    <p className="muted small">Select at least one source in the Evidence tab.</p>
                  )}
                </form>

                {/* Suggestions Output */}
                {jobs.length > 0 && (
                  <div className="suggestions-history">
                    <div className="suggestions-header">
                      <h4>Draft History ({jobs.length})</h4>
                      <select
                        value={job?.id ?? ''}
                        onChange={(e) => setJobId(e.target.value)}
                        className="job-history-select"
                      >
                        {jobs.map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.state} · Rev {item.base_revision} · {new Date(item.created_at).toLocaleTimeString()}
                          </option>
                        ))}
                      </select>
                    </div>

                    {job && (
                      <div className="job-result-card">
                        <div className="job-state-row">
                          <span className={`status-dot ${job.state}`} />
                          <strong>
                            {job.state === 'failed' && job.error?.code === 'cancelled'
                              ? 'Cancelled'
                              : job.state.toUpperCase()}
                          </strong>
                          <small className="muted">Based on revision {job.base_revision}</small>
                        </div>

                        {(job.state === 'queued' || job.state === 'running') && (
                          <button
                            type="button"
                            className="button small"
                            onClick={() =>
                              void run(async () => {
                                const next = await api.cancel(job.id);
                                setJobs((prev) => prev.map((j) => (j.id === next.id ? next : j)));
                              })
                            }
                          >
                            Cancel Draft
                          </button>
                        )}

                        {job.error && (
                          <p className="alert error" role="alert">{job.error.message}</p>
                        )}

                        {job.output && (
                          <div className="suggestion-body">
                            <div className="suggestion-text">{job.output.text}</div>
                            {job.output.insufficient_evidence && (
                              <p className="alert warning">
                                Model reported insufficient evidence in selected sources.
                              </p>
                            )}

                            <div className="suggestion-actions">
                              <button
                                type="button"
                                className="button small"
                                onClick={() => void copyToClipboard(job.output!.text)}
                              >
                                Copy text
                              </button>
                              <button
                                type="button"
                                className="primary small"
                                disabled={busy || !editable || !proposal || !!conflict || !canApplyDraft(job, proposal, dirty)}
                                onClick={() =>
                                  void run(async () => {
                                    if (proposal && canApplyDraft(job, proposal, dirty)) {
                                      await save(appendSuggestion(content, job.output!.text));
                                    }
                                  })
                                }
                              >
                                Append to proposal & Save
                              </button>
                            </div>

                            {/* Verified Verbatim Quotes */}
                            <div className="citations-list">
                              <h5>Verified Verbatim Citations ({job.output.citations.length})</h5>
                              {job.output.citations.length === 0 && (
                                <p className="muted small">No direct quotes provided.</p>
                              )}
                              {job.output.citations.map((c, idx) => (
                                <blockquote key={`${c.source_id}-${idx}`} className="citation-quote">
                                  <p>“{c.quote}”</p>
                                  <footer>
                                    <strong>{c.title}</strong>
                                    <OriginLink value={c.origin} />
                                  </footer>
                                </blockquote>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </aside>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* VIEW 2: FIND COLLABORATORS                                     */}
      {/* ------------------------------------------------------------- */}
      {currentView === 'collaborators' && (
        <main className="collaborators-view-shell" aria-labelledby="collab-heading">
          <div className="view-intro-hero">
            <h1 id="collab-heading">Faculty Collaborator Discovery</h1>
            <p className="muted">
              Enter your research hypothesis, grant proposal aims, or target keywords.
              The system calculates transparent overlap against verified RIT faculty publications and profiles.
            </p>
          </div>

          <div className="collaborator-query-card">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void handleCollaboratorMatch(collaboratorIdea);
              }}
            >
              <textarea
                value={collaboratorIdea}
                onChange={(e) => setCollaboratorIdea(e.target.value)}
                placeholder="Describe your research concept, for example: 'Wireless sensor networks and battery-powered logging for environmental monitoring'…"
                rows={3}
                required
                maxLength={1000}
              />
              <div className="query-card-bottom">
                <div className="quick-examples">
                  <span className="muted small">Try an example:</span>
                  <button
                    type="button"
                    className="chip-btn"
                    onClick={() => {
                      const text = 'sensor networks for agricultural monitoring and battery telemetry';
                      setCollaboratorIdea(text);
                      void handleCollaboratorMatch(text);
                    }}
                  >
                    Environmental Sensors
                  </button>
                  <button
                    type="button"
                    className="chip-btn"
                    onClick={() => {
                      const text = 'deep learning, computer vision and medical image analysis';
                      setCollaboratorIdea(text);
                      void handleCollaboratorMatch(text);
                    }}
                  >
                    Computer Vision / AI
                  </button>
                </div>
                <button className="primary" disabled={matchingBusy || !collaboratorIdea.trim()}>
                  <Search className="w-4 h-4" />
                  <span>{matchingBusy ? 'Searching…' : 'Find Collaborators'}</span>
                </button>
              </div>
            </form>
          </div>

          {/* Coverage Summary */}
          {collaboratorCoverage && (
            <div className="coverage-card">
              <div className="coverage-stat">
                <strong>{collaboratorMatches?.length ?? 0}</strong>
                <span>Matching Candidates</span>
              </div>
              <div className="coverage-stat">
                <strong>{collaboratorCoverage.eligible_profile_count}</strong>
                <span>Eligible Faculty Profiles</span>
              </div>
              <div className="coverage-details">
                <p className="muted">{collaboratorCoverage.note}</p>
                {collaboratorCoverage.uncovered_terms.length > 0 && (
                  <p className="muted small">
                    Unmatched idea terms: <em>{collaboratorCoverage.uncovered_terms.join(', ')}</em>
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Matches List */}
          <div className="collaborator-results-grid">
            {collaboratorMatches?.map((match) => (
              <article key={match.source_id} className="collaborator-card">
                <div className="card-top">
                  <span className={`tag ${match.candidate_status}`}>
                    {match.candidate_status.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className="coverage-badge">
                    {Math.round(match.idea_coverage * 100)}% idea coverage
                  </span>
                </div>

                <h3>{match.title}</h3>
                <p className="snippet">{match.snippet}</p>

                <div className="overlap-tags">
                  <span className="tag-label">Matched terms:</span>
                  {match.matched_terms.map((term) => (
                    <span key={term} className="term-chip">{term}</span>
                  ))}
                </div>

                <p className="reason-note">{match.reason}</p>

                <div className="card-actions">
                  <OriginLink value={match.origin} />
                  <button
                    type="button"
                    className="button primary small"
                    disabled={
                      busy ||
                      !selectedTeam ||
                      selectedTeam.role === 'viewer' ||
                      savedCollaboratorIds.includes(match.source_id)
                    }
                    onClick={() => void shortlistCollaborator(match)}
                  >
                    {savedCollaboratorIds.includes(match.source_id)
                      ? '✓ Saved to Team Shortlist'
                      : `Shortlist to ${selectedTeam?.name ?? 'Team'}`}
                  </button>
                </div>
              </article>
            ))}

            {collaboratorMatches && collaboratorMatches.length === 0 && (
              <div className="empty-results-box">
                <Users className="w-8 h-8 text-[#536779]" />
                <h3>No matching collaborators found</h3>
                <p className="muted">Try broader terminology or different keywords from the institutional directory.</p>
              </div>
            )}
          </div>
        </main>
      )}

      {/* ------------------------------------------------------------- */}
      {/* VIEW 3: KNOWLEDGE GRAPH                                        */}
      {/* ------------------------------------------------------------- */}
      {currentView === 'graph' && (
        <main className="graph-full-view">
          <GraphViewer
            onSearchTopic={(topic) => {
              setQuery(topic);
              setCurrentView('search');
              void run(async () => {
                setResults(await api.search(topic));
              });
            }}
            onAttachSource={(sourceId) => {
              if (proposal && canAttachToProposal(teamId, proposal)) {
                void run(async () => {
                  const s = await api.attach(proposal.id, sourceId);
                  setSources((prev) => [...prev.filter((i) => i.id !== s.id), s]);
                  setNotice('Source attached to proposal.');
                });
              }
            }}
            attachedSourceIds={sources.map((s) => s.id)}
            proposalOpen={!!proposal && editable}
          />
        </main>
      )}

      {/* ------------------------------------------------------------- */}
      {/* VIEW 4: LITERATURE & EVIDENCE SEARCH                           */}
      {/* ------------------------------------------------------------- */}
      {currentView === 'search' && (
        <main className="search-view-shell" aria-labelledby="search-heading">
          <div className="view-intro-hero">
            <h1 id="search-heading">Literature & Evidence Search</h1>
            <p className="muted">
              Search peer-reviewed papers, listed publication authors, and researcher facts across the public research corpus.
            </p>
          </div>

          <div className="search-bar-card">
            <form onSubmit={handleSearchSubmit} className="search-input-form">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search research topics, keywords, authors, or DOIs…"
                required
              />
              <button className="primary" disabled={busy || !query.trim()}>
                <Search className="w-4 h-4" />
                <span>Search</span>
              </button>
            </form>
          </div>

          {results?.degraded && (
            <p className="alert warning">
              Search is operating in BM25 keyword mode. Review evidence sources before citing.
            </p>
          )}

          <div className="search-results-list">
            {results?.items.map((item) => (
              <article key={item.id} className="search-result-card">
                <div className="result-card-top">
                  <span className="tag">
                    {sourceKindLabel(item.kind, item.evidence_kind, item.identity_status)}
                  </span>
                  <span className={`evidence ${item.evidence_kind === 'synthetic' ? 'synthetic' : ''}`}>
                    {item.evidence_kind === 'synthetic' ? 'Synthetic sample' : 'Public literature'}
                  </span>
                </div>

                <h3>{item.title}</h3>
                <p className="snippet">{item.snippet}</p>
                <p className="reason-note">{item.reason}</p>

                <div className="result-card-bottom">
                  <OriginLink value={item.origin} />
                  <div className="button-row">
                    <button
                      type="button"
                      className="button small"
                      disabled={busy || !selectedTeam || selectedTeam.role === 'viewer'}
                      onClick={() =>
                        void run(async () => {
                          await api.addShortlist(teamId, item.source_id);
                          setShortlistVersion((prev) => prev + 1);
                          setNotice('Added to team shortlist.');
                        })
                      }
                    >
                      Shortlist
                    </button>
                    <button
                      type="button"
                      className="button primary small"
                      disabled={
                        busy ||
                        !canAttachToProposal(teamId, proposal) ||
                        sources.some((s) => s.id === item.source_id)
                      }
                      onClick={() =>
                        void run(async () => {
                          if (!proposal) return;
                          const added = await api.attach(proposal.id, item.source_id);
                          setSources((prev) => [...prev.filter((s) => s.id !== added.id), added]);
                          setNotice('Attached to open proposal.');
                        })
                      }
                    >
                      {sources.some((s) => s.id === item.source_id) ? '✓ Attached' : 'Attach to Proposal'}
                    </button>
                  </div>
                </div>
              </article>
            ))}

            {results && results.items.length === 0 && (
              <div className="empty-results-box">
                <Search className="w-8 h-8 text-[#536779]" />
                <h3>No results found</h3>
                <p className="muted">Try broader terminology or different keywords.</p>
              </div>
            )}
          </div>
        </main>
      )}

      {/* ------------------------------------------------------------- */}
      {/* VIEW 5: GROUNDED RESEARCH CHAT                                 */}
      {/* ------------------------------------------------------------- */}
      {currentView === 'chat' && (
        <main className="chat-view-shell" aria-labelledby="chat-heading">
          <div className="view-intro-hero">
            <h1 id="chat-heading">Research Assistant & Multi-Turn Q&A</h1>
            <p className="muted">
              Converse with an AI research assistant grounded strictly on verified peer-reviewed publications and RIT faculty facts.
              Every factual assertion references inspectable verbatim quotations.
            </p>
          </div>

          <div className={`chat-container-grid ${evidenceCollapsed ? 'evidence-collapsed' : ''}`}>
            <div className="chat-main-column">
              <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '6px 12px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                <button
                  type="button"
                  className="button small"
                  onClick={() => setEvidenceCollapsed(!evidenceCollapsed)}
                  title={evidenceCollapsed ? 'Show evidence side panel' : 'Hide evidence side panel'}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '11px', padding: '3px 8px' }}
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>
                    {evidenceCollapsed
                      ? `Show Evidence Panel ${chatCitations.length > 0 ? `(${chatCitations.length})` : ''}`
                      : 'Hide Evidence Panel'}
                  </span>
                </button>
              </div>

              <ChatInterface
                proposalId={proposal?.id}
                proposalTitle={proposal?.title}
                onCitationsChange={(c) => setChatCitations(c)}
              />
            </div>

            {!evidenceCollapsed && (
              <aside className="chat-citations-column" aria-label="Active Grounded Citations">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', paddingBottom: '6px', borderBottom: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: '#475569' }}>
                    Active Citations ({chatCitations.length})
                  </span>
                  <button
                    type="button"
                    className="icon-button"
                    onClick={() => setEvidenceCollapsed(true)}
                    title="Collapse Evidence Panel"
                    style={{ padding: '2px 4px', height: '24px', width: '24px' }}
                  >
                    <X className="w-3.5 h-3.5 text-slate-500" />
                  </button>
                </div>
                <CitationPanel citations={chatCitations} />
              </aside>
            )}
          </div>
        </main>
      )}
    </div>
  );
}
