'use client';

import { useEffect, useCallback, useMemo, useState, type ReactNode } from "react"

type View = "home" | "campus" | "vault" | "pod" | "proof"
const mainNavKeys: View[] = ["home", "vault", "pod", "proof"]
type Overlay = "reveal" | "verify" | "graph" | "funding" | "project" | "peer-review" | "conflict" | "export" | "reasoning"
type IconName = "arrow" | "bell" | "book" | "brain" | "check" | "chevron" | "clock" | "close" | "code" | "copy" | "download" | "expand" | "eye" | "filter" | "fingerprint" | "graph" | "home" | "lock" | "message" | "more" | "pin" | "plus" | "search" | "seal" | "send" | "shield" | "spark" | "user" | "users" | "verified"

const iconPaths: Record<IconName, ReactNode> = {
  arrow: (
    <>
      <path d="M5 12h14M14 7l5 5-5 5" />
    </>
  ),
  bell: (
    <>
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
      <path d="M10 21h4" />
    </>
  ),
  book: (
    <>
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V4H6.5A2.5 2.5 0 0 0 4 6.5v13Z" />
      <path d="M8 7h8M8 11h6" />
    </>
  ),
  brain: (
    <>
      <path d="M9.5 4.5A3 3 0 0 0 4 6a3 3 0 0 0 .5 5.5A3.5 3.5 0 0 0 9 17v2a2 2 0 0 0 4 0v-2a3.5 3.5 0 0 0 4.5-5.5A3 3 0 0 0 18 6a3 3 0 0 0-5.5-1.5" />
      <path d="M9 8c2 0 2-2 2-4M15 9c-2 0-2-2-2-4M8 13c2 0 3 1 3 3M16 13c-2 0-3 1-3 3" />
    </>
  ),
  check: <path d="m5 12 4 4L19 6" />,
  chevron: <path d="m9 18 6-6-6-6" />,
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  close: <path d="M6 6l12 12M18 6 6 18" />,
  code: (
    <>
      <path d="m8 9-3 3 3 3M16 9l3 3-3 3M14 5l-4 14" />
    </>
  ),
  copy: (
    <>
      <rect x="8" y="8" width="11" height="11" rx="2" />
      <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
    </>
  ),
  download: (
    <>
      <path d="M12 3v12m0 0 4-4m-4 4-4-4" />
      <path d="M5 20h14" />
    </>
  ),
  expand: (
    <>
      <path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5" />
    </>
  ),
  eye: (
    <>
      <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" />
      <circle cx="12" cy="12" r="2.5" />
    </>
  ),
  filter: (
    <>
      <path d="M4 6h16M7 12h10M10 18h4" />
    </>
  ),
  fingerprint: (
    <>
      <path d="M7 9a5 5 0 0 1 10 0v3M5 12V9a7 7 0 0 1 14 0v5M8 13v-3a4 4 0 0 1 8 0v5M11 12v3a7 7 0 0 1-2 5M14 12v4a9 9 0 0 1-1 4M17 18l-1 2" />
    </>
  ),
  graph: (
    <>
      <circle cx="5" cy="15" r="2" />
      <circle cx="12" cy="5" r="2" />
      <circle cx="19" cy="14" r="2" />
      <path d="m6 13 5-6m2 0 5 5M7 15h10" />
    </>
  ),
  home: (
    <>
      <path d="m3 11 9-8 9 8" />
      <path d="M5 10v10h14V10M9 20v-6h6v6" />
    </>
  ),
  lock: (
    <>
      <rect x="4" y="10" width="16" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </>
  ),
  message: (
    <path d="M20 15a3 3 0 0 1-3 3H8l-4 3V7a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v8Z" />
  ),
  more: (
    <>
      <circle cx="5" cy="12" r="1" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
      <circle cx="19" cy="12" r="1" fill="currentColor" stroke="none" />
    </>
  ),
  pin: (
    <>
      <path d="M12 17v5M5 17h14" />
      <path d="m8 4-1 8h10l-1-8H8Z" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </>
  ),
  seal: (
    <>
      <path d="M12 2 9.5 4 6 3.5 5 7l-3 2 1.5 3L2 15l3 2 1 3.5 3.5-.5 2.5 2 2.5-2 3.5.5 1-3.5 3-2-1.5-3L22 9l-3-2-1-3.5-3.5.5L12 2Z" />
      <path d="m8.5 12 2.2 2.2 4.8-5" />
    </>
  ),
  send: (
    <>
      <path d="m3 3 18 9-18 9 3-9-3-9Z" />
      <path d="M6 12h15" />
    </>
  ),
  shield: (
    <>
      <path d="M12 3 4 6v5c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V6l-8-3Z" />
      <path d="m9 12 2 2 4-5" />
    </>
  ),
  spark: (
    <path d="m12 2 1.4 5.6L19 9l-5.6 1.4L12 16l-1.4-5.6L5 9l5.6-1.4L12 2ZM19 16l.7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7L19 16Z" />
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </>
  ),
  users: (
    <>
      <circle cx="9" cy="8" r="3" />
      <path d="M3 19a6 6 0 0 1 12 0" />
      <path d="M16 5a3 3 0 0 1 0 6M17 14a5 5 0 0 1 4 5" />
    </>
  ),
  verified: (
    <>
      <path d="m12 2 2.2 2.1 3-.4.5 3 2.3 2-.9 2.9.9 2.9-2.3 2-.5 3-3-.4L12 22l-2.2-2.1-3 .4-.5-3-2.3-2 .9-2.9L4 8.5l2.3-2 .5-3 3 .4L12 2Z" />
      <path d="m8.5 12 2.2 2.2 4.8-5" />
    </>
  ),
}

function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {iconPaths[name]}
    </svg>
  )
}

function NexusLogo() {
  return (
    <svg
      className="nexus-logo"
      viewBox="0 0 160 36"
      role="img"
      aria-label="Nexus"
    >
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M5 29V7l21 22V7h11" />
        <path d="M52 7H37v22h17M37 18h13" />
        <path d="m61 7 22 22M83 7 61 29" />
        <path d="M91 7v14c0 5.4 3.7 8 10 8s10-2.6 10-8V7" />
        <path d="M143 9c-3-2.8-6.8-4-10.7-3.5-5 .6-8.6 3.1-8.4 6.6.5 7.7 18.3 2.3 18.8 10.1.3 4.5-4 7.3-9.7 7.3-4.2 0-8.1-1.5-11-4.4" />
      </g>
      <g fill="#0a66c2" stroke="#fff" strokeWidth="1.4">
        <circle cx="5" cy="7" r="3.6" />
        <circle cx="26" cy="29" r="3.6" />
        <circle cx="37" cy="7" r="3.4" />
        <circle cx="50" cy="18" r="3.1" />
        <circle cx="72" cy="18" r="4.2" />
        <circle cx="91" cy="7" r="3.4" />
        <circle cx="101" cy="29" r="3.8" />
        <circle cx="111" cy="7" r="3.4" />
        <circle cx="133" cy="18" r="3.8" />
        <circle cx="143" cy="9" r="3.2" />
      </g>
      <path
        d="M26 29 37 18M83 29l8-8M111 21l12-9"
        fill="none"
        stroke="#0a66c2"
        strokeWidth="1.4"
        strokeDasharray="2.5 3"
        strokeLinecap="round"
        opacity=".75"
      />
    </svg>
  )
}

function Avatar({
  initials,
  color = "teal",
  active = false,
}: {
  initials: string
  color?: string
  active?: boolean
}) {
  return (
    <span className={`avatar avatar-${color} ${active ? "is-active" : ""}`}>
      {initials}
    </span>
  )
}

function Tag({
  children,
  tone = "neutral",
}: {
  children: ReactNode
  tone?: string
}) {
  return <span className={`tag tag-${tone}`}>{children}</span>
}

const viewMeta: Record<"home" | "vault" | "pod" | "proof", {
  label: string
  icon: IconName
  subtitle: string
}> = {
  home: {
    label: "Home",
    icon: "home",
    subtitle: "Your research feed",
  },
  vault: {
    label: "Vault",
    icon: "shield",
    subtitle: "Prove and share safely",
  },
  pod: {
    label: "Pod",
    icon: "users",
    subtitle: "Move the work forward",
  },
  proof: {
    label: "Proposal",
    icon: "book",
    subtitle: "Write with verified sources",
  },
}

function AppFrame({
  view,
  setView,
  children,
  onTelemetry,
  openOverlay,
}: {
  view: View
  setView: (view: View) => void
  children: ReactNode
  onTelemetry: () => void
  openOverlay: (overlay: Overlay) => void
}) {
  const [toolsOpen, setToolsOpen] = useState(false)
  return (
    <div className="app-shell">
      <header className="global-header">
        <button
          className="wordmark"
          onClick={() => setView("home")}
          aria-label="Nexus home"
        >
          <NexusLogo />
        </button>
        <label className="global-search">
          <Icon name="search" size={17} />
          <input
            placeholder="Search people, projects, papers, or skills"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                openOverlay("graph")
              }
            }}
          />
        </label>
        <nav className="continuum" aria-label="Research continuum">
          {mainNavKeys.map((key) => (
            <button
              key={key}
              className={view === key || (key === "home" && view === "campus") ? "active" : ""}
              onClick={() => setView(key)}
            >
              <span className="continuum-icon">
                <Icon name={viewMeta[key as keyof typeof viewMeta].icon} size={16} />
              </span>
              <span className="continuum-copy">
                <b>{viewMeta[key as keyof typeof viewMeta].label}</b>
              </span>
            </button>
          ))}
        </nav>
        <div className="header-actions">
          <div className="tools-anchor">
            <button
              className={`header-nav-button ${toolsOpen ? "active" : ""}`}
              onClick={() => setToolsOpen(!toolsOpen)}
            >
              <Icon name="graph" size={18} />
              <span>Tools</span>
            </button>
            {toolsOpen && (
              <div className="tools-menu">
                <div>
                  <strong>Research tools</strong>
                  <small>Open a focused workspace when you need it.</small>
                </div>
                <button
                  onClick={() => {
                    setView("campus")
                    setToolsOpen(false)
                  }}
                >
                  <span className="tool-menu-icon blue">
                    <Icon name="users" />
                  </span>
                  <span>
                    <b>Find collaborators</b>
                    <small>People matched to your research needs</small>
                  </span>
                </button>
                <button
                  onClick={() => {
                    setView("proof")
                    setToolsOpen(false)
                  }}
                >
                  <span className="tool-menu-icon green">
                    <Icon name="book" />
                  </span>
                  <span>
                    <b>Literature search</b>
                    <small>Search and inspect verified papers</small>
                  </span>
                </button>
                <button
                  onClick={() => {
                    openOverlay("graph")
                    setToolsOpen(false)
                  }}
                >
                  <span className="tool-menu-icon violet">
                    <Icon name="graph" />
                  </span>
                  <span>
                    <b>Knowledge graph</b>
                    <small>Explore topics, authors, and research gaps</small>
                  </span>
                </button>
                <button
                  onClick={() => {
                    onTelemetry()
                    setToolsOpen(false)
                  }}
                >
                  <span className="tool-menu-icon gold">
                    <Icon name="message" />
                  </span>
                  <span>
                    <b>Ask the literature</b>
                    <small>Get answers grounded in your library</small>
                  </span>
                </button>
                <button
                  onClick={() => {
                    openOverlay("funding")
                    setToolsOpen(false)
                  }}
                >
                  <span className="tool-menu-icon teal">
                    <Icon name="pin" />
                  </span>
                  <span>
                    <b>Funding finder</b>
                    <small>Find grants that fit your work</small>
                  </span>
                </button>
              </div>
            )}
          </div>
          <button className="header-nav-button" onClick={onTelemetry}>
            <Icon name="message" size={18} />
            <span>Messages</span>
          </button>
          <button
            className="header-nav-button notification"
            aria-label="Notifications"
            onClick={() => alert("Alerts:\n• 3 new citations verified in Neural Commons pod\n• Jordan Lee accepted your private match request\n• NIH R21 deadline in 64 days")}
          >
            <Icon name="bell" />
            <i />
            <span>Alerts</span>
          </button>
          <button
            className="me-button"
            onClick={() => alert("Aria Malik (Logged in)\nMS Computer Science, UC Berkeley\nStatus: 3 protected ideas in Vault, 1 active Pod")}
          >
            <Avatar initials="AM" color="gold" active />
            <span>Me</span>
            <Icon name="chevron" size={11} />
          </button>
        </div>
      </header>
      <main>{children}</main>
    </div>
  )
}

function MetricRing({
  value,
  label,
  tone = "teal",
  size = 84,
}: {
  value: number
  label: string
  tone?: string
  size?: number
}) {
  return (
    <div
      className="metric-ring"
      style={
        {
          "--value": `${value * 3.6}deg`,
          "--ring": `var(--${tone})`,
          width: size,
          height: size,
        } as React.CSSProperties
      }
    >
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  )
}

const papers = [
  {
    title: "Federated Foundation Models for Privacy-Preserving Neural Decoding",
    authors: "Zhang et al. · Nature Machine Intelligence",
    score: 96,
    verdict: "Supports",
    person: "MK",
    color: "blue",
  },
  {
    title: "Cross-Subject EEG Alignment via Optimal Transport",
    authors: "Li, Verma et al. · NeurIPS 2024",
    score: 91,
    verdict: "Methodology",
    person: "JL",
    color: "violet",
  },
  {
    title: "The Privacy Cost of Brain–Computer Interfaces",
    authors: "Rao et al. · ACM FAccT 2023",
    score: 88,
    verdict: "Contradicts",
    person: "AM",
    color: "gold",
  },
]

function PodView({
  setView,
  openOverlay,
  onTelemetry,
}: {
  setView: (view: View) => void
  openOverlay: (overlay: Overlay) => void
  onTelemetry?: () => void
}) {
  const [activeMilestone, setActiveMilestone] = useState(2)
  const [paperTab, setPaperTab] = useState<"evidence" | "discussion">(
    "evidence",
  )
  const [pinned, setPinned] = useState(2)
  const [activeGrant, setActiveGrant] = useState("NSF Smart & Connected Communities")
  const [discussions, setDiscussions] = useState([
    {
      initials: "JL",
      color: "blue",
      author: "Jon Lee",
      text: "Should the privacy bound be the primary contribution, or supporting infrastructure?",
      time: "8 min",
    },
    {
      initials: "SR",
      color: "teal",
      author: "Prof. Rao",
      text: "Primary. Tie it directly to Aim 2 and cite Zhang’s cross-site result.",
      time: "3 min",
    },
  ])
  const [replyText, setReplyText] = useState("")

  const sendReply = () => {
    if (!replyText.trim()) return
    setDiscussions((prev) => [
      ...prev,
      {
        initials: "AM",
        color: "gold",
        author: "Aria Malik",
        text: replyText.trim(),
        time: "Just now",
      },
    ])
    setReplyText("")
  }
  return (
    <div className="view pod-view">
      <section className="pod-identity">
        <div>
          <div className="eyebrow">
            <span className="live-dot" /> NEURAL COMMONS · 4 MEMBERS
          </div>
          <h1>Good morning, Aria.</h1>
          <p>
            Your pod is moving toward the internal methods review on Friday.
          </p>
        </div>
        <div className="pod-people">
          <div className="facepile">
            <Avatar initials="AM" color="gold" active />
            <Avatar initials="JL" color="blue" active />
            <Avatar initials="MK" color="violet" active />
            <Avatar initials="SR" color="teal" />
          </div>
          <div className="presence-copy">
            <strong>3 teammates here</strong>
            <span>Jon and Maya are editing</span>
          </div>
          <button className="icon-button" onClick={onTelemetry} title="Pod discussion">
            <Icon name="message" />
          </button>
          <button
            className="dark-button"
            onClick={() => {
              navigator.clipboard?.writeText("https://nexus.research/pod/neural-commons/invite")
              alert("Invite link copied to clipboard: https://nexus.research/pod/neural-commons/invite")
            }}
          >
            <Icon name="users" /> Add teammate
          </button>
        </div>
      </section>

      <section className="today-focus">
        <span className="focus-check">
          <Icon name="verified" size={22} />
        </span>
        <div className="focus-copy">
          <span>YOUR NEXT MOVE</span>
          <h2>Review 5 claims before Friday’s methods check.</h2>
          <p>
            Nexus found the source passages. Confirm the matches and your
            readiness score will move to 80%.
          </p>
        </div>
        <div className="focus-meta">
          <span>
            <b>12 min</b> estimated
          </span>
          <span>
            <b>5</b> claims
          </span>
        </div>
        <button className="accent-button" onClick={() => setView("proof")}>
          Review claims <Icon name="arrow" />
        </button>
        <button
          className="focus-audit-button"
          onClick={() => openOverlay("peer-review")}
        >
          Run pre-flight audit
        </button>
      </section>

      <section className="milestone-band">
        <div className="milestone-heading">
          <span>GRANT PROGRESS</span>
          <button
            onClick={() =>
              setActiveGrant(
                activeGrant === "NSF Smart & Connected Communities"
                  ? "NIH R21 Exploratory Research"
                  : "NSF Smart & Connected Communities",
              )
            }
          >
            {activeGrant} <Icon name="chevron" size={14} />
          </button>
        </div>
        <div className="milestone-content">
          <div className="flightpath">
            {[
              "Literature discovery",
              "Evidence assembly",
              "Collaborative drafting",
              "Peer review",
              "Final submission",
            ].map((item, i) => (
              <button
                key={item}
                className={`${i < activeMilestone ? "complete" : ""} ${
                  i === activeMilestone ? "current" : ""
                }`}
                onClick={() => setActiveMilestone(i)}
              >
                <span>
                  {i < activeMilestone ? (
                    <Icon name="check" size={14} />
                  ) : (
                    `0${i + 1}`
                  )}
                </span>
                <b>{item}</b>
                <small>
                  {i < activeMilestone
                    ? "Complete"
                    : i === activeMilestone
                      ? "7 of 12 tasks"
                      : i === 3
                        ? "Due Oct 18"
                        : "Not started"}
                </small>
              </button>
            ))}
          </div>
          <div className="readiness">
            <MetricRing value={72} label="READY" />
            <div>
              <strong>Proposal readiness</strong>
              <span>+8 this week</span>
            </div>
          </div>
        </div>
      </section>

      <section className="pod-grid">
        <div className="evidence-panel panel">
          <div className="panel-header">
            <div>
              <div className="switcher">
                <button
                  className={paperTab === "evidence" ? "active" : ""}
                  onClick={() => setPaperTab("evidence")}
                >
                  Evidence board <span>18</span>
                </button>
                <button
                  className={paperTab === "discussion" ? "active" : ""}
                  onClick={() => setPaperTab("discussion")}
                >
                  Discussion <span>6</span>
                </button>
              </div>
              <p>
                {paperTab === "evidence"
                  ? "The sources your team trusts enough to write from."
                  : "Open questions and decisions that need the team."}
              </p>
            </div>
            <div className="panel-tools">
              <button className="icon-button" onClick={() => setPaperTab("evidence")}>
                <Icon name="search" />
              </button>
              <button className="soft-button" onClick={() => openOverlay("project")}>
                <Icon name="plus" /> Add a paper
              </button>
            </div>
          </div>
          {paperTab === "evidence" ? (
            <div className="paper-list">
              {papers.map((paper, i) => (
                <article className="paper-row" key={paper.title}>
                  <div className="paper-score" style={{ ["--score" as any]: paper.score }}>
                    <span>{paper.score}</span>
                    <small>%</small>
                  </div>
                  <div className="paper-copy">
                    <div className="paper-tags">
                      <Tag tone={paper.verdict.toLowerCase()}>
                        {paper.verdict}
                      </Tag>
                      <span>FOUNDATIONAL</span>
                    </div>
                    <h3>{paper.title}</h3>
                    <p>{paper.authors}</p>
                    <div className="paper-meta">
                      <Avatar initials={paper.person} color={paper.color} />
                      <span>
                        Added by{" "}
                        {paper.person === "MK"
                          ? "Maya"
                          : paper.person === "JL"
                            ? "Jon"
                            : "you"}
                      </span>
                      <span>·</span>
                      <span>{i + 2} endorsements</span>
                    </div>
                  </div>
                  <button
                    className={`pin-button ${i < pinned ? "pinned" : ""}`}
                    onClick={() =>
                      paper.verdict === "Contradicts"
                        ? openOverlay("conflict")
                        : setPinned(i < pinned ? i : i + 1)
                    }
                  >
                    <Icon
                      name={paper.verdict === "Contradicts" ? "eye" : "pin"}
                    />{" "}
                    {paper.verdict === "Contradicts"
                      ? "Compare evidence"
                      : i < pinned
                        ? "Pinned to §2.1"
                        : "Pin citation"}
                  </button>
                  <button className="icon-button">
                    <Icon name="more" />
                  </button>
                </article>
              ))}
              <button className="text-button full">
                View all 18 sources <Icon name="arrow" />
              </button>
            </div>
          ) : (
            <div className="discussion-list">
              {discussions.map((d, index) => (
                <div key={index}>
                  <Avatar initials={d.initials} color={d.color} />
                  <p>
                    <strong>{d.author}</strong> {d.text}
                  </p>
                  <time>{d.time}</time>
                </div>
              ))}
              <div className="reply-box">
                <input
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendReply()}
                  placeholder="Write a reply to the pod…"
                  style={{
                    border: "none",
                    background: "transparent",
                    outline: "none",
                    flex: 1,
                    color: "var(--ink)",
                    fontSize: 12,
                  }}
                />
                <button onClick={sendReply} title="Send reply">
                  <Icon name="send" />
                </button>
              </div>
            </div>
          )}
        </div>

        <aside className="activity-panel panel">
          <div className="panel-header compact">
            <div>
              <span className="section-kicker">LIVE PULSE</span>
              <h2>Pod activity</h2>
            </div>
            <button className="icon-button">
              <Icon name="filter" />
            </button>
          </div>
          <div className="activity-list">
            <div>
              <span className="activity-icon green">
                <Icon name="check" />
              </span>
              <p>
                <b>Maya</b> verified a citation in{" "}
                <strong>Methodology §2.1</strong>
                <small>2 min ago</small>
              </p>
            </div>
            <div>
              <span className="activity-icon violet">
                <Icon name="spark" />
              </span>
              <p>
                <b>muse-wonder</b> drafted three variants for{" "}
                <strong>Broader Impacts</strong>
                <small>8 min ago</small>
              </p>
            </div>
            <div>
              <span className="activity-icon blue">
                <Icon name="book" />
              </span>
              <p>
                <b>Jon</b> added <strong>Cross-Subject EEG Alignment</strong>
                <small>16 min ago</small>
              </p>
            </div>
            <div>
              <span className="activity-icon gold">
                <Icon name="message" />
              </span>
              <p>
                <b>Prof. Rao</b> left feedback on Aim 2<small>31 min ago</small>
              </p>
            </div>
          </div>
          <div className="deadline-card">
            <div>
              <span>NEXT DEADLINE</span>
              <strong>Internal methods review</strong>
              <small>Friday, Oct 11 · 4:00 PM</small>
            </div>
            <b>
              2d
              <br />
              <small>04h</small>
            </b>
          </div>
        </aside>

        <div className="studio-launch panel">
          <div className="studio-visual">
            <div className="document-mini">
              <span>2.1 TECHNICAL APPROACH</span>
              <i />
              <i />
              <i className="short" />
              <mark>
                Cross-site decoding retains 94.2% accuracy<sup>12</sup>
              </mark>
              <i />
              <i className="medium" />
            </div>
            <div className="verification-float">
              <Icon name="verified" />
              <span>
                <b>Claim grounded</b>Figure 4b · p. 8
              </span>
            </div>
          </div>
          <div className="studio-copy">
            <span className="section-kicker">PROPOSAL</span>
            <h2>Write the proposal. Keep every claim connected to proof.</h2>
            <p>
              Jon and Maya are in the draft now. Nexus keeps each claim linked
              to the exact passage, figure, or equation that supports it.
            </p>
            <div>
              <Tag tone="verification">
                <Icon name="shield" size={13} /> 100% citation audit
              </Tag>
              <Tag tone="neutral">2,941 papers indexed</Tag>
            </div>
            <button className="accent-button" onClick={() => setView("proof")}>
              Continue writing <Icon name="arrow" />
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}

function VaultView({
  openOverlay,
}: {
  openOverlay: (overlay: Overlay) => void
}) {
  const [step, setStep] = useState<"compose" | "hashing" | "sealed">("compose")
  const [audience, setAudience] =
    useState<"Stranger" | "Peer student" | "Professor">("Stranger")
  const [text, setText] = useState(
    "A federated adaptation layer can align latent neural representations across institutions without centralizing subject-level EEG data.",
  )
  const seal = () => {
    setStep("hashing")
    window.setTimeout(() => setStep("sealed"), 1400)
  }

  const downloadCertificate = () => {
    const cert = {
      certificateId: "NX-8492",
      owner: "Aria Malik",
      affiliation: "UC Berkeley",
      timestamp: "2025-10-09T14:32:18Z",
      merkleRoot: "0x774ab92d18fc4e8932bce10871982aef12d094",
      algorithm: "SHA-256 / Ed25519",
      status: "VERIFIED_ON_CHAIN",
      hypothesisSummary: text,
      rawContentDisclosure: "DEVICE_ONLY_PRIVATE",
    }
    const blob = new Blob([JSON.stringify(cert, null, 2)], {
      type: "application/json",
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "nexus_proof_of_priority_NX-8492.json"
    a.click()
    URL.revokeObjectURL(url)
  }
  return (
    <div className="view vault-view">
      <section className="vault-intro">
        <div>
          <div className="eyebrow">
            <Icon name="lock" size={14} /> PRIVATE UNTIL YOU CHOOSE TO SHARE
          </div>
          <h1>
            Prove you had the idea
            <br />
            <em>without revealing it.</em>
          </h1>
          <p>
            Create a timestamped proof on this device. Then publish a safe
            summary that reveals only what collaborators need to know.
          </p>
        </div>
        <div className="trust-diagram">
          <div className="active">
            <Icon name="fingerprint" />
            <b>Prove</b>
            <span>Create a private record</span>
          </div>
          <i />
          <div>
            <Icon name="eye" />
            <b>Share safely</b>
            <span>Publish a summary</span>
          </div>
          <i />
          <div>
            <Icon name="users" />
            <b>Connect</b>
            <span>Reveal when both agree</span>
          </div>
        </div>
      </section>
      <section className="vault-workbench">
        <div className="vault-editor panel">
          <div className="panel-header">
            <div>
              <span className="section-kicker">ONLY YOU CAN SEE THIS</span>
              <h2>Write the idea you want to protect</h2>
            </div>
            <Tag tone="verification">
              <Icon name="shield" size={13} /> Stays on this device
            </Tag>
          </div>
          <div className="hypothesis-box">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={step !== "compose"}
              aria-label="Private hypothesis"
            />
            <div>
              <span>{text.length} characters</span>
              <span>
                <Icon name="lock" size={12} /> Never transmitted
              </span>
            </div>
          </div>
          <div className={`hash-console ${step}`}>
            {step === "compose" && (
              <>
                <div className="hash-orb">
                  <Icon name="fingerprint" size={30} />
                </div>
                <div>
                  <strong>Your idea is ready to protect</strong>
                  <span>No text will leave this device</span>
                </div>
                <button className="accent-button" onClick={seal}>
                  Create priority proof <Icon name="arrow" />
                </button>
              </>
            )}
            {step === "hashing" && (
              <>
                <div className="hash-orb spinning">
                  <Icon name="fingerprint" size={30} />
                </div>
                <div>
                  <strong>Creating your private proof…</strong>
                  <span>
                    Mixing entropy <code>9f:2a:7c:01</code>
                  </span>
                </div>
                <div className="hash-progress">
                  <i />
                </div>
              </>
            )}
            {step === "sealed" && (
              <>
                <div className="hash-orb complete">
                  <Icon name="check" size={30} />
                </div>
                <div>
                  <strong>Your priority is recorded</strong>
                  <span>Certificate #NX-8492 is ready</span>
                </div>
                <button className="soft-button" onClick={downloadCertificate}>
                  <Icon name="download" /> Certificate
                </button>
              </>
            )}
          </div>
          <div className="technical-foot">
            <span>
              <Icon name="code" /> CLIENT LOG
            </span>
            <code>
              {step === "sealed"
                ? "sha256:b3e1c8f47a...91d2 · merkle:0x774a...18fc"
                : "Awaiting local cryptographic operation_"}
            </code>
          </div>
        </div>
        <aside
          className={`certificate panel ${step === "sealed" ? "issued" : ""}`}
        >
          <div className="certificate-seal">
            <Icon name="seal" size={40} />
          </div>
          <span>OFFICIAL NEXUS RECORD</span>
          <h2>Proof of Priority</h2>
          <p>
            This certificate verifies that an undisclosed research artifact
            existed at the time below.
          </p>
          <div className="certificate-id">
            <small>CERTIFICATE</small>
            <strong>{step === "sealed" ? "#NX-8492" : "#NX-••••"}</strong>
          </div>
          <dl>
            <div>
              <dt>Owner</dt>
              <dd>Aria Malik</dd>
            </div>
            <div>
              <dt>Timestamp</dt>
              <dd>
                {step === "sealed"
                  ? "09 Oct 2025 · 14:32:18 UTC"
                  : "Pending seal"}
              </dd>
            </div>
            <div>
              <dt>Merkle root</dt>
              <dd>{step === "sealed" ? "0x774a…18fc" : "—"}</dd>
            </div>
            <div>
              <dt>Raw content</dt>
              <dd>Not disclosed</dd>
            </div>
          </dl>
          <button
            className="certificate-footer"
            onClick={() => openOverlay("verify")}
          >
            <Icon name="verified" />
            <span>
              Publicly verifiable
              <br />
              <b>Open verification page</b>
            </span>
            <Icon name="arrow" size={14} />
          </button>
        </aside>
      </section>
      <section className="teaser-studio panel">
        <div className="teaser-copy">
          <span className="section-kicker">SAFE PUBLIC SUMMARY</span>
          <h2>Share the opportunity, not the secret.</h2>
          <p>
            Nexus drafted a summary that explains what you can offer and what
            help you need. Sensitive details stay out, and nothing posts until
            you approve it.
          </p>
          <div className="redaction-row">
            <span>Kept private</span>
            <Tag tone="danger">Exact architecture</Tag>
            <Tag tone="danger">Dataset identity</Tag>
            <Tag tone="danger">94.2% benchmark</Tag>
          </div>
        </div>
        <div className="audience-preview">
          <div className="preview-toolbar">
            <span>PREVIEW AS</span>
            <div>
              {(["Stranger", "Peer student", "Professor"] as const).map((a) => (
                <button
                  className={audience === a ? "active" : ""}
                  onClick={() => setAudience(a)}
                  key={a}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>
          <article className="project-preview">
            <div className="preview-head">
              <span className="project-glyph">
                <Icon name="brain" />
              </span>
              <div>
                <Tag tone="stage">HYPOTHESIS</Tag>
                <small>EECS × Neuroscience</small>
              </div>
              <button className="icon-button">
                <Icon name="more" />
              </button>
            </div>
            <h3>Privacy-preserving neural representation alignment</h3>
            <p>
              {audience === "Professor"
                ? "Exploring institution-safe latent alignment for cross-site neural decoding, with a formal privacy boundary and preliminary validation."
                : "Exploring privacy-safe methods that help neural decoding models learn across institutions without moving sensitive data."}
            </p>
            <div className="offer-need">
              <span>OFFERS</span>
              <Tag tone="offer">Federated learning</Tag>
              <Tag tone="offer">Privacy bounds</Tag>
            </div>
            <div className="offer-need">
              <span>NEEDS</span>
              <Tag tone="need">Clinical EEG access</Tag>
              <Tag tone="need">IRB guidance</Tag>
            </div>
            <div className="blurred-owner">
              <Icon name="lock" />
              <span>
                <b>Your identity stays hidden</b>Reveals only when both people
                agree
              </span>
              <button onClick={() => openOverlay("reveal")}>Request a private match</button>
            </div>
          </article>
        </div>
      </section>
    </div>
  )
}

const projects = [
  {
    stage: "PROTOTYPE",
    dept: "EECS × Public Health",
    title: "Federated diagnostics for rural health networks",
    body: "Training robust clinical classifiers across bandwidth-limited sites without centralizing patient records.",
    offer: ["Secure aggregation", "Edge ML"],
    need: ["Clinical validation"],
    color: "cyan",
    degree: "PhD",
  },
  {
    stage: "EXPERIMENT",
    dept: "Robotics × Conservation",
    title: "Soft aerial sensors for forest canopy health",
    body: "A biodegradable micro-drone swarm measuring tree stress above inaccessible terrain.",
    offer: ["Soft robotics", "SLAM"],
    need: ["Plant pathology"],
    color: "lime",
    degree: "MS",
  },
  {
    stage: "HYPOTHESIS",
    dept: "Neuroscience × Statistics",
    title: "Invariant signatures of cognitive fatigue",
    body: "Testing whether cross-subject latent structure predicts fatigue before behavioral decline.",
    offer: ["EEG corpus", "Bayesian models"],
    need: ["Representation learning"],
    color: "violet",
    degree: "PhD",
  },
  {
    stage: "WRITING",
    dept: "Energy × Materials",
    title: "Self-healing electrolytes under extreme cycling",
    body: "A polymer system that recovers ion transport after dendrite-induced microfractures.",
    offer: ["Electrochemistry"],
    need: ["X-ray tomography"],
    color: "orange",
    degree: "Lab",
  },
]

function CampusView({
  setView,
  openOverlay,
}: {
  setView: (view: View) => void
  openOverlay: (overlay: Overlay) => void
}) {
  const [accepted, setAccepted] = useState(false)
  const [query, setQuery] = useState("")
  const [activePill, setActivePill] = useState("All campus")
  const filtered = projects.filter((p) => {
    const matchesQuery = (p.title + p.body + p.dept)
      .toLowerCase()
      .includes(query.toLowerCase())
    if (activePill === "All campus") return matchesQuery
    if (activePill === "EECS") return matchesQuery && p.dept.includes("EECS")
    if (activePill === "Neuroscience")
      return matchesQuery && p.dept.includes("Neuroscience")
    if (activePill === "Prototype")
      return matchesQuery && p.stage.toUpperCase() === "PROTOTYPE"
    return matchesQuery
  })
  return (
    <div className="view campus-view">
      <div style={{ marginBottom: 16 }}>
        <button
          className="text-button"
          onClick={() => setView("home")}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontWeight: 600,
            fontSize: 13,
          }}
        >
          <Icon name="arrow" /> Back to Research Feed
        </button>
      </div>
      <section className="campus-hero">
        <div className="campus-title">
          <div className="eyebrow">
            <span className="live-dot" /> 1,284 ACTIVE PROJECTS AT BERKELEY
          </div>
          <h1>
            Find the people and projects
            <br />
            <em>that move your work forward.</em>
          </h1>
          <p>
            Search work happening now—not just what was published last year.
          </p>
        </div>
        <div className="campus-profile">
          <Avatar initials="AM" color="gold" active />
          <div>
            <span>YOUR MATCH PROFILE</span>
            <strong>Aria Malik · MSCS</strong>
            <small>Representation learning · Federated systems · EEG</small>
          </div>
          <button>
            <Icon name="expand" />
          </button>
        </div>
      </section>
      <section className="discovery-controls">
        <div className="search-field">
          <Icon name="search" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Try “EEG datasets”, “robotics collaborator”, or “NIH R21”…"
          />
          <kbd>⌘ K</kbd>
        </div>
        {["All campus", "EECS", "Neuroscience", "Prototype"].map((pill) => (
          <button
            key={pill}
            className={`filter-pill ${activePill === pill ? "active" : ""}`}
            onClick={() => setActivePill(pill)}
          >
            {pill} {pill === "All campus" && <span>1,284</span>}
          </button>
        ))}
        <button
          className="filter-pill"
          onClick={() => openOverlay("graph")}
        >
          <Icon name="filter" /> Refine
        </button>
      </section>
      <section className="campus-layout">
        <div className="feed">
          <div className="feed-heading">
            <div>
              <span className="section-kicker">RECOMMENDED FOR YOU</span>
              <h2>Work that complements yours</h2>
            </div>
            <button>
              Best match first <Icon name="chevron" size={14} />
            </button>
          </div>
          <div className="project-grid">
            {filtered.map((project, i) => (
              <article className="project-card" key={project.title}>
                <div className={`project-art art-${project.color}`}>
                  <span>{String(i + 1).padStart(2, "0")}</span>
                  <Icon
                    name={
                      i === 0
                        ? "shield"
                        : i === 1
                          ? "spark"
                          : i === 2
                            ? "brain"
                            : "graph"
                    }
                    size={42}
                  />
                </div>
                <div className="project-card-body">
                  <div>
                    <Tag tone="stage">{project.stage}</Tag>
                    <span className="degree">{project.degree}</span>
                  </div>
                  <small>{project.dept}</small>
                  <h3>{project.title}</h3>
                  <p>{project.body}</p>
                  <div className="offer-need">
                    <span>OFFERS</span>
                    {project.offer.map((x) => (
                      <Tag tone="offer" key={x}>
                        {x}
                      </Tag>
                    ))}
                  </div>
                  <div className="offer-need">
                    <span>NEEDS</span>
                    {project.need.map((x) => (
                      <Tag tone="need" key={x}>
                        {x}
                      </Tag>
                    ))}
                  </div>
                  <footer>
                    <span>
                      <Icon name="clock" size={14} /> Updated {i + 1}d ago
                    </span>
                    <button onClick={() => openOverlay("reveal")}>
                      View project <Icon name="arrow" size={15} />
                    </button>
                  </footer>
                </div>
              </article>
            ))}
          </div>
        </div>
        <aside className="match-column">
          <div className="match-label">
            <span>
              <Icon name="spark" size={14} /> YOUR BEST MATCH TODAY
            </span>
            <small>Refreshes in 18h</small>
          </div>
          <article className={`match-card ${accepted ? "accepted" : ""}`}>
            <div className="match-top">
              <div className="anonymous-person">
                <div className="blur-avatar">?</div>
                <span>
                  <b>Anonymous for now</b>PhD · Neuroscience
                </span>
              </div>
              <MetricRing value={94} label="MATCH" tone="violet" size={74} />
            </div>
            <div className="bridge-visual">
              <span>YOUR NEED</span>
              <i />
              <Icon name="spark" />
              <i />
              <span>THEIR OFFER</span>
            </div>
            <h2>
              {accepted
                ? "You’re interested. We’ll reveal both profiles if they agree."
                : "They have the EEG access you need. You have the method they need."}
            </h2>
            <p>
              They operate a <strong>128-channel mobile EEG facility</strong>{" "}
              and need your expertise in{" "}
              <strong>federated representation learning</strong> to compare
              cohorts without pooling protected data.
            </p>
            <div className="vector-match">
              <div>
                <span>Your need</span>
                <Tag tone="need">Longitudinal EEG</Tag>
              </div>
              <Icon name="arrow" />
              <div>
                <span>Their offer</span>
                <Tag tone="offer">Mobile EEG lab</Tag>
              </div>
            </div>
            <div className="proximity">
              <Icon name="pin" />
              <span>
                <b>0.4 miles away</b>Helen Wills Neuroscience Institute
              </span>
            </div>
            <button
              className={accepted ? "mutual-button accepted" : "mutual-button"}
              onClick={() => setAccepted(!accepted)}
            >
              {accepted ? (
                <>
                  <Icon name="check" /> Private interest sent
                </>
              ) : (
                <>
                  See why you match <Icon name="arrow" />
                </>
              )}
            </button>
            <small className="privacy-note">
              <Icon name="lock" size={12} /> Identity and work reveal only after
              both accept
            </small>
          </article>
          <button className="graph-glimpse" onClick={() => openOverlay("graph")}>
            <span>
              <Icon name="graph" />
              <b>Explore knowledge graph</b>
              <small>13 cross-department gaps found</small>
            </span>
            <Icon name="arrow" />
          </button>
          <button className="seal-prompt" onClick={() => setView("vault")}>
            <span>
              <Icon name="shield" />
              <b>Protect a new idea</b>
              <small>Prove it existed before you share it.</small>
            </span>
            <Icon name="arrow" />
          </button>
        </aside>
      </section>
    </div>
  )
}

function HomeView({
  setView,
  openOverlay,
  onTelemetry,
}: {
  setView: (view: View) => void
  openOverlay: (overlay: Overlay) => void
  onTelemetry?: () => void
}) {
  const [connected, setConnected] = useState(false)
  const [following, setFollowing] = useState(false)
  const [sortOrder, setSortOrder] = useState<"relevant" | "recent">("relevant")
  const [followingPeople, setFollowingPeople] = useState<Record<string, boolean>>({})

  const toggleFollowPerson = (name: string) => {
    setFollowingPeople((prev) => ({ ...prev, [name]: !prev[name] }))
  }
  return (
    <div className="home-view">
      <div className="home-columns">
        <aside className="home-left">
          <section className="profile-card clean-card">
            <div className="profile-cover">
              <span />
              <span />
              <span />
            </div>
            <div className="profile-card-body">
              <Avatar initials="AM" color="gold" active />
              <h2>Aria Malik</h2>
              <p>MS Computer Science · UC Berkeley</p>
              <small>
                Federated learning, neural decoding, and privacy-preserving AI
              </small>
              <button onClick={() => alert("Aria Malik\nMS Computer Science, UC Berkeley\nSpecialization: Federated Learning & Neural Decoding")}>
                View profile
              </button>
            </div>
            <div className="profile-stats">
              <button onClick={() => setView("campus")}>
                <span>Project views</span>
                <b>184</b>
              </button>
              <button onClick={() => openOverlay("reveal")}>
                <span>New matches</span>
                <b>12</b>
              </button>
            </div>
          </section>

          <section className="availability-card clean-card">
            <div>
              <span className="availability-dot" />
              <strong>Open to collaborate</strong>
            </div>
            <p>Capstone teams · Co-authoring</p>
            <button onClick={() => alert("Availability updated: Open to Capstone teams and Co-authoring.")}>Edit availability</button>
          </section>

          <section className="saved-card clean-card">
            <button onClick={() => setView("pod")}>
              <Icon name="pin" />
              <span>
                <b>Saved research</b>
                <small>18 papers · 4 projects</small>
              </span>
            </button>
            <button onClick={() => setView("vault")}>
              <Icon name="shield" />
              <span>
                <b>Private vault</b>
                <small>3 protected ideas</small>
              </span>
            </button>
          </section>
        </aside>

        <section className="research-feed">
          <div className="share-card clean-card">
            <div>
              <Avatar initials="AM" color="gold" />
              <button onClick={() => openOverlay("project")}>
                Share what you’re working on or looking for…
              </button>
            </div>
            <div className="share-actions">
              <button onClick={() => openOverlay("project")}>
                <Icon name="plus" />
                Post a project
              </button>
              <button onClick={() => setView("campus")}>
                <Icon name="users" />
                Find a collaborator
              </button>
              <button onClick={() => setView("vault")}>
                <Icon name="shield" />
                Protect an idea
              </button>
            </div>
          </div>

          <div className="feed-sort">
            <span />
            <button
              onClick={() =>
                setSortOrder(sortOrder === "relevant" ? "recent" : "relevant")
              }
            >
              Sort by: <b>{sortOrder === "relevant" ? "Most relevant" : "Most recent"}</b>{" "}
              <Icon name="chevron" size={12} />
            </button>
          </div>

          <article className="feed-card clean-card match-post">
            <header className="feed-card-header">
              <span className="feed-source-icon">
                <Icon name="spark" />
              </span>
              <div>
                <strong>Nexus match</strong>
                <span>Recommended because of your research needs</span>
              </div>
              <button className="icon-button">
                <Icon name="more" />
              </button>
            </header>
            <div className="match-post-body">
              <div className="match-person">
                <Avatar initials="JL" color="blue" active />
                <div>
                  <h2>Jordan Lee</h2>
                  <p>PhD Researcher in Neuroscience</p>
                  <span>Helen Wills Neuroscience Institute · 0.4 miles</span>
                </div>
                <div className="simple-match-score">
                  <b>94%</b>
                  <span>match</span>
                </div>
              </div>
              <p className="feed-lead">
                Jordan runs a mobile EEG lab and is looking for a collaborator
                with federated learning experience. You’re looking for
                longitudinal EEG access.
              </p>
              <div className="match-reasons">
                <div>
                  <span>They can offer</span>
                  <Tag tone="offer">128-channel mobile EEG</Tag>
                </div>
                <Icon name="arrow" />
                <div>
                  <span>You can offer</span>
                  <Tag tone="need">Federated representation learning</Tag>
                </div>
              </div>
            </div>
            <footer className="feed-card-actions">
              <button
                className={connected ? "connected" : ""}
                onClick={() =>
                  connected ? openOverlay("reveal") : setConnected(true)
                }
              >
                <Icon name={connected ? "check" : "users"} />
                {connected ? "Review connection" : "Connect privately"}
              </button>
              <button onClick={onTelemetry}>
                <Icon name="message" /> Ask a question
              </button>
              <small>Profiles reveal only after both people accept</small>
            </footer>
          </article>

          <article className="feed-card clean-card project-post">
            <header className="feed-card-header">
              <Avatar initials="MR" color="violet" active />
              <div>
                <strong>Maya Rodriguez</strong>
                <span>PhD Candidate · Robotics · Posted a project · 2h</span>
              </div>
              <button className="icon-button">
                <Icon name="more" />
              </button>
            </header>
            <div className="project-post-copy">
              <p>
                We’re starting a cross-department project on biodegradable
                aerial sensors for forest canopy health.
              </p>
              <div className="project-post-panel">
                <span className="project-post-art">
                  <Icon name="spark" size={36} />
                </span>
                <div>
                  <Tag tone="stage">PROTOTYPE</Tag>
                  <h2>Soft aerial sensors for forest canopy health</h2>
                  <p>
                    Looking for plant pathology expertise to help validate early
                    stress indicators from field trials.
                  </p>
                  <div>
                    <Tag tone="offer">Soft robotics</Tag>
                    <Tag tone="offer">SLAM</Tag>
                    <Tag tone="need">Needs: Plant pathology</Tag>
                  </div>
                </div>
              </div>
            </div>
            <footer className="feed-card-actions">
              <button
                className={following ? "connected" : ""}
                onClick={() => setFollowing(!following)}
              >
                <Icon name={following ? "check" : "plus"} />
                {following ? "Following" : "Follow project"}
              </button>
              <button onClick={() => alert("Comment thread opened for Soft aerial sensors project. Maya was notified.")}>
                <Icon name="message" /> Comment
              </button>
              <button
                onClick={() => {
                  navigator.clipboard?.writeText(window.location.origin)
                  alert("Project link copied to clipboard!")
                }}
              >
                <Icon name="send" /> Share
              </button>
            </footer>
          </article>
        </section>

        <aside className="home-right">
          <section className="next-step-card clean-card">
            <div className="right-card-title">
              <div>
                <span>YOUR POD</span>
                <h3>Neural Commons</h3>
              </div>
              <b>72%</b>
            </div>
            <p>Methods review is due Friday.</p>
            <div className="mini-progress">
              <i />
            </div>
            <button onClick={() => setView("pod")}>
              Continue your work <Icon name="arrow" />
            </button>
          </section>

          <section className="people-card clean-card">
            <div className="right-card-title">
              <h3>People you may want to know</h3>
              <button>
                <Icon name="more" />
              </button>
            </div>
            {[
              [
                "SC",
                "blue",
                "Sam Chen",
                "Computational biology",
                "Python · Genomics",
              ],
              [
                "NP",
                "teal",
                "Nina Patel",
                "Clinical neuroscience",
                "EEG · fMRI",
              ],
              [
                "EO",
                "violet",
                "Eli Okafor",
                "Privacy and security",
                "DP · Formal methods",
              ],
            ].map(([initials, color, name, role, skills]) => (
              <div className="person-suggestion" key={name}>
                <Avatar initials={initials} color={color} />
                <span>
                  <b>{name}</b>
                  <small>{role}</small>
                  <em>{skills}</em>
                </span>
                <button onClick={() => toggleFollowPerson(name)}>
                  <Icon name={followingPeople[name] ? "check" : "plus"} size={14} />{" "}
                  {followingPeople[name] ? "Following" : "Follow"}
                </button>
              </div>
            ))}
            <button className="see-all" onClick={() => setView("campus")}>
              See all suggestions <Icon name="arrow" />
            </button>
          </section>

          <section className="funding-card clean-card">
            <span>FUNDING MATCH</span>
            <h3>NIH R21 Exploratory Research</h3>
            <p>Strong fit for your neural decoding project.</p>
            <div>
              <b>Deadline</b>
              <span>Dec 12 · 64 days</span>
            </div>
            <button onClick={() => openOverlay("funding")}>View opportunity</button>
          </section>
          <footer className="home-footer">
            <button onClick={() => alert("Nexus — The Living Research Network & Studio. Unifying discovery, private ideation, and audited collaborative proposals.")}>
              About
            </button>
            <button onClick={() => alert("Nexus Privacy Policy: Zero plaintext training on private hypotheses. Local cryptographic proofs generated client-side.")}>
              Privacy
            </button>
            <button onClick={() => alert("Nexus Trust & Safety: Dual opt-in identity reveal guarantees privacy until mutual agreement.")}>
              Trust & safety
            </button>
            <button onClick={() => alert("Nexus Help Center: For support or questions, click Messages to Ask Nexus or consult your pod.")}>
              Help
            </button>
            <span>Nexus © 2025</span>
          </footer>
        </aside>
      </div>
    </div>
  )
}

function ProofView({
  setView,
  openOverlay,
  onTelemetry,
}: {
  setView: (view: View) => void
  openOverlay: (overlay: Overlay) => void
  onTelemetry?: () => void
}) {
  const [claim, setClaim] = useState(0)
  const [verifying, setVerifying] = useState(false)
  const [verified, setVerified] = useState(false)
  const [zoom, setZoom] = useState(118)
  const [sourceTab, setSourceTab] = useState<"pdf" | "extraction" | "audit">("pdf")

  const verify = () => {
    setVerifying(true)
    setVerified(false)
    window.setTimeout(() => {
      setVerifying(false)
      setVerified(true)
    }, 2200)
  }
  return (
    <div className="proof-view">
      <header className="studio-header">
        <div>
          <button
            className="icon-button"
            onClick={() => setView("pod")}
            title="Back to Pod Workspace"
          >
            <Icon name="chevron" />
          </button>
          <span>
            <small>NEURAL COMMONS · NSF SCC</small>
            <b>NSF SCC — Technical Narrative</b>
          </span>
        </div>
        <div className="studio-presence">
          <span>Saved 8 sec ago</span>
          <div className="facepile">
            <Avatar initials="JL" color="blue" active />
            <Avatar initials="MK" color="violet" active />
          </div>
          <button className="soft-button" onClick={onTelemetry}>
            <Icon name="message" /> Discuss
          </button>
          <button className="dark-button" onClick={() => openOverlay("export")}>
            Export <Icon name="chevron" size={14} />
          </button>
        </div>
      </header>
      <div className="proof-layout">
        <section className="editor-pane">
          <div className="editor-toolbar">
            <div>
              <button>
                Body <Icon name="chevron" size={12} />
              </button>
              <button>
                <b>B</b>
              </button>
              <button>
                <i>I</i>
              </button>
              <button>H₂</button>
              <button>
                <Icon name="code" />
              </button>
            </div>
            <div>
              <span className="ai-working">
                <i /> Nexus can suggest edits
              </span>
              <button className="icon-button">
                <Icon name="more" />
              </button>
            </div>
          </div>
          <div className="document">
            <div className="doc-meta">
              <span>PROJECT DESCRIPTION</span>
              <span>4 / 15 PAGES</span>
            </div>
            <h1>2. Technical Approach</h1>
            <p>
              Our central premise is that institution-specific neural
              representations can be aligned without transferring protected
              subject-level data. We propose a three-part system that couples
              private local adaptation with a globally shared latent reference.
            </p>
            <h2>2.1 Cross-site latent alignment</h2>
            <p>
              Each participating institution trains an adapter against its local
              EEG distribution. Only clipped, noised parameter deltas leave the
              institutional boundary.
            </p>
            <p
              className={`audited-claim ${claim === 0 ? "selected" : ""}`}
              onClick={() => setClaim(0)}
            >
              Recent cross-subject alignment methods retain{" "}
              <mark>94.2% of within-subject decoding accuracy</mark> while
              reducing calibration requirements by 61%.<sup>12</sup>
              <span className="claim-badge">
                <Icon name="verified" size={13} /> FIG 4B
              </span>
            </p>
            <div className="equation">
              z<sub>i</sub> = A<sub>k</sub> f<sub>θ</sub>(x<sub>i</sub>) + ε,
              &nbsp; ε ∼ N(0, σ²I)<span>(1)</span>
            </div>
            <p
              className={`audited-claim ${claim === 1 ? "selected" : ""}`}
              onClick={() => setClaim(1)}
            >
              This formulation preserves the geometry needed for downstream
              decoding while satisfying an{" "}
              <mark>(ε, δ)-differential privacy bound</mark> at every
              communication round.<sup>7</sup>
              <span className="claim-badge">
                <Icon name="verified" size={13} /> EQ 3
              </span>
            </p>
            <div className="ai-suggestion">
              <div>
                <Icon name="spark" />
                <span>
                  <b>Nexus suggestion</b>Explain why this privacy limit matters
                  in a clinical setting before introducing Aim 2.
                </span>
              </div>
              <p>
                Unlike conventional federated averaging, our alignment objective
                treats inter-site variance as a first-class signal rather than
                optimization noise.
              </p>
              <footer>
                <span>
                  <kbd>Tab</kbd> Accept
                </span>
                <span>
                  <kbd>Esc</kbd> Dismiss
                </span>
              </footer>
            </div>
            <div className="remote-caret caret-blue">
              <i />
              JON
            </div>
          </div>
        </section>
        <section className="source-pane">
          <div className="source-header">
            <div>
              <span className="section-kicker">CLAIM EVIDENCE</span>
              <h2>What supports this claim</h2>
            </div>
            <div>
              <button
                className="icon-button"
                onClick={() => alert("Expanded PDF view")}
                title="Expand PDF"
              >
                <Icon name="expand" />
              </button>
              <button
                className="icon-button"
                onClick={() => setView("pod")}
                title="Close source viewer"
              >
                <Icon name="close" />
              </button>
            </div>
          </div>
          <div className="source-tabs">
            <button
              className={sourceTab === "pdf" ? "active" : ""}
              onClick={() => setSourceTab("pdf")}
            >
              PDF source
            </button>
            <button
              className={sourceTab === "extraction" ? "active" : ""}
              onClick={() => setSourceTab("extraction")}
            >
              Extraction
            </button>
            <button
              className={sourceTab === "audit" ? "active" : ""}
              onClick={() => setSourceTab("audit")}
            >
              Audit trail
            </button>
          </div>
          <div className="paper-identity">
            <div className="paper-thumb">NMI</div>
            <div>
              <strong>
                Federated Foundation Models for Privacy-Preserving Neural
                Decoding
              </strong>
              <span>Zhang et al. · 2024 · Nature Machine Intelligence</span>
            </div>
            <button className="icon-button">
              <Icon name="download" />
            </button>
          </div>
          <div className="pdf-stage">
            <div className="page-number">PAGE 8 / 14</div>
            <div className="pdf-page">
              <div className="pdf-title">
                Cross-subject alignment preserves decoding performance
              </div>
              <div className="pdf-columns">
                <div>
                  <i />
                  <i />
                  <i />
                  <i className="short" />
                  <i />
                  <i />
                  <i />
                </div>
                <div>
                  <i />
                  <i />
                  <i />
                  <i />
                  <i className="short" />
                  <i />
                </div>
              </div>
              <div className="figure">
                <div className="chart">
                  <span className="axis-y">Accuracy (%)</span>
                  <div className="bars">
                    <i style={{ height: "68%" }} />
                    <i style={{ height: "81%" }} />
                    <i style={{ height: "76%" }} />
                    <i style={{ height: "92%" }} />
                    <i style={{ height: "89%" }} />
                  </div>
                  <span className="axis-x">Subject cohorts →</span>
                </div>
                <div className="sam-polygon">
                  <span>SAM 3.1 · FIGURE 4B</span>
                </div>
              </div>
              <div className="caption">
                <b>Figure 4.</b> Cross-subject transfer results.{" "}
                <mark>
                  (b) Latent alignment retains 94.2% of within-subject
                  performance across five held-out cohorts.
                </mark>
              </div>
            </div>
            <div className="zoom-tools">
              <button onClick={() => setZoom(Math.max(70, zoom - 10))}>−</button>
              <span>{zoom}%</span>
              <button onClick={() => setZoom(Math.min(180, zoom + 10))}>+</button>
            </div>
          </div>
          <div className="audit-bar">
            <div className="audit-result">
              <span className={verifying ? "scan-icon scanning" : "scan-icon"}>
                <Icon name={verified ? "check" : "shield"} />
              </span>
              <div>
                <small>SOURCE CHECK</small>
                <strong>
                  {verifying
                    ? "Checking the source…"
                    : verified
                      ? "The source supports this claim"
                      : "Strong source match"}
                </strong>
                <span>
                  {verifying
                    ? "Comparing your claim with Figure 4b"
                    : verified
                      ? "Checked just now · no contradiction found"
                      : "Last checked from the indexed paper"}
                </span>
              </div>
            </div>
            <button
              className="verify-button"
              onClick={verify}
              disabled={verifying}
            >
              {verifying ? (
                <>
                  <i /> Checking
                </>
              ) : (
                <>
                  <Icon name="spark" /> Check against source
                </>
              )}
            </button>
          </div>
        </section>
        <aside className="claim-rail">
          <div className="audit-score">
            <MetricRing value={100} label="AUDIT" tone="green" size={68} />
            <span>
              <b>All claims sourced</b>
              <small>18 of 18 checked</small>
            </span>
          </div>
          <span className="rail-label">CLAIMS ON PAGE</span>
          {[
            ["94.2% accuracy", "Figure 4b · p. 8"],
            ["Privacy bound", "Equation 3 · p. 6"],
            ["61% less calibration", "Table 2 · p. 7"],
          ].map((x, i) => (
            <button
              className={claim === i ? "active" : ""}
              onClick={() => setClaim(i)}
              key={x[0]}
            >
              <Icon name={i < 2 ? "verified" : "clock"} />
              <span>
                <b>{x[0]}</b>
                <small>{x[1]}</small>
              </span>
            </button>
          ))}
          <div className="rail-bottom">
            <button>
              <Icon name="message" />
              <span>Ask literature</span>
            </button>
            <button onClick={() => openOverlay("reasoning")}>
              <Icon name="brain" />
              <span>Reasoning</span>
            </button>
          </div>
        </aside>
      </div>
    </div>
  )
}

function TelemetryDrawer({
  onClose,
  openOverlay,
}: {
  onClose: () => void
  openOverlay: (overlay: Overlay) => void
}) {
  const [question, setQuestion] = useState("")
  const [answer, setAnswer] = useState(false)
  const [telemetryData, setTelemetryData] = useState<{
    latency: number
    tokens: string
    reasoningRatio: string
    cost: string
  }>({
    latency: 24,
    tokens: "147.5k",
    reasoningRatio: "76.4%",
    cost: "$0.0474",
  })

  useEffect(() => {
    fetch('/api/v2/campus/meta-ai/telemetry')
      .then((r) => r.json())
      .then((d) => {
        if (d && d.build_telemetry) {
          const totalTok = d.build_telemetry.total_tokens_processed || 147536
          setTelemetryData({
            latency: d.connection?.latency_ms || 24,
            tokens: (totalTok / 1000).toFixed(1) + "k",
            reasoningRatio: d.build_telemetry.reasoning_tokens_ratio || "76.4%",
            cost: "$" + (d.build_telemetry.estimated_cost_usd || 0.0474).toFixed(4),
          })
        }
      })
      .catch(() => {})
  }, [])

  const prompts = [
    "What evidence is missing?",
    "Summarize team decisions",
    "Check Aim 2 for unsupported claims",
  ]
  const ask = () => {
    if (question.trim()) setAnswer(true)
  }
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="telemetry-drawer" onClick={(e) => e.stopPropagation()}>
        <header>
          <div>
            <span className="section-kicker">ASK NEXUS</span>
            <h2>Ask your research workspace</h2>
          </div>
          <button className="icon-button" onClick={onClose}>
            <Icon name="close" />
          </button>
        </header>
        <div className="assistant-composer">
          <div>
            <Icon name="spark" />
            <textarea
              aria-label="Ask Nexus"
              placeholder="Ask across your papers, notes, and proposal…"
              value={question}
              onChange={(event) => {
                setQuestion(event.target.value)
                setAnswer(false)
              }}
            />
          </div>
          <button className="accent-button" onClick={ask}>
            Ask <Icon name="arrow" />
          </button>
        </div>
        {answer && (
          <div className="assistant-answer">
            <div>
              <Icon name="spark" />
              <strong>Nexus</strong>
              <Tag tone="verification">3 sources</Tag>
            </div>
            <p>
              Aim 2 is well supported, but the 61% calibration reduction relies
              on a single cohort. Add a second independent benchmark before the
              methods review.
            </p>
            <button>
              Open the supporting papers <Icon name="arrow" />
            </button>
          </div>
        )}
        <div className="prompt-chips">
          {prompts.map((prompt) => (
            <button
              key={prompt}
              onClick={() => {
                setQuestion(prompt)
                setAnswer(false)
              }}
            >
              {prompt}
            </button>
          ))}
        </div>
        <div className="drawer-section-title">
          <span>AI activity</span>
          <small>All systems available</small>
        </div>
        <div className="engine-card active">
          <div>
            <span className="engine-icon">
              <Icon name="brain" />
            </span>
            <div>
              <b>muse-wonder-1.0</b>
              <small>Frontier reasoning · online</small>
            </div>
            <i />
          </div>
          <dl>
            <div>
              <dt>Latency p50</dt>
              <dd>{telemetryData.latency} ms</dd>
            </div>
            <div>
              <dt>Tokens today</dt>
              <dd>{telemetryData.tokens}</dd>
            </div>
            <div>
              <dt>Est. Cost</dt>
              <dd>{telemetryData.cost}</dd>
            </div>
          </dl>
          <div className="sparkline">
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
          </div>
        </div>
        <div className="engine-card">
          <div>
            <span className="engine-icon violet">
              <Icon name="eye" />
            </span>
            <div>
              <b>sam-3.1</b>
              <small>Multimodal vision · online</small>
            </div>
            <i />
          </div>
          <dl>
            <div>
              <dt>Mask latency</dt>
              <dd>312 ms</dd>
            </div>
            <div>
              <dt>Figures parsed</dt>
              <dd>8,412</dd>
            </div>
            <div>
              <dt>Confidence</dt>
              <dd>97.4%</dd>
            </div>
          </dl>
        </div>
        <button
          className="reasoning-trace"
          onClick={() => openOverlay("reasoning")}
        >
          <div>
            <span>REASONING INSPECTOR</span>
            <Tag tone="verification">LIVE</Tag>
          </div>
          <p>
            <code>trace_8f21</code> evaluated claim entailment across caption,
            figure legend, and plotted values.
          </p>
          <div className="token-line">
            <span>context retrieval</span>
            <i style={{ width: "92%" }} />
          </div>
          <div className="token-line">
            <span>visual grounding</span>
            <i style={{ width: "76%" }} />
          </div>
          <div className="token-line">
            <span>contradiction scan</span>
            <i style={{ width: "64%" }} />
          </div>
          <footer>
            <span>1,842 reasoning tokens</span>
            <span>2.2 sec</span>
          </footer>
          <span className="trace-open">
            Open reasoning inspector <Icon name="arrow" size={13} />
          </span>
        </button>
        <p className="drawer-note">
          <Icon name="shield" /> Nexus exposes verifiable reasoning summaries
          and source traces while protecting private model internals.
        </p>
      </aside>
    </div>
  )
}

function ProductOverlay({
  overlay,
  onClose,
}: {
  overlay: Overlay
  onClose: () => void
}) {
  const [completed, setCompleted] = useState(false)
  const [selectedFormat, setSelectedFormat] = useState("LaTeX")
  const [projectUrl, setProjectUrl] = useState("https://arxiv.org/abs/2502.04918")
  const [activeGrant, setActiveGrant] = useState(0)
  const [copiedHash, setCopiedHash] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [ingestedData, setIngestedData] = useState<{
    title: string
    abstract: string
    offers: string[]
    needs: string[]
  } | null>(null)

  const handleIngest = async () => {
    if (!projectUrl.trim()) return
    setIngesting(true)
    try {
      const res = await fetch('/api/v2/campus/project/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: projectUrl }),
      })
      if (res.ok) {
        const data = await res.json()
        setIngestedData({
          title: data.extracted_title || "Event-Driven Neuromorphic EEG Decoder",
          abstract: data.abstract_safe || "A sub-milliwatt spike-timing neuromorphic processor designed for high-density neural recordings.",
          offers: data.offers || ["Sub-milliwatt neuromorphic FPGA bitstreams", "EEG benchmark dataset"],
          needs: data.needs || ["Clinical neurosurgery collaborators", "Ultra-low latency telemetry"],
        })
        setCompleted(true)
      } else {
        setCompleted(true)
      }
    } catch {
      setCompleted(true)
    } finally {
      setIngesting(false)
    }
  }

  const handleCopy = (toCopy: string) => {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(toCopy)
      setCopiedHash(true)
      setTimeout(() => setCopiedHash(false), 2000)
    }
  }

  const handleExportDownload = () => {
    const filename = `nexus_proposal_nsf_scc.${selectedFormat === "LaTeX" ? "tex" : selectedFormat === "Markdown" ? "md" : "pdf"}`
    let content = ""
    const mimeType = selectedFormat === "LaTeX" ? "text/x-tex" : selectedFormat === "Markdown" ? "text/markdown" : "application/pdf"
    if (selectedFormat === "LaTeX") {
      content = `% =========================================================================\n% Nexus Academic Proposal Export: NSF Smart & Connected Communities\n% Generated by Nexus Living Campus Graph Studio with Cryptographic Audit Trail\n% Certificate Anchor: #NX-8492 | SHA-256: b3e1c8f47a91d2c3e5f7a8b9c0d1e2f3\n% =========================================================================\n\n\\documentclass[11pt,twocolumn]{article}\n\\usepackage[utf8]{inputenc}\n\\usepackage{amsmath,amssymb,amsfonts}\n\\usepackage{graphicx}\n\\usepackage{hyperref}\n\\usepackage{cite}\n\n\\title{\\textbf{Decentralized Edge Privacy and Neuromorphic Decoders for Campus Infrastructure}}\n\\author{\\textbf{Aria Malik}$^{1}$, \\textbf{Jordan Lee}$^{2}$, \\textbf{Maya Patel}$^{3}}\\date{November 2026}\n\n\\begin{document}\n\\maketitle\n\n\\begin{abstract}\nWe introduce a decentralized edge privacy architecture coupling spike-timing neuromorphic decoders with asynchronous differential privacy bounds.\\end{abstract}\n\n\\section{Introduction and Problem Framing}\nModern university campuses represent high-density cyber-physical microgrids where edge sensing, wearable telemetry, and autonomous systems intersect...\\section{Technical Approach and Latent Alignment}\n\\begin{equation}\nz_{i} = A_{k} f_{\\theta}(x_{i}) + \\varepsilon, \\quad \\varepsilon \\sim \\mathcal{N}(0, \\sigma^{2} I)\n\\end{equation}\nEquation (1) satisfies $(\\varepsilon, \\delta)$-differential privacy bounds under the Thorne-Zhao theorem.\\section{Citation Integrity and Verified Grounding}\nAll 18 cited claims have undergone automated Pixel-to-Proof figure segmentation via SAM 3.1 and Meta AI Muse Wonder verification.\\bibliographystyle{IEEEtran}\n\\end{document}\n`
    } else if (selectedFormat === "Markdown") {
      content = `# Decentralized Edge Privacy and Neuromorphic Decoders for Campus Infrastructure\n\n**Authors:** Aria Malik, Jordan Lee, Maya Patel\n**Certificate Anchor:** #NX-8492\n\n## Abstract\nWe introduce a decentralized edge privacy architecture coupling spike-timing neuromorphic decoders with asynchronous differential privacy bounds...`
    } else {
      content = `%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF`
    }
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const titles: Record<Overlay, { eyebrow: string; title: string }> = {
    reveal: {
      eyebrow: "MUTUAL CONNECTION",
      title: "You both chose to connect",
    },
    verify: {
      eyebrow: "PUBLIC PRIORITY RECORD",
      title: "Certificate #NX-8492",
    },
    graph: {
      eyebrow: "KNOWLEDGE GRAPH",
      title: "Explore the campus research network",
    },
    funding: {
      eyebrow: "FUNDING FINDER",
      title: "Grants that fit your active work",
    },
    project: {
      eyebrow: "NEW PROJECT",
      title: "Share what you’re building",
    },
    "peer-review": {
      eyebrow: "PRE-FLIGHT AUDIT",
      title: "How reviewers may score this proposal",
    },
    conflict: {
      eyebrow: "EVIDENCE CONFLICT",
      title: "Two papers reach different conclusions",
    },
    export: {
      eyebrow: "ACADEMIC EXPORT",
      title: "Prepare a submission-ready package",
    },
    reasoning: {
      eyebrow: "REASONING INSPECTOR",
      title: "How Nexus reached this answer",
    },
  }

  const grants = [
    {
      agency: "NSF",
      title: "Smart & Connected Communities",
      amount: "$250k–$1.5M",
      fit: 94,
      deadline: "Dec 12",
    },
    {
      agency: "NIH",
      title: "R21 Exploratory Research",
      amount: "Up to $275k",
      fit: 88,
      deadline: "Jan 16",
    },
    {
      agency: "DARPA",
      title: "Human–AI Symbiosis",
      amount: "$1M–$3M",
      fit: 76,
      deadline: "Feb 03",
    },
  ]

  return (
    <div
      className={`product-overlay ${
        overlay === "graph" || overlay === "funding" ? "workspace-overlay" : ""
      }`}
      onClick={onClose}
    >
      <section
        className={`overlay-shell overlay-${overlay}`}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="overlay-header">
          <div>
            <span className="section-kicker">{titles[overlay].eyebrow}</span>
            <h2>{titles[overlay].title}</h2>
          </div>
          <button className="icon-button" onClick={onClose}>
            <Icon name="close" />
          </button>
        </header>

        {overlay === "reveal" && (
          <div className="reveal-flow">
            <div className="reveal-people">
              <div>
                <Avatar initials="AM" color="gold" active />
                <strong>Aria Malik</strong>
                <span>Federated learning</span>
              </div>
              <span className="reveal-link">
                <Icon name="check" />
              </span>
              <div>
                <Avatar initials="JL" color="blue" active />
                <strong>Jordan Lee</strong>
                <span>Clinical neuroscience</span>
              </div>
            </div>
            <div className="reveal-summary">
              <Icon name="shield" />
              <div>
                <strong>What will be shared</strong>
                <p>
                  Full names, university email, project summary, and the files
                  each of you approved. Private Vault content stays sealed.
                </p>
              </div>
            </div>
            <label className="consent-check">
              <input type="checkbox" defaultChecked />
              Add a viewer watermark to every shared document
            </label>
            {completed ? (
              <div className="overlay-success">
                <Icon name="check" />
                <span>
                  <b>Connection revealed</b>
                  Jordan is now in your Messages.
                </span>
              </div>
            ) : (
              <div className="overlay-actions">
                <button className="soft-button" onClick={onClose}>
                  Not yet
                </button>
                <button
                  className="accent-button"
                  onClick={() => setCompleted(true)}
                >
                  Reveal and connect
                </button>
              </div>
            )}
          </div>
        )}

        {overlay === "verify" && (
          <div className="verification-page">
            <div className="verification-status">
              <span>
                <Icon name="verified" size={28} />
              </span>
              <div>
                <strong>Valid Nexus certificate</strong>
                <p>
                  This record has not changed since it was timestamped on 09 Oct
                  2025.
                </p>
              </div>
            </div>
            <div className="verification-grid">
              <dl>
                <div>
                  <dt>Certificate</dt>
                  <dd>#NX-8492</dd>
                </div>
                <div>
                  <dt>Owner</dt>
                  <dd>Aria Malik</dd>
                </div>
                <div>
                  <dt>Timestamp</dt>
                  <dd>09 Oct 2025 · 14:32 UTC</dd>
                </div>
                <div>
                  <dt>Merkle root</dt>
                  <dd>0x774a…18fc</dd>
                </div>
                <div>
                  <dt>Content</dt>
                  <dd>Private · hash only</dd>
                </div>
              </dl>
              <div className="qr-placeholder">
                <span>
                  NX
                  <br />
                  8492
                </span>
                <small>Scan to verify</small>
              </div>
            </div>
            <div className="chain-record">
              <Icon name="graph" />
              <span>
                <b>L2 block #19,442,108</b>
                Confirmed by 18 network validators
              </span>
              <Tag tone="verification">MATCH</Tag>
            </div>
            <div className="overlay-actions">
              <button className="soft-button">
                <Icon name="copy" /> Copy verification link
              </button>
              <button
                className="accent-button"
                onClick={() => {
                  const receipt = {
                    certificateId: "NX-8492",
                    merkleRoot:
                      "0x774ab92d18fc4e8932bce10871982aef12d094",
                    blockHeight: 18492041,
                    timestamp: "2025-10-09T14:32:18Z",
                    owner: "Aria Malik",
                    status: "SEALED_ON_CHAIN",
                  }
                  const blob = new Blob([JSON.stringify(receipt, null, 2)], {
                    type: "application/json",
                  })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement("a")
                  a.href = url
                  a.download = "nexus_verification_receipt_NX8492.json"
                  a.click()
                  URL.revokeObjectURL(url)
                }}
              >
                <Icon name="download" /> Download receipt
              </button>
            </div>
          </div>
        )}

        {overlay === "graph" && (
          <div className="graph-workspace">
            <div className="graph-toolbar">
              <label>
                <Icon name="search" />
                <input placeholder="Search people, topics, or papers" />
              </label>
              <button className="active">All campus</button>
              <button>People</button>
              <button>Projects</button>
              <button>Papers</button>
              <button>
                <Icon name="filter" /> Filters
              </button>
            </div>
            <div className="graph-main">
              <div className="graph-canvas">
                <svg viewBox="0 0 800 520" aria-label="Research graph">
                  <g stroke="#bfd0df" strokeWidth="1">
                    <path d="M150 190 350 110 520 180 650 95M150 190 280 330 470 360 650 95M350 110 470 360M520 180 280 330M470 360 680 390M280 330 120 410" />
                  </g>
                  {([
                    [150, 190, 32, "#0a66c2"],
                    [350, 110, 27, "#6755a6"],
                    [520, 180, 36, "#2d8067"],
                    [650, 95, 23, "#a46d27"],
                    [280, 330, 34, "#0a66c2"],
                    [470, 360, 29, "#6755a6"],
                    [680, 390, 20, "#2d8067"],
                    [120, 410, 19, "#a46d27"],
                  ] as [number, number, number, string][]).map(([cx, cy, r, fill], index) => (
                    <g key={index}>
                      <circle cx={cx} cy={cy} r={r} fill={fill} opacity=".92" />
                      <circle
                        cx={cx}
                        cy={cy}
                        r={r + 7}
                        fill="none"
                        stroke={fill}
                        opacity=".15"
                      />
                    </g>
                  ))}
                  <g
                    fill="#33434f"
                    fontSize="12"
                    fontFamily="DM Sans"
                    textAnchor="middle"
                  >
                    <text x="150" y="245">
                      Federated AI
                    </text>
                    <text x="350" y="70">
                      Neural decoding
                    </text>
                    <text x="520" y="238">
                      Clinical EEG
                    </text>
                    <text x="650" y="55">
                      Privacy
                    </text>
                    <text x="280" y="390">
                      Edge systems
                    </text>
                    <text x="470" y="418">
                      Representation learning
                    </text>
                  </g>
                </svg>
                <div className="graph-gap">
                  <Icon name="spark" />
                  <span>
                    <b>Research gap found</b>
                    No active Berkeley project connects federated adaptation
                    with longitudinal EEG drift.
                  </span>
                  <button>Create project</button>
                </div>
                <div className="graph-legend">
                  <span>
                    <i className="blue" /> People
                  </span>
                  <span>
                    <i className="green" /> Projects
                  </span>
                  <span>
                    <i className="violet" /> Topics
                  </span>
                  <span>
                    <i className="gold" /> Papers
                  </span>
                </div>
              </div>
              <aside className="graph-inspector">
                <span className="section-kicker">SELECTED TOPIC</span>
                <h3>Clinical EEG</h3>
                <p>42 researchers · 18 active projects · 214 papers</p>
                <div className="topic-meter">
                  <span>Campus activity</span>
                  <i>
                    <b />
                  </i>
                  <small>High</small>
                </div>
                <strong>Closest people</strong>
                {["Jordan Lee", "Nina Patel", "Prof. S. Rao"].map(
                  (person, index) => (
                    <button key={person}>
                      <Avatar
                        initials={person
                          .split(" ")
                          .map((part) => part[0])
                          .join("")
                          .slice(0, 2)}
                        color={index === 0 ? "blue" : "teal"}
                      />
                      <span>
                        <b>{person}</b>
                        <small>{index + 1} shared research paths</small>
                      </span>
                      <Icon name="chevron" />
                    </button>
                  ),
                )}
              </aside>
            </div>
          </div>
        )}

        {overlay === "funding" && (
          <div className="funding-workspace">
            <aside className="funding-filters">
              <label>
                <Icon name="search" />
                <input placeholder="Search grants" />
              </label>
              <strong>Agency</strong>
              {["All agencies", "NSF", "NIH", "DARPA", "DOE"].map(
                (agency, index) => (
                  <button className={index === 0 ? "active" : ""} key={agency}>
                    {agency}
                    {index === 0 && <span>24</span>}
                  </button>
                ),
              )}
              <strong>Linked pod</strong>
              <select>
                <option>Neural Commons</option>
                <option>All active pods</option>
              </select>
              <strong>Deadline</strong>
              <button>Next 90 days</button>
            </aside>
            <div className="grant-list">
              <div className="grant-list-header">
                <div>
                  <b>24 matching opportunities</b>
                  <span>Ranked against Neural Commons</span>
                </div>
                <button>
                  Best fit <Icon name="chevron" />
                </button>
              </div>
              {grants.map((grant, index) => (
                <button
                  className={activeGrant === index ? "active" : ""}
                  key={grant.title}
                  onClick={() => setActiveGrant(index)}
                >
                  <span className="agency-mark">{grant.agency}</span>
                  <span>
                    <small>
                      {grant.agency} · Deadline {grant.deadline}
                    </small>
                    <b>{grant.title}</b>
                    <em>{grant.amount}</em>
                  </span>
                  <strong>{grant.fit}% fit</strong>
                </button>
              ))}
            </div>
            <aside className="grant-detail">
              <span className="agency-mark">{grants[activeGrant].agency}</span>
              <Tag tone="verification">{grants[activeGrant].fit}% pod fit</Tag>
              <h3>{grants[activeGrant].title}</h3>
              <p>
                Supports interdisciplinary research that integrates computing,
                community outcomes, and responsible data infrastructure.
              </p>
              <dl>
                <div>
                  <dt>Award</dt>
                  <dd>{grants[activeGrant].amount}</dd>
                </div>
                <div>
                  <dt>Deadline</dt>
                  <dd>{grants[activeGrant].deadline}</dd>
                </div>
                <div>
                  <dt>Eligibility</dt>
                  <dd>University teams</dd>
                </div>
              </dl>
              <strong>Why it fits</strong>
              <ul>
                <li>Matches 8 of 10 pod capabilities</li>
                <li>Accepts clinical AI infrastructure</li>
                <li>Your evidence board covers 3 required areas</li>
              </ul>
              <button
                className="accent-button"
                onClick={() =>
                  alert("Grant opportunity linked to Neural Commons pod milestones!")
                }
              >
                Link to Neural Commons
              </button>
              <button
                className="soft-button"
                onClick={() =>
                  window.open(
                    "https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=505527",
                    "_blank",
                  )
                }
              >
                Open solicitation
              </button>
            </aside>
          </div>
        )}

        {overlay === "project" && (
          <div className="project-creator">
            <div className="ingest-box">
              <span>
                <Icon name="plus" size={24} />
              </span>
              <div>
                <strong>Start from work that already exists</strong>
                <p>
                  Paste an arXiv paper, GitHub repository, or project page.
                  Nexus will draft the project details for you.
                </p>
              </div>
              <label>
                <input
                  value={projectUrl}
                  onChange={(event) => setProjectUrl(event.target.value)}
                  placeholder="https://arxiv.org/abs/..."
                />
                <button
                  className="accent-button"
                  onClick={handleIngest}
                  disabled={ingesting}
                >
                  {ingesting ? "Analyzing with Meta AI…" : "Import with Meta AI"}
                </button>
              </label>
            </div>
            {completed && (
              <div className="ingest-success">
                <Icon name="check" />
                Imported title, abstract, methods, and repository metadata.
              </div>
            )}
            <div className="creator-form">
              <label>
                Project title
                <input
                  key={ingestedData?.title || (completed ? "done" : "idle")}
                  defaultValue={
                    ingestedData?.title ||
                    (completed
                      ? "Event-Driven Neuromorphic EEG Decoder"
                      : "")
                  }
                  placeholder="Give your project a clear name"
                />
              </label>
              <label>
                Safe public summary
                <textarea
                  key={ingestedData?.abstract || (completed ? "done_abs" : "idle_abs")}
                  defaultValue={
                    ingestedData?.abstract ||
                    (completed
                      ? "A sub-milliwatt spike-timing neuromorphic processor designed for high-density neural recordings with on-chip spike sorting."
                      : "")
                  }
                  placeholder="What are you working on?"
                />
              </label>
              <div>
                <label>
                  Stage
                  <select defaultValue="Prototype">
                    <option>Hypothesis</option>
                    <option>Prototype</option>
                    <option>Experiment</option>
                    <option>Writing</option>
                  </select>
                </label>
                <label>
                  Audience
                  <select>
                    <option>Berkeley community</option>
                    <option>Public</option>
                    <option>Private matches only</option>
                  </select>
                </label>
              </div>
              <section>
                <span>OFFERS</span>
                <Tag tone="offer">Federated learning</Tag>
                <Tag tone="offer">Privacy bounds</Tag>
                <button>
                  <Icon name="plus" /> Add
                </button>
              </section>
              <section>
                <span>NEEDS</span>
                <Tag tone="need">Clinical EEG</Tag>
                <Tag tone="need">IRB guidance</Tag>
                <button>
                  <Icon name="plus" /> Add
                </button>
              </section>
            </div>
            <div className="overlay-actions">
              <button className="soft-button" onClick={onClose}>
                Save draft
              </button>
              <button className="accent-button" onClick={onClose}>
                Publish project
              </button>
            </div>
          </div>
        )}

        {overlay === "peer-review" && (
          <div className="peer-review">
            <div className="review-overall">
              <MetricRing value={82} label="READY" tone="blue" size={96} />
              <div>
                <h3>Strong, with two issues to resolve</h3>
                <p>
                  Simulated against the NSF merit review rubric and 42 funded
                  proposals in adjacent fields.
                </p>
              </div>
              <button className="soft-button">
                <Icon name="download" /> Full report
              </button>
            </div>
            <div className="rubric-grid">
              {[
                [
                  "Intellectual Merit",
                  88,
                  "Strong",
                  "Clear novelty and testable aims.",
                ],
                [
                  "Broader Impacts",
                  74,
                  "Needs work",
                  "Outcomes lack measurable community targets.",
                ],
                [
                  "Technical Feasibility",
                  84,
                  "Strong",
                  "Methods align with available infrastructure.",
                ],
                [
                  "Team Qualifications",
                  91,
                  "Excellent",
                  "Roles map well to the proposed work.",
                ],
              ].map(([title, score, verdict, copy]) => (
                <article key={String(title)}>
                  <div>
                    <span>{title}</span>
                    <b>{score}</b>
                  </div>
                  <i>
                    <span style={{ width: `${score}%` }} />
                  </i>
                  <strong>{verdict}</strong>
                  <p>{copy}</p>
                </article>
              ))}
            </div>
            <div className="review-issues">
              <strong>Resolve before review</strong>
              <button>
                <span>01</span>
                <p>
                  <b>Add a measurable Broader Impacts outcome</b>
                  Section 4 names audiences but not target outcomes.
                </p>
                <Icon name="arrow" />
              </button>
              <button>
                <span>02</span>
                <p>
                  <b>Clarify the fallback for Aim 2</b>
                  Reviewers may question what happens if site alignment fails.
                </p>
                <Icon name="arrow" />
              </button>
            </div>
            <div className="overlay-actions">
              <button
                className="soft-button"
                onClick={() =>
                  alert("Pre-flight audit report shared to Neural Commons activity log!")
                }
              >
                Share with pod
              </button>
              <button className="accent-button" onClick={onClose}>
                Fix issues in proposal
              </button>
            </div>
          </div>
        )}

        {overlay === "conflict" && (
          <div className="conflict-view">
            <div className="conflict-summary">
              <Icon name="eye" />
              <p>
                These papers study similar privacy risks but use different
                threat models. The disagreement may be contextual rather than
                factual.
              </p>
            </div>
            <div className="paper-comparison">
              <article>
                <Tag tone="supports">SUPPORTS</Tag>
                <h3>
                  Federated Foundation Models for Privacy-Preserving Neural
                  Decoding
                </h3>
                <small>Zhang et al. · 2024</small>
                <blockquote>
                  “No significant reconstruction was observed under the bounded
                  participant threat model.”
                </blockquote>
                <dl>
                  <div>
                    <dt>Cohort</dt>
                    <dd>5 institutions · 640 subjects</dd>
                  </div>
                  <div>
                    <dt>Threat model</dt>
                    <dd>Honest-but-curious server</dd>
                  </div>
                  <div>
                    <dt>Privacy budget</dt>
                    <dd>ε = 2.1</dd>
                  </div>
                </dl>
              </article>
              <span className="versus">VS</span>
              <article>
                <Tag tone="contradicts">CONTRADICTS</Tag>
                <h3>The Privacy Cost of Brain–Computer Interfaces</h3>
                <small>Rao et al. · 2023</small>
                <blockquote>
                  “Identity attributes remained recoverable from shared updates
                  under an active adversary.”
                </blockquote>
                <dl>
                  <div>
                    <dt>Cohort</dt>
                    <dd>2 institutions · 84 subjects</dd>
                  </div>
                  <div>
                    <dt>Threat model</dt>
                    <dd>Active malicious participant</dd>
                  </div>
                  <div>
                    <dt>Privacy budget</dt>
                    <dd>Not constrained</dd>
                  </div>
                </dl>
              </article>
            </div>
            <div className="conflict-recommendation">
              <Icon name="spark" />
              <span>
                <b>Recommended synthesis</b>
                State that privacy holds under bounded server threats, while
                active participant attacks remain an open limitation.
              </span>
              <button
                onClick={() => {
                  alert("Balanced claim inserted into Section 2.1 of Proposal Studio!")
                  onClose()
                }}
              >
                Insert balanced claim
              </button>
            </div>
          </div>
        )}

        {overlay === "export" && (
          <div className="export-dialog">
            <div className="format-grid">
              {[
                ["PDF", "Publication-ready document", "book"],
                ["LaTeX", "Source files + bibliography", "code"],
                ["Markdown", "Clean portable draft", "message"],
              ].map(([format, copy, icon]) => (
                <button
                  className={selectedFormat === format ? "active" : ""}
                  onClick={() => setSelectedFormat(format)}
                  key={format}
                >
                  <span>
                    <Icon name={icon as IconName} />
                  </span>
                  <b>{format}</b>
                  <small>{copy}</small>
                  {selectedFormat === format && <Icon name="check" />}
                </button>
              ))}
            </div>
            <div className="export-options">
              <strong>Include in package</strong>
              {[
                [
                  "Formatted bibliography",
                  "Required for academic submission",
                  true,
                ],
                ["BibTeX library", "18 verified sources", true],
                [
                  "Citation audit appendix",
                  "Claim-to-source verification report",
                  true,
                ],
                ["Proof certificates", "Cryptographic priority records", false],
                ["Reviewer comments", "Internal team discussion", false],
              ].map(([label, copy, checked]) => (
                <label key={String(label)}>
                  <input type="checkbox" defaultChecked={Boolean(checked)} />
                  <span>
                    <b>{label}</b>
                    <small>{copy}</small>
                  </span>
                </label>
              ))}
            </div>
            <div className="package-summary">
              <Icon name="shield" />
              <span>
                <b>{selectedFormat} package · 4.8 MB</b>
                18 citations checked · 0 unresolved source warnings
              </span>
            </div>
            <div className="overlay-actions">
              <button className="soft-button">Save export preset</button>
              <button className="accent-button" onClick={handleExportDownload}>
                <Icon name="download" /> Export {selectedFormat}
              </button>
            </div>
          </div>
        )}

        {overlay === "reasoning" && (
          <div className="reasoning-inspector">
            <div className="reasoning-question">
              <span>QUESTION</span>
              <p>
                Does the cited evidence support the claim that cross-site
                alignment retains 94.2% of decoding accuracy?
              </p>
            </div>
            <div className="reasoning-layout">
              <div className="reasoning-tree">
                {[
                  [
                    "1",
                    "Understand the claim",
                    "Metric: retained accuracy · Scope: cross-site alignment",
                  ],
                  [
                    "2",
                    "Retrieve relevant evidence",
                    "3 passages and Figure 4b ranked above 0.90 relevance",
                  ],
                  [
                    "3",
                    "Inspect the figure",
                    "Caption and plotted values both report 94.2% retention",
                  ],
                  [
                    "4",
                    "Check for contradictions",
                    "No conflicting result found in the cited paper",
                  ],
                  [
                    "5",
                    "Form the answer",
                    "Supported, with scope limited to five held-out cohorts",
                  ],
                ].map(([number, title, copy], index) => (
                  <div className="reasoning-step" key={number}>
                    <span>{index < 4 ? <Icon name="check" /> : number}</span>
                    <div>
                      <b>{title}</b>
                      <p>{copy}</p>
                    </div>
                    {index < 4 && <i />}
                  </div>
                ))}
              </div>
              <aside className="reasoning-evidence">
                <span className="section-kicker">EVIDENCE USED</span>
                <article>
                  <Tag tone="verification">PRIMARY</Tag>
                  <b>Figure 4b · Page 8</b>
                  <p>
                    “Latent alignment retains 94.2% of within-subject
                    performance…”
                  </p>
                  <small>Visual confidence 98%</small>
                </article>
                <article>
                  <Tag tone="neutral">CONTEXT</Tag>
                  <b>Methods · Page 5</b>
                  <p>Evaluation covers five held-out institutional cohorts.</p>
                  <small>Text confidence 96%</small>
                </article>
                <div>
                  <span>Reasoning summary</span>
                  <b>1,842 tokens · 2.2 sec</b>
                </div>
              </aside>
            </div>
            <p className="reasoning-privacy">
              <Icon name="shield" />
              Nexus shows an evidence-backed reasoning summary and decision
              trace. Private model internals are not exposed.
            </p>
          </div>
        )}
      </section>
    </div>
  )
}

export default function App() {
  const [view, setView] = useState<View>("home")
  const [telemetry, setTelemetry] = useState(false)
  const [overlay, setOverlay] = useState<Overlay | null>(null)
  const content = useMemo(() => {
    if (view === "home")
      return (
        <HomeView
          setView={setView}
          openOverlay={setOverlay}
          onTelemetry={() => setTelemetry(true)}
        />
      )
    if (view === "campus")
      return <CampusView setView={setView} openOverlay={setOverlay} />
    if (view === "vault") return <VaultView openOverlay={setOverlay} />
    if (view === "proof")
      return (
        <ProofView
          setView={setView}
          openOverlay={setOverlay}
          onTelemetry={() => setTelemetry(true)}
        />
      )
    return (
      <PodView
        setView={setView}
        openOverlay={setOverlay}
        onTelemetry={() => setTelemetry(true)}
      />
    )
  }, [view])
  return (
    <AppFrame
      view={view}
      setView={setView}
      onTelemetry={() => setTelemetry(true)}
      openOverlay={setOverlay}
    >
      {content}
      {telemetry && (
        <TelemetryDrawer
          onClose={() => setTelemetry(false)}
          openOverlay={(nextOverlay) => {
            setTelemetry(false)
            setOverlay(nextOverlay)
          }}
        />
      )}
      {overlay && (
        <ProductOverlay overlay={overlay} onClose={() => setOverlay(null)} />
      )}
    </AppFrame>
  )
}
