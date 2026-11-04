'use client';

import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Menu, MoreHorizontal } from 'lucide-react';
import type { Team, TeamMember, User } from '@/lib/api';
import type { AppView } from './AppSidebar';

type Props = {
  currentView: AppView;
  title: string;
  teams: Team[];
  teamId: string;
  members: TeamMember[];
  user: User;
  busy: boolean;
  sidebarOpen: boolean;
  settingsContent: ReactNode;
  inviteContent: ReactNode;
  onTeamChange: (teamId: string) => void;
  onSignOut: () => void;
  onToggleSidebar: () => void;
};

const viewTitles: Record<AppView, string> = {
  campus: 'Living Campus Graph',
  workspace: 'Proposals',
  collaborators: 'Find collaborators',
  graph: 'Knowledge graph',
  search: 'Literature search',
  chat: 'Research chat',
};

function initials(name: string) {
  return name.trim().split(/\s+/).slice(0, 2).map(part => part[0]?.toUpperCase() ?? '').join('');
}

export default function WorkspaceTopBar({
  currentView,
  title,
  teams,
  teamId,
  members,
  user,
  busy,
  sidebarOpen,
  settingsContent,
  inviteContent,
  onTeamChange,
  onSignOut,
  onToggleSidebar,
}: Props) {
  const [dialog, setDialog] = useState<'settings' | 'invite' | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const menuRef = useRef<HTMLDetailsElement>(null);
  const dialogReturnFocusRef = useRef<HTMLElement | null>(null);
  const selectedTeam = teams.find(team => team.id === teamId);
  const teammates = members.filter(member => member.id !== user.id);
  const visibleMembers = teammates.slice(0, 4);
  const additionalMembers = Math.max(0, teammates.length - visibleMembers.length);

  useEffect(() => {
    const element = dialogRef.current;
    if (!element) return;
    if (dialog && !element.open) element.showModal();
    if (!dialog && element.open) element.close();
  }, [dialog]);

  const closeDialog = () => {
    dialogRef.current?.close();
    setDialog(null);
    dialogReturnFocusRef.current?.focus();
  };

  return (
    <>
      <header className="workspace-topbar">
        <div className="topbar-leading">
          <button
            type="button"
            className="icon-button mobile-sidebar-toggle"
            aria-label={sidebarOpen ? 'Close navigation' : 'Open navigation'}
            aria-expanded={sidebarOpen}
            onClick={onToggleSidebar}
          >
            <Menu className="w-5 h-5" aria-hidden="true" />
          </button>
          <div className="breadcrumb" aria-label="Current location">
            <span>{viewTitles[currentView]}</span>
            {currentView === 'workspace' && title && (
              <>
                <span aria-hidden="true">/</span>
                <strong>{title}</strong>
              </>
            )}
          </div>
        </div>

        <div className="topbar-actions">
          <label className="team-picker">
            <span className="sr-only">Team workspace</span>
            <select
              value={teamId}
              disabled={busy}
              onChange={event => onTeamChange(event.target.value)}
              className="team-select"
              aria-label="Team workspace"
            >
              <option value="" disabled>Choose a team</option>
              {teams.map(team => (
                <option key={team.id} value={team.id}>{team.name} · {team.role}</option>
              ))}
            </select>
          </label>

          {teammates.length > 0 && (
            <div className="member-avatar-stack" aria-label={`${teammates.length} teammate${teammates.length === 1 ? '' : 's'}`}>
              {visibleMembers.map(member => (
                <span
                  key={member.id}
                  className="member-avatar"
                  title={`${member.name} (${member.role})`}
                  aria-label={`${member.name}, ${member.role}`}
                >
                  {initials(member.name)}
                </span>
              ))}
              {additionalMembers > 0 && (
                <span className="member-avatar member-avatar-more" aria-label={`${additionalMembers} more teammates`}>
                  +{additionalMembers}
                </span>
              )}
            </div>
          )}

          <button
            type="button"
            className="button invite-button"
            disabled={busy || selectedTeam?.role !== 'owner'}
            title={selectedTeam?.role === 'owner' ? 'Invite a teammate' : 'Only team owners can invite members'}
            onClick={event => {
              dialogReturnFocusRef.current = event.currentTarget;
              setDialog('invite');
            }}
          >
            Invite
          </button>

          <details className="user-menu" ref={menuRef}>
            <summary aria-label={`Account menu for ${user.name}`} title="Account menu">
              <span className="user-avatar" aria-hidden="true">{initials(user.name)}</span>
              <span className="user-menu-name">{user.name}</span>
              <MoreHorizontal className="w-4 h-4" aria-hidden="true" />
            </summary>
            <div className="user-menu-panel">
              <strong>{user.name}</strong>
              <small>{user.email}</small>
              <button
                type="button"
                onClick={() => {
                  if (menuRef.current) menuRef.current.open = false;
                  dialogReturnFocusRef.current = menuRef.current?.querySelector('summary') ?? null;
                  setDialog('settings');
                }}
              >
                Team settings & members
              </button>
              <button type="button" disabled={busy} onClick={onSignOut}>Sign out</button>
            </div>
          </details>
        </div>
      </header>

      <dialog
        ref={dialogRef}
        className="team-dialog"
        aria-labelledby="team-dialog-title"
        onClose={() => setDialog(null)}
        onKeyDown={event => {
          if (event.key === 'Escape') {
            event.preventDefault();
            closeDialog();
          }
        }}
        onCancel={event => {
          event.preventDefault();
          closeDialog();
        }}
      >
        <div className="team-dialog-header">
          <div>
            <p className="dialog-eyebrow">{selectedTeam?.name ?? 'Team'}</p>
            <h2 id="team-dialog-title">{dialog === 'invite' ? 'Invite a teammate' : 'Team settings & members'}</h2>
          </div>
          <button type="button" className="icon-button" aria-label="Close dialog" onClick={closeDialog}>×</button>
        </div>
        <div className="team-dialog-content">
          {dialog === 'invite' ? inviteContent : settingsContent}
        </div>
      </dialog>
    </>
  );
}
