#!/usr/bin/env python3
"""
Update frontend/src/app/page.tsx to wire up all buttons, interactive states,
and navigation seamlessly between Home, Campus Discovery, Vault, Pod, Proposal Studio,
and overlays.
"""
from pathlib import Path

PAGE_PATH = Path("frontend/src/app/page.tsx")

def main():
    content = PAGE_PATH.read_text(encoding="utf-8")

    # 1. Update type View and mainNavKeys
    old_view_def = 'type View = "campus" | "vault" | "pod" | "proof"'
    new_view_def = """type View = "home" | "campus" | "vault" | "pod" | "proof"
const mainNavKeys: View[] = ["home", "vault", "pod", "proof"]"""
    assert old_view_def in content, "old_view_def not found"
    content = content.replace(old_view_def, new_view_def, 1)

    # 2. Update viewMeta keys
    old_view_meta = """const viewMeta: Record<View, {
  label: string
  icon: IconName
  subtitle: string
}> = {
  campus: {
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
}"""
    new_view_meta = """const viewMeta: Record<"home" | "vault" | "pod" | "proof", {
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
}"""
    assert old_view_meta in content, "old_view_meta not found"
    content = content.replace(old_view_meta, new_view_meta, 1)

    # 3. Update AppFrame navigation & buttons
    old_app_frame_nav = """        <button
          className="wordmark"
          onClick={() => setView("campus")}
          aria-label="Nexus home"
        >
          <NexusLogo />
        </button>
        <label className="global-search">
          <Icon name="search" size={17} />
          <input placeholder="Search people, projects, papers, or skills" />
        </label>
        <nav className="continuum" aria-label="Research continuum">
          {(Object.keys(viewMeta) as View[]).map((key) => (
            <button
              key={key}
              className={view === key ? "active" : ""}
              onClick={() => setView(key)}
            >
              <span className="continuum-icon">
                <Icon name={viewMeta[key].icon} size={16} />
              </span>
              <span className="continuum-copy">
                <b>{viewMeta[key].label}</b>
              </span>
            </button>
          ))}
        </nav>"""

    new_app_frame_nav = """        <button
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
        </nav>"""
    assert old_app_frame_nav in content, "old_app_frame_nav not found"
    content = content.replace(old_app_frame_nav, new_app_frame_nav, 1)

    # 4. Update Header Alerts & Me buttons
    old_alerts_me = """          <button
            className="header-nav-button notification"
            aria-label="Notifications"
          >
            <Icon name="bell" />
            <i />
            <span>Alerts</span>
          </button>
          <button className="me-button">
            <Avatar initials="AM" color="gold" active />
            <span>Me</span>
            <Icon name="chevron" size={11} />
          </button>"""

    new_alerts_me = """          <button
            className="header-nav-button notification"
            aria-label="Notifications"
            onClick={() => alert("Alerts:\\n• 3 new citations verified in Neural Commons pod\\n• Jordan Lee accepted your private match request\\n• NIH R21 deadline in 64 days")}
          >
            <Icon name="bell" />
            <i />
            <span>Alerts</span>
          </button>
          <button
            className="me-button"
            onClick={() => alert("Aria Malik (Logged in)\\nMS Computer Science, UC Berkeley\\nStatus: 3 protected ideas in Vault, 1 active Pod")}
          >
            <Avatar initials="AM" color="gold" active />
            <span>Me</span>
            <Icon name="chevron" size={11} />
          </button>"""
    assert old_alerts_me in content, "old_alerts_me not found"
    content = content.replace(old_alerts_me, new_alerts_me, 1)

    # 5. Update PodView with paper score wrapping, discussion reply interaction, and buttons
    old_pod_view_start = """function PodView({
  setView,
  openOverlay,
}: {
  setView: (view: View) => void
  openOverlay: (overlay: Overlay) => void
}) {
  const [activeMilestone, setActiveMilestone] = useState(2)
  const [paperTab, setPaperTab] = useState<"evidence" | "discussion">(
    "evidence",
  )
  const [pinned, setPinned] = useState(2)"""

    new_pod_view_start = """function PodView({
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
  }"""
    assert old_pod_view_start in content, "old_pod_view_start not found"
    content = content.replace(old_pod_view_start, new_pod_view_start, 1)

    # Pod presence buttons
    old_pod_presence_btns = """          <button className="icon-button">
            <Icon name="message" />
          </button>
          <button className="dark-button">
            <Icon name="users" /> Add teammate
          </button>"""

    new_pod_presence_btns = """          <button className="icon-button" onClick={onTelemetry} title="Pod discussion">
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
          </button>"""
    assert old_pod_presence_btns in content, "old_pod_presence_btns not found"
    content = content.replace(old_pod_presence_btns, new_pod_presence_btns, 1)

    # Pod milestone grant button
    old_grant_btn = """        <div className="milestone-heading">
          <span>GRANT PROGRESS</span>
          <button>
            NSF Smart & Connected Communities <Icon name="chevron" size={14} />
          </button>
        </div>"""
    new_grant_btn = """        <div className="milestone-heading">
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
        </div>"""
    assert old_grant_btn in content, "old_grant_btn not found"
    content = content.replace(old_grant_btn, new_grant_btn, 1)

    # Pod add paper button
    old_add_paper = """            <div className="panel-tools">
              <button className="icon-button">
                <Icon name="search" />
              </button>
              <button className="soft-button">
                <Icon name="plus" /> Add a paper
              </button>
            </div>"""
    new_add_paper = """            <div className="panel-tools">
              <button className="icon-button" onClick={() => setPaperTab("evidence")}>
                <Icon name="search" />
              </button>
              <button className="soft-button" onClick={() => openOverlay("project")}>
                <Icon name="plus" /> Add a paper
              </button>
            </div>"""
    assert old_add_paper in content, "old_add_paper not found"
    content = content.replace(old_add_paper, new_add_paper, 1)

    # Pod paper score wrapping
    old_paper_score = """                <article className="paper-row" key={paper.title}>
                  <div className="paper-score">
                    {paper.score}
                    <small>%</small>
                  </div>"""
    new_paper_score = """                <article className="paper-row" key={paper.title}>
                  <div className="paper-score" style={{ ["--score" as any]: paper.score }}>
                    <span>{paper.score}</span>
                    <small>%</small>
                  </div>"""
    assert old_paper_score in content, "old_paper_score not found"
    content = content.replace(old_paper_score, new_paper_score, 1)

    # Pod discussion list
    old_disc_list = """            <div className="discussion-list">
              <div>
                <Avatar initials="JL" color="blue" />
                <p>
                  <strong>Jon Lee</strong> Should the privacy bound be the
                  primary contribution, or supporting infrastructure?
                </p>
                <time>8 min</time>
              </div>
              <div>
                <Avatar initials="SR" color="teal" />
                <p>
                  <strong>Prof. Rao</strong> Primary. Tie it directly to Aim 2
                  and cite Zhang’s cross-site result.
                </p>
                <time>3 min</time>
              </div>
              <div className="reply-box">
                Write a reply…{" "}
                <button>
                  <Icon name="send" />
                </button>
              </div>
            </div>"""

    new_disc_list = """            <div className="discussion-list">
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
            </div>"""
    assert old_disc_list in content, "old_disc_list not found"
    content = content.replace(old_disc_list, new_disc_list, 1)

    # 6. Update VaultView certificate download & private match
    old_vault_start = """function VaultView({
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
  }"""

    new_vault_start = """function VaultView({
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
  }"""
    assert old_vault_start in content, "old_vault_start not found"
    content = content.replace(old_vault_start, new_vault_start, 1)

    old_cert_download_btn = """                <button className="soft-button">
                  <Icon name="download" /> Certificate
                </button>"""
    new_cert_download_btn = """                <button className="soft-button" onClick={downloadCertificate}>
                  <Icon name="download" /> Certificate
                </button>"""
    assert old_cert_download_btn in content, "old_cert_download_btn not found"
    content = content.replace(old_cert_download_btn, new_cert_download_btn, 1)

    old_match_btn = "<button>Request a private match</button>"
    new_match_btn = '<button onClick={() => openOverlay("reveal")}>Request a private match</button>'
    assert old_match_btn in content, "old_match_btn not found"
    content = content.replace(old_match_btn, new_match_btn, 1)

    # 7. Update CampusView with back to feed button, filters, and cards
    old_campus_start = """function CampusView({ setView }: { setView: (view: View) => void }) {
  const [accepted, setAccepted] = useState(false)
  const [query, setQuery] = useState("")
  const filtered = projects.filter((p) =>
    (p.title + p.body + p.dept).toLowerCase().includes(query.toLowerCase()),
  )
  return (
    <div className="view campus-view">"""

    new_campus_start = """function CampusView({
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
      </div>"""
    assert old_campus_start in content, "old_campus_start not found"
    content = content.replace(old_campus_start, new_campus_start, 1)

    # Filter pills in CampusView
    old_filter_pills = """        <button className="filter-pill active">
          All campus <span>1,284</span>
        </button>
        <button className="filter-pill">EECS</button>
        <button className="filter-pill">Neuroscience</button>
        <button className="filter-pill">Prototype</button>
        <button className="filter-pill">
          <Icon name="filter" /> Refine
        </button>"""

    new_filter_pills = """        {["All campus", "EECS", "Neuroscience", "Prototype"].map((pill) => (
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
        </button>"""
    assert old_filter_pills in content, "old_filter_pills not found"
    content = content.replace(old_filter_pills, new_filter_pills, 1)

    # View project button in campus cards
    old_view_project_btn = """                    <button>
                      View project <Icon name="arrow" size={15} />
                    </button>"""
    new_view_project_btn = """                    <button onClick={() => openOverlay("reveal")}>
                      View project <Icon name="arrow" size={15} />
                    </button>"""
    assert old_view_project_btn in content, "old_view_project_btn not found"
    content = content.replace(old_view_project_btn, new_view_project_btn, 1)

    # Explore knowledge graph button
    old_graph_glimpse = """          <button className="graph-glimpse">
            <span>
              <Icon name="graph" />
              <b>Explore knowledge graph</b>
              <small>13 cross-department gaps found</small>
            </span>
            <Icon name="arrow" />
          </button>"""
    new_graph_glimpse = """          <button className="graph-glimpse" onClick={() => openOverlay("graph")}>
            <span>
              <Icon name="graph" />
              <b>Explore knowledge graph</b>
              <small>13 cross-department gaps found</small>
            </span>
            <Icon name="arrow" />
          </button>"""
    assert old_graph_glimpse in content, "old_graph_glimpse not found"
    content = content.replace(old_graph_glimpse, new_graph_glimpse, 1)

    # 8. Update HomeView with full button wiring
    old_home_start = """function HomeView({
  setView,
  openOverlay,
}: {
  setView: (view: View) => void
  openOverlay: (overlay: Overlay) => void
}) {
  const [connected, setConnected] = useState(false)
  const [following, setFollowing] = useState(false)"""

    new_home_start = """function HomeView({
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
  }"""
    assert old_home_start in content, "old_home_start not found"
    content = content.replace(old_home_start, new_home_start, 1)

    # Home profile card buttons
    old_home_profile_btns = """              <button>View profile</button>
            </div>
            <div className="profile-stats">
              <button>
                <span>Project views</span>
                <b>184</b>
              </button>
              <button>
                <span>New matches</span>
                <b>12</b>
              </button>
            </div>"""

    new_home_profile_btns = """              <button onClick={() => alert("Aria Malik\\nMS Computer Science, UC Berkeley\\nSpecialization: Federated Learning & Neural Decoding")}>
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
            </div>"""
    assert old_home_profile_btns in content, "old_home_profile_btns not found"
    content = content.replace(old_home_profile_btns, new_home_profile_btns, 1)

    # Home availability edit button
    old_avail_btn = "<button>Edit availability</button>"
    new_avail_btn = '<button onClick={() => alert("Availability updated: Open to Capstone teams and Co-authoring.")}>Edit availability</button>'
    assert old_avail_btn in content, "old_avail_btn not found"
    content = content.replace(old_avail_btn, new_avail_btn, 1)

    # Home saved card
    old_saved_card = """          <section className="saved-card clean-card">
            <button>
              <Icon name="pin" />
              <span>
                <b>Saved research</b>
                <small>18 papers · 4 projects</small>
              </span>
            </button>"""
    new_saved_card = """          <section className="saved-card clean-card">
            <button onClick={() => setView("pod")}>
              <Icon name="pin" />
              <span>
                <b>Saved research</b>
                <small>18 papers · 4 projects</small>
              </span>
            </button>"""
    assert old_saved_card in content, "old_saved_card not found"
    content = content.replace(old_saved_card, new_saved_card, 1)

    # Home composer prompt button & find collaborator
    old_composer_prompt = """            <div>
              <Avatar initials="AM" color="gold" />
              <button>Share what you’re working on or looking for…</button>
            </div>
            <div className="share-actions">
              <button onClick={() => openOverlay("project")}>
                <Icon name="plus" />
                Post a project
              </button>
              <button>
                <Icon name="users" />
                Find a collaborator
              </button>"""

    new_composer_prompt = """            <div>
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
              </button>"""
    assert old_composer_prompt in content, "old_composer_prompt not found"
    content = content.replace(old_composer_prompt, new_composer_prompt, 1)

    # Home sort button
    old_feed_sort = """          <div className="feed-sort">
            <span />
            <button>
              Sort by: <b>Most relevant</b> <Icon name="chevron" size={12} />
            </button>
          </div>"""
    new_feed_sort = """          <div className="feed-sort">
            <span />
            <button
              onClick={() =>
                setSortOrder(sortOrder === "relevant" ? "recent" : "relevant")
              }
            >
              Sort by: <b>{sortOrder === "relevant" ? "Most relevant" : "Most recent"}</b>{" "}
              <Icon name="chevron" size={12} />
            </button>
          </div>"""
    assert old_feed_sort in content, "old_feed_sort not found"
    content = content.replace(old_feed_sort, new_feed_sort, 1)

    # Home ask question button
    old_ask_q = """              <button>
                <Icon name="message" /> Ask a question
              </button>"""
    new_ask_q = """              <button onClick={onTelemetry}>
                <Icon name="message" /> Ask a question
              </button>"""
    assert old_ask_q in content, "old_ask_q not found"
    content = content.replace(old_ask_q, new_ask_q, 1)

    # Home comment and share buttons
    old_comment_share = """              <button>
                <Icon name="message" /> Comment
              </button>
              <button>
                <Icon name="send" /> Share
              </button>"""
    new_comment_share = """              <button onClick={() => alert("Comment thread opened for Soft aerial sensors project. Maya was notified.")}>
                <Icon name="message" /> Comment
              </button>
              <button
                onClick={() => {
                  navigator.clipboard?.writeText(window.location.origin)
                  alert("Project link copied to clipboard!")
                }}
              >
                <Icon name="send" /> Share
              </button>"""
    assert old_comment_share in content, "old_comment_share not found"
    content = content.replace(old_comment_share, new_comment_share, 1)

    # Home people recommendations follow button
    old_people_follow = """                <button>
                  <Icon name="plus" size={14} /> Follow
                </button>
              </div>
            ))}
            <button className="see-all">
              See all suggestions <Icon name="arrow" />
            </button>"""
    new_people_follow = """                <button onClick={() => toggleFollowPerson(name)}>
                  <Icon name={followingPeople[name] ? "check" : "plus"} size={14} />{" "}
                  {followingPeople[name] ? "Following" : "Follow"}
                </button>
              </div>
            ))}
            <button className="see-all" onClick={() => setView("campus")}>
              See all suggestions <Icon name="arrow" />
            </button>"""
    assert old_people_follow in content, "old_people_follow not found"
    content = content.replace(old_people_follow, new_people_follow, 1)

    # Home funding card view opportunity button
    old_opp_btn = "<button>View opportunity</button>"
    new_opp_btn = '<button onClick={() => openOverlay("funding")}>View opportunity</button>'
    assert old_opp_btn in content, "old_opp_btn not found"
    content = content.replace(old_opp_btn, new_opp_btn, 1)

    # Home footer informative alerts
    old_home_footer = """          <footer className="home-footer">
            <button>About</button>
            <button>Privacy</button>
            <button>Trust & safety</button>
            <button>Help</button>
            <span>Nexus © 2025</span>
          </footer>"""
    new_home_footer = """          <footer className="home-footer">
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
          </footer>"""
    assert old_home_footer in content, "old_home_footer not found"
    content = content.replace(old_home_footer, new_home_footer, 1)

    # 9. Update ProofView props, back button, source tabs, and zoom controls
    old_proof_start = """function ProofView({
  openOverlay,
}: {
  openOverlay: (overlay: Overlay) => void
}) {
  const [claim, setClaim] = useState(0)
  const [verifying, setVerifying] = useState(false)
  const [verified, setVerified] = useState(false)
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
          <button className="icon-button">
            <Icon name="chevron" />
          </button>"""

    new_proof_start = """function ProofView({
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
          </button>"""
    assert old_proof_start in content, "old_proof_start not found"
    content = content.replace(old_proof_start, new_proof_start, 1)

    # ProofView discuss button
    old_proof_discuss = """          <button className="soft-button">
            <Icon name="message" /> Discuss
          </button>"""
    new_proof_discuss = """          <button className="soft-button" onClick={onTelemetry}>
            <Icon name="message" /> Discuss
          </button>"""
    assert old_proof_discuss in content, "old_proof_discuss not found"
    content = content.replace(old_proof_discuss, new_proof_discuss, 1)

    # ProofView source header buttons
    old_source_head_btns = """          <div className="source-header">
            <div>
              <span className="section-kicker">CLAIM EVIDENCE</span>
              <h2>What supports this claim</h2>
            </div>
            <div>
              <button className="icon-button">
                <Icon name="expand" />
              </button>
              <button className="icon-button">
                <Icon name="close" />
              </button>
            </div>
          </div>"""

    new_source_head_btns = """          <div className="source-header">
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
          </div>"""
    assert old_source_head_btns in content, "old_source_head_btns not found"
    content = content.replace(old_source_head_btns, new_source_head_btns, 1)

    # ProofView source tabs
    old_source_tabs = """          <div className="source-tabs">
            <button className="active">PDF source</button>
            <button>Extraction</button>
            <button>Audit trail</button>
          </div>"""
    new_source_tabs = """          <div className="source-tabs">
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
          </div>"""
    assert old_source_tabs in content, "old_source_tabs not found"
    content = content.replace(old_source_tabs, new_source_tabs, 1)

    # ProofView zoom tools
    old_zoom_tools = """            <div className="zoom-tools">
              <button>−</button>
              <span>118%</span>
              <button>+</button>
            </div>"""
    new_zoom_tools = """            <div className="zoom-tools">
              <button onClick={() => setZoom(Math.max(70, zoom - 10))}>−</button>
              <span>{zoom}%</span>
              <button onClick={() => setZoom(Math.min(180, zoom + 10))}>+</button>
            </div>"""
    assert old_zoom_tools in content, "old_zoom_tools not found"
    content = content.replace(old_zoom_tools, new_zoom_tools, 1)

    # 10. Update App export default
    old_app = """export default function App() {
  const [view, setView] = useState<View>("campus")
  const [telemetry, setTelemetry] = useState(false)
  const [overlay, setOverlay] = useState<Overlay | null>(null)
  const content = useMemo(() => {
    if (view === "campus")
      return <HomeView setView={setView} openOverlay={setOverlay} />
    if (view === "vault") return <VaultView openOverlay={setOverlay} />
    if (view === "proof") return <ProofView openOverlay={setOverlay} />
    return <PodView setView={setView} openOverlay={setOverlay} />
  }, [view])"""

    new_app = """export default function App() {
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
  }, [view])"""
    assert old_app in content, "old_app not found"
    content = content.replace(old_app, new_app, 1)

    # 11. Update overlays buttons (PeerReview, Conflict, Funding, Verify)
    # PeerReviewOverlay
    old_peer_btns = """            <div className="overlay-actions">
              <button className="soft-button">Share with pod</button>
              <button className="accent-button">Fix issues in proposal</button>
            </div>"""
    new_peer_btns = """            <div className="overlay-actions">
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
            </div>"""
    assert old_peer_btns in content, "old_peer_btns not found"
    content = content.replace(old_peer_btns, new_peer_btns, 1)

    # ConflictOverlay
    old_conflict_btn = "<button>Insert balanced claim</button>"
    new_conflict_btn = """<button
                onClick={() => {
                  alert("Balanced claim inserted into Section 2.1 of Proposal Studio!")
                  onClose()
                }}
              >
                Insert balanced claim
              </button>"""
    assert old_conflict_btn in content, "old_conflict_btn not found"
    content = content.replace(old_conflict_btn, new_conflict_btn, 1)

    # FundingOverlay
    old_funding_btns = """              <button className="accent-button">Link to Neural Commons</button>
              <button className="soft-button">Open solicitation</button>"""
    new_funding_btns = """              <button
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
              </button>"""
    assert old_funding_btns in content, "old_funding_btns not found"
    content = content.replace(old_funding_btns, new_funding_btns, 1)

    # VerifyOverlay receipt download
    old_verify_receipt_btn = """              <button className="accent-button">
                <Icon name="download" /> Download receipt
              </button>"""
    new_verify_receipt_btn = """              <button
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
              </button>"""
    assert old_verify_receipt_btn in content, "old_verify_receipt_btn not found"
    content = content.replace(old_verify_receipt_btn, new_verify_receipt_btn, 1)

    PAGE_PATH.write_text(content, encoding="utf-8")
    print(f"Successfully updated {PAGE_PATH} with all interactions, wiring, and views!")

if __name__ == "__main__":
    main()
