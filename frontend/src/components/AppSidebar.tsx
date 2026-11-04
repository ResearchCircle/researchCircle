'use client';

import { useState, type FormEvent, type ReactNode } from 'react';
import {
  ChevronLeft,
  Compass,
  FileText,
  MessageSquare,
  Network,
  Plus,
  Search,
  Sparkles,
  Trash2,
  Users,
} from 'lucide-react';
import type { Proposal } from '@/lib/api';

export type AppView = 'workspace' | 'collaborators' | 'graph' | 'search' | 'chat' | 'campus';

type Props = {
  currentView: AppView;
  busy: boolean;
  canEdit: boolean;
  proposals: Proposal[];
  teamId: string;
  activeProposalId: string | null;
  mobileOpen: boolean;
  shortlist: ReactNode;
  onNavigate: (view: AppView) => void;
  onOpenProposal: (id: string) => void;
  onCreateProposal: (title: string) => Promise<void>;
  onDeleteProposal?: (proposal: Proposal) => Promise<void>;
  onMobileClose: () => void;
};

const navigation: { view: AppView; label: string; icon: typeof FileText }[] = [
  { view: 'campus', label: 'Living Campus Graph', icon: Sparkles },
  { view: 'workspace', label: 'Workspace', icon: FileText },
  { view: 'collaborators', label: 'Find Collaborators', icon: Users },
  { view: 'graph', label: 'Knowledge Graph', icon: Network },
  { view: 'search', label: 'Literature Search', icon: Search },
  { view: 'chat', label: 'Research Chat', icon: MessageSquare },
];

export default function AppSidebar({
  currentView,
  busy,
  canEdit,
  proposals,
  teamId,
  activeProposalId,
  mobileOpen,
  shortlist,
  onNavigate,
  onOpenProposal,
  onCreateProposal,
  onDeleteProposal,
  onMobileClose,
}: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const teamProposals = proposals.filter(proposal => proposal.team_id === teamId);

  const navigate = (view: AppView) => {
    onNavigate(view);
    onMobileClose();
  };

  const createProposal = async (event: FormEvent) => {
    event.preventDefault();
    if (!newTitle.trim() || creating) return;
    setCreating(true);
    try {
      await onCreateProposal(newTitle.trim());
      setNewTitle('');
    } finally {
      setCreating(false);
    }
  };

  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={onMobileClose}
        />
      )}
      <aside
        className={`app-sidebar ${collapsed ? 'is-collapsed' : ''} ${mobileOpen ? 'is-mobile-open' : ''}`}
        aria-label="Application sidebar"
      >
        <div className="sidebar-brand">
          <span className="brand-mark small" aria-hidden="true">trb</span>
          <span className="sidebar-brand-label">
            <strong>Tiger Research Buddy</strong>
            <small>Research workspace</small>
          </span>
          <button
            type="button"
            className="sidebar-collapse-button"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={() => setCollapsed(value => !value)}
          >
            <ChevronLeft className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <nav className="sidebar-navigation" aria-label="Main navigation">
          {navigation.map(({ view, label, icon: Icon }) => (
            <button
              key={view}
              type="button"
              className={`sidebar-nav-item ${currentView === view ? 'active' : ''}`}
              aria-current={currentView === view ? 'page' : undefined}
              aria-label={label}
              title={collapsed ? label : undefined}
              onClick={() => navigate(view)}
            >
              <Icon className="w-4 h-4" aria-hidden="true" />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        {currentView === 'workspace' && (
          <div className="sidebar-proposals">
            <div className="sidebar-section-title">
              <h2>Proposals</h2>
              <span>{teamProposals.length} {teamProposals.length === 1 ? 'proposal' : 'proposals'}</span>
            </div>
            {!collapsed && (
              <>
                <div className="sidebar-proposal-list" role="list" aria-label="Team proposals">
                  {teamProposals.map(proposal => (
                    <div
                      key={proposal.id}
                      className={`sidebar-proposal-row ${proposal.id === activeProposalId ? 'active' : ''}`}
                      role="listitem"
                    >
                      <button
                        type="button"
                        className={`sidebar-proposal-item ${proposal.id === activeProposalId ? 'active' : ''}`}
                        aria-current={proposal.id === activeProposalId ? 'page' : undefined}
                        disabled={busy || deletingId === proposal.id}
                        onClick={() => {
                          onOpenProposal(proposal.id);
                          onMobileClose();
                        }}
                      >
                        <span>{proposal.title}</span>
                        <small>Saved · v{proposal.revision}</small>
                      </button>
                      {canEdit && onDeleteProposal && (
                        <button
                          type="button"
                          className="sidebar-proposal-delete"
                          aria-label={`Delete proposal ${proposal.title}`}
                          title="Delete proposal"
                          disabled={busy || deletingId === proposal.id}
                          onClick={async (event) => {
                            event.stopPropagation();
                            if (!window.confirm(`Delete “${proposal.title}”? This permanently removes the proposal, its private sources, drafts and tracking history.`)) return;
                            setDeletingId(proposal.id);
                            try {
                              await onDeleteProposal(proposal);
                            } finally {
                              setDeletingId(null);
                            }
                          }}
                        >
                          <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                        </button>
                      )}
                    </div>
                  ))}
                  {teamProposals.length === 0 && (
                    <p className="sidebar-empty" role="listitem">No proposals yet.</p>
                  )}
                </div>
                <form className="sidebar-new-proposal" onSubmit={createProposal}>
                  <label className="sr-only" htmlFor="sidebar-new-proposal-title">New proposal title</label>
                  <input
                    id="sidebar-new-proposal-title"
                    value={newTitle}
                    onChange={event => setNewTitle(event.target.value)}
                    placeholder="New proposal name"
                    maxLength={240}
                    required
                    disabled={creating || busy || !teamId || !canEdit}
                  />
                  <button type="submit" className="sidebar-new-button" disabled={creating || busy || !teamId || !canEdit}>
                    <Plus className="w-4 h-4" aria-hidden="true" />
                    <span>New proposal</span>
                  </button>
                </form>
              </>
            )}
          </div>
        )}

        {currentView === 'workspace' && (
          <div className="sidebar-shortlist">
            {collapsed ? (
              <button
                type="button"
                className="sidebar-nav-item"
                aria-label="Saved sources"
                title="Saved sources"
                onClick={() => setCollapsed(false)}
              >
                <FileText className="w-4 h-4" aria-hidden="true" />
                <span>Saved Sources</span>
              </button>
            ) : shortlist}
          </div>
        )}
      </aside>
    </>
  );
}
