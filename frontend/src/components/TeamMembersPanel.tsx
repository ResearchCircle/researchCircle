
'use client';

import { useEffect, useState } from 'react';
import {
  api,
  type Team,
  type TeamMember,
} from '@/lib/api';

type Props = {
  team: Team;
  currentUserId: string;
  onChanged: () => Promise<void>;
  beforeSelfChange: () => boolean;
};

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : 'Something went wrong. Please try again.';
}

export default function TeamMembersPanel({
  team,
  currentUserId,
  onChanged,
  beforeSelfChange,
}: Props) {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const isOwner = team.role === 'owner';

  useEffect(() => {
    let active = true;

    api.teamDetails(team.id)
      .then(details => {
        if (active) setMembers(details.members);
      })
      .catch(err => {
        if (active) setError(errorMessage(err));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [team.id]);

  async function refreshMembers() {
    const details = await api.teamDetails(team.id);
    setMembers(details.members);
  }

  async function changeRole(
    member: TeamMember,
    newRole: Team['role']
  ) {
    if (!isOwner || member.role === newRole) return;

    if (member.id === currentUserId && !beforeSelfChange()) {
      return;
    }

    const confirmed = window.confirm(
      `Change ${member.name}'s role from ${member.role} to ${newRole}?`
    );

    if (!confirmed) return;

    setPendingId(member.id);
    setError('');
    setNotice('');

    try {
      await api.updateMemberRole(team.id, member.id, newRole);
      await onChanged();
      await refreshMembers();
      setNotice(`${member.name}'s role was updated.`);
    } catch (err) {
      setError(errorMessage(err));
      try {
        await refreshMembers();
      } catch {
        // Preserve the original error.
      }
    } finally {
      setPendingId(null);
    }
  }

  async function removeMember(member: TeamMember) {
    if (!isOwner) return;

    if (member.id === currentUserId && !beforeSelfChange()) {
      return;
    }

    const confirmed = window.confirm(
      `Remove ${member.name} (${member.email}) from ${team.name}? This will revoke their team access.`
    );

    if (!confirmed) return;

    setPendingId(member.id);
    setError('');
    setNotice('');

    try {
      await api.removeMember(team.id, member.id);
      await onChanged();

      if (member.id !== currentUserId) {
        await refreshMembers();
        setNotice(`${member.name} was removed from the team.`);
      }
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPendingId(null);
    }
  }

  return (
    <details>
      <summary>Team members ({members.length})</summary>

      <section aria-label="Team member management">
        {loading && (
          <p className="muted" role="status">
            Loading team members…
          </p>
        )}

        {error && (
          <p className="alert error" role="alert">
            {error}
          </p>
        )}

        {notice && (
          <p className="success" role="status">
            {notice}
          </p>
        )}

        {!loading && members.length === 0 && (
          <p className="muted">
            No members found.
          </p>
        )}

        {members.map(member => (
          <div
            key={member.id}
            className="team-member"
          >
            <div className="team-member-info">
              <strong>
                {member.name}
                {member.id === currentUserId ? ' (you)' : ''}
              </strong>
              <small>{member.email}</small>
            </div>

            {isOwner ? (
              <div className="team-member-actions">
                <label>
                  Access
                  <select
                    aria-label={`Role for ${member.name}`}
                    value={member.role}
                    disabled={pendingId !== null}
                    onChange={event =>
                      void changeRole(
                        member,
                        event.target.value as Team['role']
                      )
                    }
                  >
                    <option value="owner">Owner</option>
                    <option value="editor">Editor</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </label>

                <button
                  type="button"
                  disabled={pendingId !== null}
                  onClick={() => void removeMember(member)}
                >
                  Remove
                </button>
              </div>
            ) : (
              <span className="muted">{member.role}</span>
            )}
          </div>
        ))}

        {!isOwner && (
          <p className="muted">
            Only team owners can change member access.
          </p>
        )}

        <button
          type="button"
          className="text-button"
          disabled={pendingId !== null || loading}
          onClick={() => {
            setError('');
            setNotice('');
            void refreshMembers().catch(err =>
              setError(errorMessage(err))
            );
          }}
        >
          Refresh members
        </button>
      </section>
    </details>
  );
}
