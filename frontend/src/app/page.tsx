'use client';

import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import Link from 'next/link';
import {
  FileText,
  Users,
  Search,
  Sparkles,
  ShieldCheck,
  Layers,
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
  PanelRight,
  CircleHelp,
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
  ArrowRight,
  Network,
} from 'lucide-react';
import {
  api,
  ApiError,
  type ChatCitation,
  type CollaboratorCoverage,
  type CollaboratorMatch,
  type DraftJob,
  type Invitation,
  type ModelInfo,
  type Proposal,
  type SearchPage,
  type SourceSnapshot,
  type Team,
  type TeamMember,
  type User,
} from '@/lib/api';
import { appendSuggestion, canApplyDraft, hasEdits, safeOrigin, renderMarkdownSimple } from '@/lib/editor';
import AppSidebar, { type AppView } from '@/components/AppSidebar';
import ContextPanel, { type ContextTab } from '@/components/ContextPanel';
import PursuitPanel from '@/components/PursuitPanel';
import ShortlistPanel from '@/components/ShortlistPanel';
import TeamMembersPanel from '@/components/TeamMembersPanel';
import WorkspaceTopBar from '@/components/WorkspaceTopBar';
import PublicLanding from '@/components/PublicLanding';
import GraphViewer from '@/components/GraphViewer';
import ChatInterface from '@/components/ChatInterface';
import CitationPanel from '@/components/CitationPanel';
import CollaborationHub from '@/components/CollaborationHub';
import PdfViewerModal from '@/components/PdfViewerModal';
import {
  canChangeTeam,
  canAttachToProposal,
  sourceKindLabel,
  editShortlistDraft,
  acknowledgeShortlistDraft,
  type ShortlistDrafts,
} from '@/lib/shortlist';

function looksLikePaperSource(opts: { title?: string; origin?: string }): boolean {
  const title = (opts.title || '').toLowerCase();
  const origin = (opts.origin || '').toLowerCase();
  if (title.startsWith('listed author:') || title.startsWith('synthetic researcher')) return false;
  if (origin.startsWith('synthetic ')) return false;
  if (!origin.startsWith('http://') && !origin.startsWith('https://')) return false;
  return true;
}

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

function DraftText({
  text,
  citations,
  jobId,
}: {
  text: string;
  citations: NonNullable<DraftJob['output']>['citations'];
  jobId: string;
}) {
  const parts = text.split(/(\[[0-9a-f]{8}-[0-9a-f-]{27}\])/gi);
  return (
    <div className="draft-text-content">
      {parts.map((part, index) => {
        const sourceId = part.startsWith('[') ? part.slice(1, -1) : '';
        const citationIndex = citations.findIndex(citation => citation.source_id === sourceId);
        if (citationIndex < 0) return <span key={index}>{part}</span>;
        return (
          <a
            key={index}
            className="citation-chip"
            href={`#draft-citation-${jobId}-${citationIndex}`}
            aria-label={`Go to citation ${citationIndex + 1}: ${citations[citationIndex].title}`}
          >
            [{citationIndex + 1}]
          </a>
        );
      })}
    </div>
  );
}

function formatError(error: unknown) {
  return error instanceof Error ? error.message : 'The request failed. Please try again.';
}

export default function App() {
  const [checking, setChecking] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);

  // Auth form states
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  // App navigation & status
  const [currentView, setCurrentView] = useState<AppView>('workspace');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [contextOpen, setContextOpen] = useState(true);

  // Team states
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useState('');
  const [teamName, setTeamName] = useState('');
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'editor' | 'viewer'>('editor');

  // Proposal states
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [newTitle, setNewTitle] = useState('');
  const [dashboardProposalTitle, setDashboardProposalTitle] = useState('');
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [sources, setSources] = useState<SourceSnapshot[]>([]);
  const [conflict, setConflict] = useState<Proposal | null>(null);
  const [activePdf, setActivePdf] = useState<{ id: string; title: string } | null>(null);
  const [collaboratorViewMode, setCollaboratorViewMode] = useState<'synthesizer' | 'lexical'>('synthesizer');
  const [editorMode, setEditorMode] = useState<'edit' | 'split' | 'preview'>('edit');
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
    if (templateText) {
      setContent((prev) => (prev.trim() ? `${prev}\n\n${templateText}` : templateText));
    }
  };

  // Right sidebar tab in Workspace
  const [workspaceRightTab, setWorkspaceRightTab] = useState<ContextTab>('ai');
  const contextTriggerRef = useRef<HTMLButtonElement>(null);

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
  const [evidenceCollapsed, setEvidenceCollapsed] = useState(false);
  const [hasUnseenCitations, setHasUnseenCitations] = useState(false);
  const prevCitationsKey = useRef<string>('');

  useEffect(() => {
    const key = chatCitations.map((c) => `${c.source_id}:${c.quote}`).join('|');
    if (key && key !== prevCitationsKey.current) {
      if (evidenceCollapsed) setHasUnseenCitations(true);
    }
    prevCitationsKey.current = key;
  }, [chatCitations, evidenceCollapsed]);

  useEffect(() => {
    if (!evidenceCollapsed) setHasUnseenCitations(false);
  }, [evidenceCollapsed]);

  const opening = useRef(0);
  const selectedTeam = teams.find((team) => team.id === teamId);
  const dirty = !!proposal && hasEdits(proposal, title, content, selected);
  const shortlistDirty = Object.values(shortlistDrafts).some((notes) => Object.keys(notes).length > 0);
  const editable = proposal?.role !== 'viewer';
  const canEditTeam = selectedTeam?.role !== 'viewer';
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
    if (window.matchMedia('(max-width: 760px)').matches) setContextOpen(false);
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
    if (!user) {
      setModelInfo(null);
      return;
    }
    let active = true;
    api.modelInfo()
      .then((result) => {
        if (active) setModelInfo(result);
      })
      .catch((err) => {
        if (active) setError(formatError(err));
      });
    return () => {
      active = false;
    };
  }, [user]);

  useEffect(() => {
    if (!selectedTeam) {
      setTeamMembers([]);
      return;
    }
    let active = true;
    api.teamDetails(selectedTeam.id)
      .then(details => {
        if (active) setTeamMembers(details.members);
      })
      .catch(err => {
        if (active) setError(formatError(err));
      });
    return () => {
      active = false;
    };
  }, [selectedTeam?.id]);

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

  const submitAuth = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void run(async () => {
      const res = await api.authenticate(authMode, {
        email,
        password,
        ...(authMode === 'register' ? { name } : {}),
      });
      setUser(res.user);
      setPassword('');
    });
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

  const guardEdits = () => (!dirty && !shortlistDirty) || confirmDiscard();

  const navigateView = (view: AppView) => {
    if (view === currentView || guardEdits()) {
      setCurrentView(view);
      setSidebarOpen(false);
    }
  };

  const createProposal = async (proposalTitle: string, initialContent: string = '') => {
    if (!teamId || !guardEdits()) return;
    await run(async () => {
      const created = await api.createProposal(teamId, proposalTitle, initialContent);
      await openProposal(created.id);
    });
  };

  const deleteProposal = async (target: Proposal) => {
    await run(async () => {
      await api.deleteProposal(target.id);
      setProposals((previous) => previous.filter((item) => item.id !== target.id));
      if (proposal?.id === target.id) {
        clearEditor();
      }
      setNotice(`Deleted “${target.title}”.`);
    });
  };

  const createProposalWithTemplate = async (proposalTitle: string, templateType: 'nsf' | 'nih' | 'darpa') => {
    let templateText = '';
    if (templateType === 'nsf') {
      templateText = `# Project Description\n\n## 1. Overview and Objectives\n[State the overarching goals, hypotheses, and primary research questions of the proposed project.]\n\n## 2. Intellectual Merit\n[Detail the scientific significance, novelty, and technological innovation.]\n\n## 3. Proposed Research Methodology & Work Plan\n[Provide the detailed experimental design, algorithms, baseline metrics, and validation.]\n\n## 4. Broader Impacts\n[Describe the societal benefits, education/outreach, student training, and dissemination.]\n\n## 5. Timeline and Key Milestones\n- Year 1: Baseline development and dataset curation.\n- Year 2: Algorithmic prototyping and empirical validation.\n- Year 3: System deployment, user studies, and final evaluation.`;
    } else if (templateType === 'nih') {
      templateText = `# Specific Aims\n\n## Significance & Background\n[Briefly summarize the critical biomedical or algorithmic challenge.]\n\n## Specific Aim 1\n[Formulate Aim 1, testable hypothesis, and anticipated research milestone.]\n\n## Specific Aim 2\n[Formulate Aim 2, experimental protocol, and expected outcomes.]\n\n## Innovation & Potential Pitfalls\n[Highlight conceptual innovations, potential pitfalls, and alternative strategies.]`;
    } else if (templateType === 'darpa') {
      templateText = `# Technical Proposal & Approach\n\n## 1. Executive Summary & Problem Statement\n[Define the critical operational challenge and state-of-the-art limitations.]\n\n## 2. Proposed Technical Breakthrough\n[Describe the transformative technology, architecture, and expected performance gains.]\n\n## 3. Measurable Technical Milestones\n- Month 6: Proof-of-concept prototype demonstrating 2x efficiency.\n- Month 12: Laboratory validation and stress testing under adversarial conditions.\n- Month 18: Full system demonstration and transition plan.\n\n## 4. Risk Mitigation Matrix\n[Identify high-risk technical barriers and corresponding mitigation protocols.]`;
    }
    await createProposal(proposalTitle, templateText);
  };

  const activateTeam = (nextTeamId: string) => {
    if (nextTeamId !== teamId) {
      clearEditor();
      setTeamId(nextTeamId);
      setError('');
      setNotice('');
    }
  };

  const changeTeam = (nextTeamId: string) => {
    if (canChangeTeam(teamId, nextTeamId, dirty || shortlistDirty, confirmDiscard)) {
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
      setNotice('Draft queued. Review the suggestion and its sources before adding it to your proposal.');
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

  const handleAttachSource = async (sourceId: string) => {
    if (!proposal) return;
    if (selected.includes(sourceId)) return;
    const nextSelected = [...selected, sourceId];
    setSelected(nextSelected);
    try {
      const saved = await api.save(proposal.id, {
        expected_revision: proposal.revision,
        title,
        content,
        selected_source_ids: nextSelected,
      });
      install(saved);
      setNotice(`Attached source to proposal (revision ${saved.revision}).`);
    } catch (err) {
      setError(formatError(err));
    }
  };

  const handleShortlistCandidate = async (sourceId: string, candTitle: string, rationale: string) => {
    if (!selectedTeam || selectedTeam.role === 'viewer') return;
    await run(async () => {
      await api.addShortlist(selectedTeam.id, sourceId, rationale);
      setSavedCollaboratorIds((prev) => [...prev, sourceId]);
      setShortlistVersion((prev) => prev + 1);
      setNotice(`Added ${candTitle} to team shortlist.`);
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
      <PublicLanding
        authMode={authMode}
        email={email}
        password={password}
        name={name}
        busy={busy}
        error={error}
        onModeChange={(mode) => {
          setAuthMode(mode);
          setError('');
        }}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onNameChange={setName}
        onSubmit={submitAuth}
      />
    );
  }

  // -------------------------------------------------------------
  // VIEW: AUTHENTICATED APPLICATION
  // -------------------------------------------------------------
  const inviteForm = selectedTeam?.role === 'owner' ? (
    <form
      onSubmit={event => {
        event.preventDefault();
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
          onChange={event => setInviteEmail(event.target.value)}
          placeholder="colleague@rit.edu"
          required
        />
      </label>
      <label>
        Role
        <select
          value={inviteRole}
          onChange={event => setInviteRole(event.target.value as 'editor' | 'viewer')}
        >
          <option value="editor">Editor</option>
          <option value="viewer">Viewer (read only)</option>
        </select>
      </label>
      <button className="primary" disabled={busy}>Send invitation</button>
    </form>
  ) : (
    <p className="muted">Only a team owner can invite members.</p>
  );

  const teamSettingsContent = (
    <div className="team-settings-sections">
      {selectedTeam && user && (
        <section>
          <h3>Members and access</h3>
          <TeamMembersPanel
            key={selectedTeam.id}
            team={selectedTeam}
            currentUserId={user.id}
            onChanged={async () => {
              await refreshLists();
              const details = await api.teamDetails(selectedTeam.id);
              setTeamMembers(details.members);
            }}
            beforeSelfChange={() => (!dirty && !shortlistDirty) || confirmDiscard()}
          />
        </section>
      )}
      {selectedTeam?.role === 'owner' && (
        <section>
          <h3>Invite a teammate</h3>
          {inviteForm}
        </section>
      )}
      <section>
        <h3>Create another team</h3>
        <form
          onSubmit={event => {
            event.preventDefault();
            if (guardEdits()) {
              void run(async () => {
                const nextTeam = await api.createTeam(teamName);
                setTeamName('');
                await refreshLists();
                activateTeam(nextTeam.id);
                setNotice('Team created.');
              });
            }
          }}
        >
          <label>
            New team name
            <input value={teamName} onChange={event => setTeamName(event.target.value)} required maxLength={160} />
          </label>
          <button type="submit" disabled={busy}>Create team</button>
        </form>
      </section>
      {invitations.length > 0 && (
        <section>
          <h3>Pending invitations</h3>
          {invitations.map(invite => (
            <div className="invite-row" key={invite.id}>
              <span>{invite.team_name} ({invite.role})</span>
              <button
                type="button"
                disabled={busy}
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
        </section>
      )}
    </div>
  );

  const shortlistContent = selectedTeam ? (
    <details className="sidebar-shortlist-details">
      <summary>Saved Sources</summary>
      <ShortlistPanel
        team={selectedTeam}
        proposal={proposal}
        attachedSourceIds={sources.map(source => source.id)}
        refreshVersion={shortlistVersion}
        workspaceBusy={busy}
        noteDrafts={shortlistDrafts[teamId] ?? {}}
        onNoteChange={(entryId, value, savedNote) =>
          setShortlistDrafts(previous => editShortlistDraft(previous, teamId, entryId, value, savedNote))
        }
        onNoteSaved={(entryId, savedNote) =>
          setShortlistDrafts(previous => acknowledgeShortlistDraft(previous, teamId, entryId, savedNote))
        }
        onRemove={entryId =>
          setShortlistDrafts(previous => {
            const notes = { ...previous[teamId] };
            delete notes[entryId];
            return { ...previous, [teamId]: notes };
          })
        }
        onAttach={sourceId =>
          run(async () => {
            if (!proposal || !canAttachToProposal(teamId, proposal)) return;
            const source = await api.attach(proposal.id, sourceId);
            setSources(previous => [...previous.filter(item => item.id !== source.id), source]);
            setNotice('Shortlisted source attached to proposal.');
          })
        }
      />
    </details>
  ) : null;

  return (
    <div className="workspace-app">
      <WorkspaceTopBar
        currentView={currentView}
        title={title}
        teams={teams}
        teamId={teamId}
        members={teamMembers}
        user={user}
        busy={busy}
        sidebarOpen={sidebarOpen}
        settingsContent={teamSettingsContent}
        inviteContent={inviteForm}
        onTeamChange={changeTeam}
        onToggleSidebar={() => setSidebarOpen(value => !value)}
        onSignOut={() => {
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
      />
      <div className="app-shell-body">
        <AppSidebar
          currentView={currentView}
          busy={busy}
          canEdit={selectedTeam?.role !== 'viewer'}
          proposals={proposals}
          teamId={teamId}
          activeProposalId={proposal?.id ?? null}
          mobileOpen={sidebarOpen}
          shortlist={shortlistContent}
          onNavigate={navigateView}
          onOpenProposal={id => {
            if (guardEdits()) void run(() => openProposal(id));
          }}
          onCreateProposal={createProposal}
          onDeleteProposal={deleteProposal}
          onMobileClose={() => setSidebarOpen(false)}
        />
        <div className="app-content">

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
        <div className={`workspace-editor-layout ${contextOpen ? 'with-context-panel' : ''}`}>
          {false && <aside className="workspace-sidebar" aria-label="Teams and proposals">
            <details className="workspace-utility-card">
              <summary>Team settings, members & invitations</summary>
              <p className="workspace-help">
                Use these settings to manage who can work on this team. Editors can change proposals;
                viewers can only read them.
              </p>
              <div className="sidebar-section">
                <div className="sidebar-header">
                  <h3>Team access</h3>
                  <button type="button" className="text-button" onClick={() => void run(refreshLists)}>
                    Refresh
                  </button>
                </div>

                {selectedTeam && user && (
                  <TeamMembersPanel
                    key={selectedTeam?.id}
                    team={selectedTeam!}
                    currentUserId={user!.id}
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
            </details>

            <section className="sidebar-section workspace-step-card" aria-labelledby="proposal-select-heading">
              <div className="workspace-step-heading">
                <span className="workspace-step-number" aria-hidden="true">1</span>
                <div>
                  <h2 id="proposal-select-heading">Choose or create a proposal</h2>
                  <p>A proposal is the shared document for one research idea. Open one to continue, or create one to start fresh. The saved version number changes when edits are saved.</p>
                </div>
                <span className="count-pill">
                  {proposals.filter((item) => item.team_id === teamId).length}{' '}
                  {proposals.filter((item) => item.team_id === teamId).length === 1 ? 'proposal' : 'proposals'}
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
                        <small className="muted">
                          {item.id === proposal?.id ? 'Currently open · ' : ''}Saved version {item.revision}
                        </small>
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
                  placeholder="Name your research idea…"
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
            </section>

            {/* Team Shortlist Preview */}
            {selectedTeam && (
              <details className="workspace-utility-card">
                <summary>Manage team shortlist</summary>
                <p className="workspace-help">
                  A shortlist is a team-wide holding area for papers and researcher profiles. Attach a saved
                  source to the open proposal when you are ready to use it.
                </p>
                <div className="sidebar-section">
                  <ShortlistPanel
                    team={selectedTeam!}
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
              </details>
            )}
          </aside>}

          <main id="main" className="workspace-editor-canvas">
            {proposal ? (
              <div className="editor-card">
                <div className="editor-toolbar">
                  <label className="editor-title-input">
                    <span className="sr-only">Proposal title</span>
                    <input
                      value={title}
                      onChange={event => setTitle(event.target.value)}
                      maxLength={240}
                      required
                      disabled={busy || !editable}
                      placeholder="Untitled proposal"
                    />
                  </label>
                  <span className={`save-status-pill ${dirty ? 'unsaved' : 'saved'}`} role="status">
                    {dirty ? 'Unsaved changes' : `Saved · v${proposal.revision}`}
                  </span>
                  <div className="editor-toolbar-actions">
                    <button
                      type="button"
                      className="primary"
                      disabled={busy || !editable || !dirty || !title.trim() || !!conflict}
                      onClick={() => void run(() => save())}
                    >
                      <Save className="w-4 h-4" aria-hidden="true" />
                      <span>Save</span>
                    </button>
                    <button
                      type="button"
                      className="icon-button"
                      aria-label="Download proposal as Markdown"
                      title="Download as Markdown"
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
                      <Download className="w-4 h-4" aria-hidden="true" />
                    </button>
                    <button
                      ref={contextTriggerRef}
                      type="button"
                      className="icon-button context-toggle"
                      aria-label={contextOpen ? 'Close proposal tools' : 'Open proposal tools'}
                      aria-expanded={contextOpen}
                      onClick={() => setContextOpen(value => !value)}
                    >
                      <PanelRight className="w-4 h-4" aria-hidden="true" />
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

                <div className="editor-inputs">
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
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Edit</span>
                      </button>
                      <button
                        type="button"
                        className={`mode-btn ${editorMode === 'split' ? 'active' : ''}`}
                        onClick={() => setEditorMode('split')}
                        title="Split view (Editor + Live Preview)"
                      >
                        <Columns className="w-3.5 h-3.5" />
                        <span>Split</span>
                      </button>
                      <button
                        type="button"
                        className={`mode-btn ${editorMode === 'preview' ? 'active' : ''}`}
                        onClick={() => setEditorMode('preview')}
                        title="Formatted manuscript preview"
                      >
                        <Eye className="w-3.5 h-3.5" />
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
                      placeholder="Start with your research question, aims, or methods…"
                      rows={26}
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
                        rows={26}
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

              </div>
            ) : (
              <div className="workspace-dashboard">
                {/* Hero Welcome Banner */}
                <div className="dashboard-hero">
                  <div className="dashboard-hero-content">
                    <div className="dashboard-badge">
                      <Sparkles className="w-4 h-4 text-amber-500" />
                      <span>{selectedTeam ? `${selectedTeam.name} Workspace` : 'Research Workspace'}</span>
                    </div>
                    <h2>
                      Welcome back{user?.name ? <>, <span className="hero-name">{user.name.split(' ')[0]}</span></> : ''} <span className="hero-wave" aria-hidden="true">👋</span>
                    </h2>
                    <p className="dashboard-subtitle">
                      Start a new proposal, continue where you left off, or explore the knowledge graph to find your next collaborator.
                    </p>
                  </div>
                  <div className="dashboard-hero-glyph" aria-hidden="true">
                    <div className="hero-glyph-ring">
                      <Sparkles className="w-7 h-7" />
                    </div>
                  </div>
                </div>

                {/* Quick Proposal Creator Card */}
                <div className="dashboard-quickstart-card">
                  <div className="quickstart-header">
                    <div className="quickstart-title-row">
                      <Plus className="w-5 h-5 text-blue-600" />
                      <h3>Create a Research Proposal</h3>
                    </div>
                    <p className="muted">Enter a proposal title or start from a pre-configured grant template.</p>
                  </div>

                  <form
                    className="quickstart-form"
                    onSubmit={(e) => {
                      e.preventDefault();
                      if (dashboardProposalTitle.trim()) {
                        void createProposal(dashboardProposalTitle.trim());
                        setDashboardProposalTitle('');
                      }
                    }}
                  >
                    <input
                      type="text"
                      className="quickstart-input"
                      placeholder="e.g. Multimodal Deep Learning for Assistive Drone Navigation…"
                      value={dashboardProposalTitle}
                      onChange={(e) => setDashboardProposalTitle(e.target.value)}
                      disabled={busy || !teamId || !canEditTeam}
                    />
                    <button
                      type="submit"
                      className="button primary quickstart-button"
                      disabled={busy || !teamId || !canEditTeam || !dashboardProposalTitle.trim()}
                    >
                      <span>Create Draft</span>
                    </button>
                  </form>

                  <div className="template-quickstarts">
                    <span className="template-label">Or start with a grant template:</span>
                    <div className="template-chips">
                      <button
                        type="button"
                        className="template-chip"
                        onClick={() => void createProposalWithTemplate('NSF Project Description', 'nsf')}
                        disabled={busy || !teamId || !canEditTeam}
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>NSF Project Description</span>
                      </button>
                      <button
                        type="button"
                        className="template-chip"
                        onClick={() => void createProposalWithTemplate('NIH Specific Aims', 'nih')}
                        disabled={busy || !teamId || !canEditTeam}
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>NIH Specific Aims</span>
                      </button>
                      <button
                        type="button"
                        className="template-chip"
                        onClick={() => void createProposalWithTemplate('DoD / DARPA Technical Approach', 'darpa')}
                        disabled={busy || !teamId || !canEditTeam}
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>DoD / DARPA Technical</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Team Proposals Grid (if any exist) */}
                {proposals.length > 0 && (
                  <div className="dashboard-section">
                    <div className="section-header-row">
                      <h3>Active Proposals ({proposals.length})</h3>
                      <span className="section-subtext">Click any card to continue drafting</span>
                    </div>
                    <div className="proposals-cards-grid">
                      {proposals.map((item) => (
                        <div
                          key={item.id}
                          className="proposal-launch-card"
                          onClick={() => void openProposal(item.id)}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => e.key === 'Enter' && void openProposal(item.id)}
                        >
                          <div className="card-top-meta">
                            <span className="role-tag">{item.role}</span>
                            <span className="revision-tag">v{item.revision}</span>
                          </div>
                          <h4 className="proposal-card-title">{item.title}</h4>
                          <p className="proposal-card-snippet">
                            {item.content
                              ? item.content.slice(0, 140) + '…'
                              : 'Blank proposal draft. Ready for research aims, methodologies, and literature citations.'}
                          </p>
                          <div className="card-footer-meta">
                            <span className="card-date">
                              {new Date(item.updated_at).toLocaleDateString(undefined, {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric',
                              })}
                            </span>
                            <span className="open-link">
                              Open Editor <ArrowRight className="w-3.5 h-3.5" />
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Platform Capabilities & Quick Nav */}
                <div className="dashboard-section">
                  <div className="section-header-row">
                    <h3>Explore Research Capabilities</h3>
                    <span className="section-subtext">Integrated tools grounded on verified RIT scholarship</span>
                  </div>
                  <div className="tools-cards-grid">
                    <div
                      className="tool-card"
                      onClick={() => navigateView('chat')}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && navigateView('chat')}
                    >
                      <div className="tool-icon-circle chat">
                        <MessageSquare className="w-5 h-5 text-indigo-600" />
                      </div>
                      <h4>Research Chat</h4>
                      <p>Ask questions across verified publications and faculty profiles with full multi-session memory and citations.</p>
                      <span className="tool-card-action">Launch Chat &rarr;</span>
                    </div>

                    <div
                      className="tool-card"
                      onClick={() => navigateView('graph')}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && navigateView('graph')}
                    >
                      <div className="tool-icon-circle graph">
                        <Network className="w-5 h-5 text-teal-600" />
                      </div>
                      <h4>Knowledge Graph</h4>
                      <p>Interactive force-directed graph with 2,500+ nodes, dark obsidian theme, and ego-network clustering.</p>
                      <span className="tool-card-action">Explore Graph &rarr;</span>
                    </div>

                    <div
                      className="tool-card"
                      onClick={() => navigateView('collaborators')}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && navigateView('collaborators')}
                    >
                      <div className="tool-icon-circle collaborators">
                        <Users className="w-5 h-5 text-blue-600" />
                      </div>
                      <h4>Collaborator Discovery</h4>
                      <p>Match your research concept with faculty research affinities, publication records, and departmental focus.</p>
                      <span className="tool-card-action">Find Collaborators &rarr;</span>
                    </div>

                    <div
                      className="tool-card"
                      onClick={() => navigateView('search')}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && navigateView('search')}
                    >
                      <div className="tool-icon-circle search">
                        <Search className="w-5 h-5 text-amber-600" />
                      </div>
                      <h4>Literature Discovery</h4>
                      <p>Hybrid semantic and BM25 search across thousands of indexed papers with instant evidence attachment.</p>
                      <span className="tool-card-action">Search Literature &rarr;</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </main>

          <ContextPanel
            userId={user.id}
            activeTab={workspaceRightTab}
            open={contextOpen}
            sourceCount={sources.length}
            triggerRef={contextTriggerRef}
            onTabChange={setWorkspaceRightTab}
            onOpenChange={setContextOpen}
          >
            <>

            {/* TAB: ATTACHED EVIDENCE */}
            {workspaceRightTab === 'sources' && (
              <div className="sidebar-tab-content">
                <div className="tab-instructions">
                  <p className="muted">
                    Select sources to make them available to AI Draft.
                  </p>
                  {proposal && (
                    <p className="source-selection-count">
                      {selected.length} of {sources.length} source{sources.length === 1 ? '' : 's'} selected
                      for drafting.
                    </p>
                  )}
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
                            {s.is_public ? 'Public literature' : 'Added to this proposal'}
                          </small>
                        </div>
                      </label>
                      <details className="source-preview-details">
                        <summary>Preview source text and link</summary>
                        <pre>{s.text}</pre>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '6px', flexWrap: 'wrap' }}>
                          <OriginLink value={s.origin} />
                          {s.is_public && looksLikePaperSource({ title: s.title, origin: s.origin }) && (
                            <button
                              type="button"
                              className="button small"
                              style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '11px', padding: '2px 8px' }}
                              onClick={() => setActivePdf({ id: s.id, title: s.title })}
                            >
                              <FileText className="w-3 h-3 text-rose-600" />
                              <span>Read PDF</span>
                            </button>
                          )}
                        </div>
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
                      <label>
                        Source title
                        <input
                          value={sourceTitle}
                          onChange={(e) => setSourceTitle(e.target.value)}
                          placeholder="For example, the paper title"
                          required
                        />
                      </label>
                      <label>
                        Where it came from
                        <input
                          value={sourceOrigin}
                          onChange={(e) => setSourceOrigin(e.target.value)}
                          placeholder="Paste a web link or DOI"
                          required
                        />
                      </label>
                      <label>
                        Source text
                        <textarea
                          value={sourceText}
                          onChange={(e) => setSourceText(e.target.value)}
                          placeholder="Paste the useful passage or document text…"
                          rows={5}
                          required
                        />
                      </label>
                      <button className="button small">Attach text</button>
                    </form>
                  </details>
                )}
              </div>
            )}

            {/* TAB: AI DRAFTING */}
            {workspaceRightTab === 'ai' && (
              <div className="sidebar-tab-content">
                <div className="ai-assistant-header">
                  <div className="ai-model-tag">
                    <Sparkles className="w-3.5 h-3.5 text-[#225bb2]" />
                    {modelInfo?.provider === 'fixture' && (
                      <span className="fixture-badge" tabIndex={0} title="Sample response only; no live AI model call is made.">
                        Demo fixture (no live model call)
                        <CircleHelp className="w-3 h-3" aria-hidden="true" />
                      </span>
                    )}
                    {modelInfo?.provider !== 'fixture' && (
                      <span>{modelInfo?.display_name ?? 'AI Draft Assistant'}</span>
                    )}
                  </div>
                  <p className="safety-note">Suggestions are never added automatically; review before adding.</p>
                  <p className="safety-note">Verify every claim; an exact quote does not prove the surrounding claim.</p>
                </div>

                <form
                  className="draft-prompt-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void requestDraft();
                  }}
                >
                  <label>
                    Which part are you drafting?
                    <input
                      value={section}
                      onChange={(e) => setSection(e.target.value)}
                      placeholder="e.g. Research approach, objectives, or impact"
                      required
                      disabled={!proposal || !editable || busy}
                    />
                  </label>
                  <label>
                    What should the suggestion cover?
                    <textarea
                      value={instruction}
                      onChange={(e) => setInstruction(e.target.value)}
                      placeholder="Ask for a specific draft based on your selected sources…"
                      rows={4}
                      maxLength={8000}
                      required
                      disabled={!proposal || !editable || busy}
                    />
                  </label>
                  <div className="prompt-examples" aria-label="Example prompts">
                    {[
                      'Summarize the main approaches in these sources.',
                      'Compare what the sources agree and disagree about.',
                      'Identify an unanswered question suggested by these sources.',
                    ].map(example => (
                      <button
                        key={example}
                        type="button"
                        className="prompt-chip"
                        disabled={!proposal || busy}
                        onClick={() => setInstruction(example)}
                      >
                        {example}
                      </button>
                    ))}
                  </div>
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
                    <p className="muted small">Select sources in the Sources tab first.</p>
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
                            <div className="suggestion-text">
                              <DraftText text={job.output.text} citations={job.output.citations} jobId={job.id} />
                            </div>
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
                                <blockquote
                                  key={`${c.source_id}-${idx}`}
                                  id={`draft-citation-${job.id}-${idx}`}
                                  className="citation-quote"
                                >
                                  <span className="citation-number">[{idx + 1}]</span>
                                  <p>“{c.quote}”</p>
                                  <footer>
                                    <strong>{c.title}</strong>
                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '4px', flexWrap: 'wrap' }}>
                                      <OriginLink value={c.origin} />
                                      {looksLikePaperSource({ title: c.title, origin: c.origin }) && (
                                        <button
                                          type="button"
                                          className="button small"
                                          style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '11px', padding: '2px 8px' }}
                                          onClick={() => setActivePdf({ id: c.source_id, title: c.title })}
                                        >
                                          <FileText className="w-3 h-3 text-rose-600" />
                                          <span>Read PDF</span>
                                        </button>
                                      )}
                                    </div>
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
            {workspaceRightTab === 'funding' && (
              proposal
                ? <PursuitPanel proposal={proposal} />
                : <p className="empty">Open a proposal to track its funding progress.</p>
            )}
            </>
          </ContextPanel>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* VIEW 2: FIND COLLABORATORS                                     */}
      {/* ------------------------------------------------------------- */}
      {currentView === 'collaborators' && (
        <main className="collaborators-view-shell" aria-labelledby="collab-heading">
          <div className="view-intro-hero">
            <h1 id="collab-heading">Faculty Collaborator Discovery & Idea Synthesizer</h1>
            <p className="muted">
              Explore strategic interdisciplinary faculty matches, federal funding alignment (NSF, NIH, DARPA, DOE),
              and verified publication overlap across 3,000+ academic sources.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', marginBottom: '1.5rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
            <button
              type="button"
              className={`nav-tab ${collaboratorViewMode === 'synthesizer' ? 'active' : ''}`}
              onClick={() => setCollaboratorViewMode('synthesizer')}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '8px 16px', borderRadius: '6px', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
            >
              <Sparkles className="w-4 h-4 text-emerald-600" />
              <span>AI Idea Synthesizer & Grant Fit</span>
            </button>
            <button
              type="button"
              className={`nav-tab ${collaboratorViewMode === 'lexical' ? 'active' : ''}`}
              onClick={() => setCollaboratorViewMode('lexical')}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '8px 16px', borderRadius: '6px', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
            >
              <Search className="w-4 h-4 text-slate-600" />
              <span>Keyword & Term Directory Matcher</span>
            </button>
          </div>

          {collaboratorViewMode === 'synthesizer' ? (
            <CollaborationHub
              onAttachSource={proposal ? handleAttachSource : undefined}
              onShortlist={handleShortlistCandidate}
              attachedSourceIds={selected}
              proposalOpen={Boolean(proposal)}
            />
          ) : (
            <>
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
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <OriginLink value={match.origin} />
                      </div>
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
            </>
          )}
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
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <OriginLink value={item.origin} />
                    {item.kind === 'paper' && item.evidence_kind === 'public' && (
                      <button
                        type="button"
                        className="button small"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '11px', padding: '2px 8px' }}
                        onClick={() => setActivePdf({ id: item.source_id, title: item.title })}
                      >
                        <FileText className="w-3 h-3 text-rose-600" />
                        <span>Read PDF</span>
                      </button>
                    )}
                  </div>
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

          <div className={`chat-container-grid ${evidenceCollapsed ? 'citations-collapsed' : ''}`}>
            <div className="chat-main-column">
              <ChatInterface
                proposalId={proposal?.id}
                proposalTitle={proposal?.title}
                onCitationsChange={(c) => setChatCitations(c)}
                citationsCollapsed={evidenceCollapsed}
                citationsCount={chatCitations.length}
                hasUnseenCitations={hasUnseenCitations}
                onShowCitations={() => setEvidenceCollapsed(false)}
              />
            </div>

            {!evidenceCollapsed && (
              <aside className="chat-citations-column" aria-label="Sources used in this conversation">
                <div className="citations-column-head">
                  <div className="citations-column-heading">
                    <BookOpen className="w-4 h-4" aria-hidden="true" />
                    <span>Sources</span>
                    {chatCitations.length > 0 && (
                      <span className="citations-column-count">{chatCitations.length}</span>
                    )}
                  </div>
                  <button
                    type="button"
                    className="icon-button citations-column-close"
                    onClick={() => setEvidenceCollapsed(true)}
                    title="Hide sources panel"
                    aria-label="Hide sources panel"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
                <CitationPanel
                  citations={chatCitations}
                  onViewPdf={(id, title) => setActivePdf({ id, title })}
                />
              </aside>
            )}
          </div>
        </main>
      )}
        </div>
      </div>

      {activePdf && (
        <PdfViewerModal
          sourceId={activePdf.id}
          title={activePdf.title}
          onClose={() => setActivePdf(null)}
        />
      )}
    </div>
  );
}
