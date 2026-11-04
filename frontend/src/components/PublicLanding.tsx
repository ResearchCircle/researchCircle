'use client';

import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent as ReactKeyboardEvent } from 'react';
import {
  ArrowRight,
  Eye,
  EyeOff,
  FileText,
  Menu,
  Network,
  Sparkles,
  Users,
  X,
} from 'lucide-react';

type AuthMode = 'login' | 'register';

type PublicLandingProps = {
  authMode: AuthMode;
  email: string;
  password: string;
  name: string;
  busy: boolean;
  error: string;
  onModeChange: (mode: AuthMode) => void;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onNameChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

const features = [
  {
    icon: Users,
    tone: 'collaborators',
    title: 'Find collaborators',
    description:
      'Describe your research idea and explore matching RIT faculty, with the evidence behind each match.',
  },
  {
    icon: Network,
    tone: 'graph',
    title: 'Explore the knowledge graph',
    description:
      'See co-authorship networks, departments, and research clusters, linked to their public sources.',
  },
  {
    icon: Sparkles,
    tone: 'drafting',
    title: 'Draft with cited AI',
    description:
      'Generate suggestions from sources you choose. Review every suggestion before it becomes part of your proposal.',
  },
  {
    icon: FileText,
    tone: 'workspace',
    title: 'Write and track grants together',
    description:
      'Co-author with your team and track proposals from first draft through submission and outcome.',
  },
];

const steps = [
  ['Find collaborators', 'Discover RIT faculty whose work connects with your research idea.'],
  ['Gather evidence', 'Explore public research records and select the sources that support your proposal.'],
  ['Draft and track', 'Write with your team, review cited suggestions, and follow grant progress.'],
];

function SiteHeader({ onModeChange }: { onModeChange: (mode: AuthMode) => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!menuOpen) return;
    const closeOnEscape = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    };
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [menuOpen]);

  const closeMenu = () => setMenuOpen(false);

  return (
    <header className="public-header">
      <div className="public-header-inner">
        <a className="public-brand" href="#top" aria-label="Tiger Research Buddy home">
          <span className="brand-mark small" aria-hidden="true">trb</span>
          <span className="public-brand-copy">
            <strong>Tiger Research Buddy</strong>
            <small>RIT Research Platform</small>
          </span>
        </a>

        <button
          ref={menuButtonRef}
          type="button"
          className="public-menu-toggle"
          aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={menuOpen}
          aria-controls="public-navigation"
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
        </button>

        <nav
          id="public-navigation"
          className={`public-navigation${menuOpen ? ' is-open' : ''}`}
          aria-label="Main navigation"
        >
          <a className="public-nav-link" href="#features" onClick={closeMenu}>Features</a>
          <a className="public-nav-link" href="#how-it-works" onClick={closeMenu}>How it works</a>
          <a
            className="public-nav-link public-sign-in"
            href="#auth"
            onClick={() => {
              onModeChange('login');
              closeMenu();
            }}
          >
            Sign in
          </a>
          <a
            className="public-button public-button-primary public-header-cta"
            href="#auth"
            onClick={() => {
              onModeChange('register');
              closeMenu();
            }}
          >
            Get started
          </a>
        </nav>
      </div>
    </header>
  );
}

function AuthCard({
  authMode,
  email,
  password,
  name,
  busy,
  error,
  onModeChange,
  onEmailChange,
  onPasswordChange,
  onNameChange,
  onSubmit,
}: PublicLandingProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [resetNotice, setResetNotice] = useState(false);
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const changeMode = (mode: AuthMode) => {
    onModeChange(mode);
    setResetNotice(false);
  };

  const onTabKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    const nextIndex = event.key === 'ArrowRight' || event.key === 'Home'
      ? (event.key === 'Home' ? 0 : 1)
      : event.key === 'ArrowLeft' || event.key === 'End'
        ? (event.key === 'End' ? 1 : 0)
        : -1;
    if (nextIndex < 0) return;
    event.preventDefault();
    tabRefs.current[nextIndex]?.focus();
    changeMode(nextIndex === 0 ? 'login' : 'register');
  };

  return (
    <section className="auth-card" id="auth" aria-labelledby="auth-heading">
      <h2 className="auth-card-heading" id="auth-heading">Your research workspace</h2>
      <div className="auth-tabs" role="tablist" aria-label="Account access" onKeyDown={onTabKeyDown}>
        <button
          ref={(element) => { tabRefs.current[0] = element; }}
          type="button"
          role="tab"
          id="sign-in-tab"
          aria-selected={authMode === 'login'}
          aria-controls="auth-form-panel"
          tabIndex={authMode === 'login' ? 0 : -1}
          className={`auth-tab${authMode === 'login' ? ' active' : ''}`}
          onClick={() => changeMode('login')}
        >
          Sign in
        </button>
        <button
          ref={(element) => { tabRefs.current[1] = element; }}
          type="button"
          role="tab"
          id="create-account-tab"
          aria-selected={authMode === 'register'}
          aria-controls="auth-form-panel"
          tabIndex={authMode === 'register' ? 0 : -1}
          className={`auth-tab${authMode === 'register' ? ' active' : ''}`}
          onClick={() => changeMode('register')}
        >
          Create account
        </button>
      </div>

      <div
        id="auth-form-panel"
        role="tabpanel"
        aria-labelledby={authMode === 'login' ? 'sign-in-tab' : 'create-account-tab'}
        className="auth-form-panel"
      >
        {error && <p className="auth-error" id="auth-error" role="alert">{error}</p>}

        <form onSubmit={onSubmit} aria-busy={busy}>
          {authMode === 'register' && (
            <label className="auth-field">
              Full name
              <input
                type="text"
                name="name"
                autoComplete="name"
                placeholder="Your name"
                value={name}
                onChange={(event) => onNameChange(event.target.value)}
                required
                maxLength={100}
              />
            </label>
          )}

          <label className="auth-field">
            Academic email
            <input
              type="email"
              name="email"
              autoComplete="email"
              placeholder="name@rit.edu"
              value={email}
              onChange={(event) => onEmailChange(event.target.value)}
              aria-describedby={error ? 'auth-error' : undefined}
              required
            />
          </label>

          <label className="auth-field">
            Password
            <span className="password-input-wrap">
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                autoComplete={authMode === 'register' ? 'new-password' : 'current-password'}
                value={password}
                onChange={(event) => onPasswordChange(event.target.value)}
                minLength={authMode === 'register' ? 12 : undefined}
                maxLength={1024}
                required
                aria-describedby={
                  authMode === 'register'
                    ? error ? 'auth-error password-hint' : 'password-hint'
                    : error ? 'auth-error' : undefined
                }
              />
              <button
                type="button"
                className="password-toggle"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                aria-pressed={showPassword}
                onClick={() => setShowPassword((shown) => !shown)}
              >
                {showPassword
                  ? <EyeOff aria-hidden="true" />
                  : <Eye aria-hidden="true" />}
              </button>
            </span>
            {authMode === 'register' && (
              <span className="auth-field-hint" id="password-hint">Use at least 12 characters.</span>
            )}
          </label>

          {authMode === 'login' && (
            <div className="auth-utility-row">
              {/* TODO: Connect this note to a password-reset route when the API supports one. */}
              <button
                type="button"
                className="auth-inline-link"
                aria-expanded={resetNotice}
                aria-controls="password-reset-note"
                onClick={() => setResetNotice((visible) => !visible)}
              >
                Forgot password?
              </button>
            </div>
          )}
          {resetNotice && (
            <p className="password-reset-note" id="password-reset-note" role="status">
              Password reset is not available yet.
            </p>
          )}

          <button className="public-button public-button-primary auth-submit" type="submit" disabled={busy}>
            {busy && <span className="auth-spinner" aria-hidden="true" />}
            <span>{busy ? 'Please wait…' : authMode === 'login' ? 'Sign in to workspace' : 'Create account'}</span>
          </button>
          <span className="sr-only" role="status" aria-live="polite">
            {busy ? 'Submitting your account details.' : ''}
          </span>
        </form>
      </div>
      <p className="auth-card-note">For RIT faculty, students, and research teams.</p>
    </section>
  );
}

export default function PublicLanding(props: PublicLandingProps) {
  return (
    <div className="public-landing" id="top">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <SiteHeader onModeChange={props.onModeChange} />

      <main id="main-content">
        <section className="public-hero" aria-labelledby="hero-title">
          <div className="public-hero-inner">
            <div className="hero-copy">
              <p className="hero-eyebrow">
                <Sparkles aria-hidden="true" />
                <span>Evidence-grounded AI for research proposals</span>
              </p>
              <h1 id="hero-title">From first research idea to funded, cited proposal.</h1>
              <p className="hero-description">
                Discover collaborators, build on public research, and draft proposals with evidence you can review.
              </p>
              <div className="hero-actions">
                <a
                  className="public-button public-button-primary"
                  href="#auth"
                  onClick={() => props.onModeChange('register')}
                >
                  Get started <ArrowRight aria-hidden="true" />
                </a>
                <a className="public-button public-button-secondary" href="#how-it-works">
                  See how it works
                </a>
              </div>
              <p className="hero-trust">Built for RIT faculty and students <span aria-hidden="true">·</span> Uses public university records</p>
            </div>
            <AuthCard {...props} />
          </div>
        </section>

        <section className="public-section public-features" id="features" aria-labelledby="features-title">
          <div className="public-section-heading">
            <p className="public-section-kicker">Research, connected</p>
            <h2 id="features-title">Everything you need to go from idea to proposal</h2>
            <p>Find people, explore evidence, and move your research forward with your team.</p>
          </div>
          <div className="public-feature-grid">
            {features.map(({ icon: Icon, tone, title, description }) => (
              <article className="public-feature-card" key={title}>
                <span className={`public-feature-icon ${tone}`}>
                  <Icon aria-hidden="true" />
                </span>
                <h3>{title}</h3>
                <p>{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="public-section public-how" id="how-it-works" aria-labelledby="how-title">
          <div className="public-section-heading">
            <p className="public-section-kicker">A clear path forward</p>
            <h2 id="how-title">How it works</h2>
          </div>
          <ol className="public-steps">
            {steps.map(([title, description], index) => (
              <li className="public-step" key={title}>
                <span className="public-step-number" aria-hidden="true">{index + 1}</span>
                <h3>{title}</h3>
                <p>{description}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="public-cta-band" aria-labelledby="cta-title">
          <div>
            <p className="public-section-kicker">Start with your next idea</p>
            <h2 id="cta-title">Ready to start your next proposal?</h2>
          </div>
          <a
            className="public-button public-button-primary"
            href="#auth"
            onClick={() => props.onModeChange('register')}
          >
            Get started <ArrowRight aria-hidden="true" />
          </a>
        </section>
      </main>

      <footer className="public-footer">
        <div className="public-footer-inner">
          <a className="public-brand" href="#top" aria-label="Tiger Research Buddy home">
            <span className="brand-mark small" aria-hidden="true">trb</span>
            <span className="public-brand-copy">
              <strong>Tiger Research Buddy</strong>
              <small>Research with evidence. Build together.</small>
            </span>
          </a>
          <nav className="public-footer-links" aria-label="Footer navigation">
            <a href="#features">Features</a>
            <a href="#how-it-works">How it works</a>
            <a href="#auth" onClick={() => props.onModeChange('login')}>Sign in</a>
          </nav>
          <p>© 2026 Tiger Research Buddy · ResearchCircle · RIT Research Platform</p>
        </div>
      </footer>
    </div>
  );
}
