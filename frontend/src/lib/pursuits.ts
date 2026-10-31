import type { OutcomeState } from './api';

export type OutcomeAttempt = { fingerprint: string; key: string };

export function outcomeAttempt(previous: OutcomeAttempt | null, proposalId: string, outcome: OutcomeState, awardReference: string | null, newKey: string): OutcomeAttempt {
  const fingerprint = JSON.stringify([proposalId, outcome, awardReference]);
  return previous?.fingerprint === fingerprint ? previous : { fingerprint, key: newKey };
}

export function isTerminal(state: string | undefined): boolean {
  return state === 'won' || state === 'lost' || state === 'withdrawn';
}

export function localDeadline(value: string): { deadline: string | null; deadline_timezone: string | null } {
  if (!value) return { deadline: null, deadline_timezone: null };
  const parts = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(value);
  if (!parts) throw new Error('Enter a valid deadline date and time.');
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) throw new Error('Enter a valid deadline date and time.');
  const [, year, month, day, hour, minute] = parts.map(Number);
  if (date.getFullYear() !== year || date.getMonth() + 1 !== month || date.getDate() !== day || date.getHours() !== hour || date.getMinutes() !== minute) {
    throw new Error('This local deadline does not exist in your timezone. Choose another date and time.');
  }
  return { deadline: date.toISOString(), deadline_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone };
}

export class RequestScope {
  private generation = 0;
  begin(): number { return ++this.generation; }
  current(generation: number): boolean { return generation === this.generation; }
  invalidate(): void { ++this.generation; }
}
