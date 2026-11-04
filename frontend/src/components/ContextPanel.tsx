'use client';

import { useCallback, useEffect, useRef, type KeyboardEvent, type ReactNode, type RefObject } from 'react';

export type ContextTab = 'ai' | 'sources' | 'funding';

type Props = {
  userId: string;
  activeTab: ContextTab;
  open: boolean;
  sourceCount: number;
  children: ReactNode;
  triggerRef: RefObject<HTMLButtonElement | null>;
  onTabChange: (tab: ContextTab) => void;
  onOpenChange: (open: boolean) => void;
};

const tabs: { id: ContextTab; label: string }[] = [
  { id: 'ai', label: 'AI Draft' },
  { id: 'sources', label: 'Sources' },
  { id: 'funding', label: 'Funding' },
];

export default function ContextPanel({
  userId,
  activeTab,
  open,
  sourceCount,
  children,
  triggerRef,
  onTabChange,
  onOpenChange,
}: Props) {
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const closePanel = useCallback(() => {
    onOpenChange(false);
    triggerRef.current?.focus();
  }, [onOpenChange, triggerRef]);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(`tbr-context-panel-tab-${userId}`);
      if (tabs.some(tab => tab.id === saved)) onTabChange(saved as ContextTab);
    } catch {
      // Storage may be disabled; the current session can still use the panel.
    }
  }, [userId, onTabChange]);

  useEffect(() => {
    try {
      localStorage.setItem(`tbr-context-panel-tab-${userId}`, activeTab);
    } catch {
      // Storage may be disabled; retain the selected tab in memory.
    }
  }, [userId, activeTab]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') closePanel();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open, closePanel]);

  useEffect(() => {
    if (open) tabRefs.current[tabs.findIndex(tab => tab.id === activeTab)]?.focus({ preventScroll: true });
  }, [open, activeTab]);

  const moveTabFocus = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight' && event.key !== 'Home' && event.key !== 'End') return;
    event.preventDefault();
    const currentIndex = tabs.findIndex(tab => tab.id === activeTab);
    const nextIndex = event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? tabs.length - 1
        : (currentIndex + (event.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length;
    onTabChange(tabs[nextIndex].id);
    tabRefs.current[nextIndex]?.focus();
  };

  return (
    <>
      {open && <button className="context-backdrop" type="button" aria-label="Close tools panel" onClick={closePanel} />}
      <aside className={`context-panel ${open ? 'is-open' : 'is-closed'}`} aria-label="Proposal tools" aria-hidden={!open}>
        <div className="context-panel-header">
          <strong>Proposal tools</strong>
          <button type="button" className="icon-button context-close" onClick={closePanel} aria-label="Close proposal tools">
            ×
          </button>
        </div>
        <div className="context-tabs" role="tablist" aria-label="Proposal tools">
          {tabs.map((tab, index) => (
            <button
              key={tab.id}
              ref={element => { tabRefs.current[index] = element; }}
              type="button"
              role="tab"
              id={`context-tab-${tab.id}`}
              aria-controls="context-tab-panel"
              aria-selected={activeTab === tab.id}
              tabIndex={activeTab === tab.id ? 0 : -1}
              className={`context-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => onTabChange(tab.id)}
              onKeyDown={moveTabFocus}
            >
              {tab.label}{tab.id === 'sources' ? ` (${sourceCount})` : ''}
            </button>
          ))}
        </div>
        <div
          className="context-tab-panel"
          role="tabpanel"
          id="context-tab-panel"
          aria-labelledby={`context-tab-${activeTab}`}
          tabIndex={0}
        >
          {children}
        </div>
      </aside>
    </>
  );
}
