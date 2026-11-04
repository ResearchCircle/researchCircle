"use client"

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react"

export type View = "home" | "campus" | "vault" | "pod" | "proof"
export const mainNavKeys: View[] = ["home", "vault", "pod", "proof"]
export type Overlay =
  | "reveal"
  | "verify"
  | "graph"
  | "funding"
  | "project"
  | "peer-review"
  | "conflict"
  | "export"
  | "reasoning"

export type IconName =
  | "arrow"
  | "bell"
  | "book"
  | "brain"
  | "check"
  | "chevron"
  | "clock"
  | "close"
  | "code"
  | "copy"
  | "download"
  | "expand"
  | "eye"
  | "filter"
  | "fingerprint"
  | "graph"
  | "home"
  | "lock"
  | "message"
  | "more"
  | "pin"
  | "plus"
  | "search"
  | "seal"
  | "send"
  | "shield"
  | "spark"
  | "user"
  | "users"
  | "verified"

const iconPaths: Record<IconName, ReactNode> = {
  arrow: <path d="M5 12h14M14 7l5 5-5 5" />,
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
  code: <path d="m8 9-3 3 3 3M16 9l3 3-3 3M14 5l-4 14" />,
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
  expand: <path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5" />,
  eye: (
    <>
      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  filter: <path d="M4 6h16M7 12h10M10 18h4" />,
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
      <circle cx="5" cy="12" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="19" cy="12" r="1.5" fill="currentColor" stroke="none" />
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

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
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

export function NexusLogo() {
  return (
    <svg className="nexus-logo" viewBox="0 0 160 36" role="img" aria-label="Nexus">
      <g fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
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

export function Avatar({
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

export function Tag({
  children,
  tone = "neutral",
}: {
  children: ReactNode
  tone?: string
}) {
  return <span className={`tag tag-${tone}`}>{children}</span>
}

export function MetricRing({
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

export function Toast({ message }: { message: string }) {
  return (
    <div className="nexus-toast">
      <Icon name="check" size={16} />
      <span>{message}</span>
    </div>
  )
}

export const viewMeta: Record<View, {
  label: string
  icon: IconName
  subtitle: string
}> = {
  home: {
    label: "Home",
    icon: "home",
    subtitle: "Your research feed",
  },
  campus: {
    label: "Campus",
    icon: "search",
    subtitle: "Explore campus projects",
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

// --- COMMON DATA CATALOGS ---

export const initialProjects = [
  {
    stage: "PROTOTYPE",
    color: "blue",
    degree: "PhD",
    dept: "EECS · Helen Wills Neuroscience",
    title: "Cross-subject latent alignment for non-invasive EEG decoding",
    body: "We train subject-specific adapters into a shared geometry. Looking for teams with 64+ channel longitudinal datasets to benchmark calibration speed.",
    offer: ["Optimal transport", "Adapter weights", "PyTorch codebase"],
    need: ["Longitudinal EEG", "Clinical sleep data", "Compute grant"],
  },
  {
    stage: "DISCOVERY",
    color: "violet",
    degree: "Postdoc",
    dept: "Robotics and Autonomous Systems",
    title: "Low-overhead soft sensors for continuous micro-strain monitoring",
    body: "Testing multi-material conductive elastomers under cyclic load. Seeking signal processing collaborators to filter drift and motion artifacts in real time.",
    offer: ["Cleanroom fabrication", "Sensor hardware", "Mechanical testing"],
    need: ["Drift modeling", "Embedded DSP", "Field trial partner"],
  },
  {
    stage: "PRE-PRINT",
    color: "teal",
    degree: "Faculty Lab",
    dept: "Computational Precision Health",
    title: "Privacy-preserving cohort comparison without centralizing records",
    body: "Developing differential privacy bounds for federated clinical analytics. We need clinical partners with multi-site IRB approval to pilot evaluation rounds.",
    offer: ["DP audit tooling", "Formal verification", "Pre-print draft"],
    need: ["Clinical partner", "Multi-site IRB", "Hospital dataset"],
  },
  {
    stage: "PROTOTYPE",
    color: "orange",
    degree: "Lab",
    dept: "Bioengineering & Neurotechnology",
    title: "Synchronized multimodal telemetry for freely moving subjects",
    body: "Combining high-density optical tracking with sub-millivolt surface biopotentials. Need validation against commercial wireless acquisition rigs.",
    offer: ["Optical hardware", "Firmware stack", "Telemetry sync"],
    need: ["Biopotential rig", "Benchmarking lab", "Validation trials"],
  },
]

export const initialPapers = [
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
  {
    title: "Differentially Private Parameter Aggregation in Healthcare Fleets",
    authors: "Kairouz, McMahan et al. · Nature Digital Medicine 2024",
    score: 87,
    verdict: "Supports",
    person: "MK",
    color: "blue",
  },
  {
    title: "Riemannian Geometries for Manifold Alignment of Biopotentials",
    authors: "Barachant, Bonnet et al. · IEEE TBME 2023",
    score: 85,
    verdict: "Methodology",
    person: "JL",
    color: "violet",
  },
  {
    title: "Membership Inference Vulnerabilities in Federated Latent Embeddings",
    authors: "Shokri, Carlini et al. · IEEE S&P 2024",
    score: 84,
    verdict: "Contradicts",
    person: "AM",
    color: "gold",
  },
]

export const searchCatalog = [
  { type: "person", title: "Jordan Lee", subtitle: "PhD · Neuroscience · Helen Wills Institute", meta: "0.4 miles away", view: "campus" },
  { type: "person", title: "Maya Rodriguez", subtitle: "PhD Candidate · Robotics & Autonomous Systems", meta: "Active now", view: "campus" },
  { type: "person", title: "Sam Chen", subtitle: "Computational Biology · Python & Genomics", meta: "Suggested peer", view: "campus" },
  { type: "project", title: "Soft aerial sensors for forest canopy health", subtitle: "Maya Rodriguez · Prototype stage", meta: "Robotics", view: "home" },
  { type: "project", title: "Cross-subject latent alignment for non-invasive EEG", subtitle: "EECS · Helen Wills Neuroscience", meta: "94% Match", view: "campus" },
  { type: "paper", title: "Federated Foundation Models for Neural Decoding", subtitle: "Nature Machine Intelligence · Zhang et al.", meta: "96% Verified", view: "proof" },
  { type: "paper", title: "Cross-Subject EEG Alignment via Optimal Transport", subtitle: "NeurIPS 2024 · Li, Verma et al.", meta: "91% Method", view: "proof" },
  { type: "skill", title: "Federated Representation Learning", subtitle: "Privacy-preserving multi-site optimization", meta: "12 Projects", view: "graph" },
  { type: "skill", title: "Mobile EEG Lab Access (128-channel)", subtitle: "High-density mobile neurotelemetry", meta: "Jordan Lee", view: "campus" },
]

// --- MODAL DIALOGS ---

export function ProfileModal({ onClose, onNavigate }: { onClose: () => void; onNavigate: (v: View) => void }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>Researcher Profile</h3>
          <button className="icon-button" onClick={onClose}><Icon name="close" /></button>
        </div>
        <div className="modal-body">
          <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
            <Avatar initials="AM" color="gold" active />
            <div>
              <h2 style={{ margin: "0 0 4px", fontSize: 20 }}>Aria Malik</h2>
              <p style={{ margin: 0, color: "var(--muted)", fontSize: 13 }}>MS Computer Science · UC Berkeley</p>
              <small style={{ color: "var(--teal)", fontWeight: 600 }}>Hardware Sealed Key: 0x9f2a...7c01</small>
            </div>
          </div>
          <div>
            <strong>Research Focus</strong>
            <p style={{ margin: "6px 0 0", fontSize: 13, color: "#455350", lineHeight: 1.5 }}>
              Federated learning algorithms, privacy-preserving neural latent alignment, and cross-subject calibration
              reduction for non-invasive brain-computer interfaces.
            </p>
          </div>
          <div>
            <strong>Protected Ideas in Private Vault (3)</strong>
            <ul style={{ margin: "6px 0 0", paddingLeft: 20, fontSize: 13, color: "var(--muted)", lineHeight: 1.6 }}>
              <li>NX-8492: Federated adaptation layer for latent EEG alignment (Sealed on-chain)</li>
              <li>NX-7110: Orthogonal subspace projection with bounded DP noise (Drafting)</li>
              <li>NX-6084: Dual opt-in identity discovery protocol (Peer verified)</li>
            </ul>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Tag tone="offer">Federated learning</Tag>
            <Tag tone="offer">Neural decoding</Tag>
            <Tag tone="offer">Differential privacy</Tag>
            <Tag tone="need">Needs: Longitudinal EEG</Tag>
          </div>
        </div>
        <div className="modal-foot">
          <button className="soft-button" onClick={() => { onNavigate("vault"); onClose(); }}>Open Private Vault</button>
          <button className="accent-button" onClick={onClose}>Done</button>
        </div>
      </div>
    </div>
  )
}

export function ViewsModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>Project Views Analytics</h3>
          <button className="icon-button" onClick={onClose}><Icon name="close" /></button>
        </div>
        <div className="modal-body">
          <div style={{ display: "flex", justifyContent: "space-between", padding: "14px 18px", background: "#f6faf8", borderRadius: 10 }}>
            <div>
              <span style={{ fontSize: 11, color: "var(--teal)", fontWeight: 600 }}>TOTAL PROFILE IMPRESSIONS</span>
              <h2 style={{ margin: "4px 0 0", fontSize: 28, color: "var(--ink)" }}>184</h2>
            </div>
            <div style={{ textAlign: "right" }}>
              <span style={{ fontSize: 11, color: "var(--muted)" }}>LAST 7 DAYS</span>
              <p style={{ margin: "8px 0 0", color: "var(--green)", fontWeight: 600, fontSize: 14 }}>+42% vs last week</p>
            </div>
          </div>
          <div>
            <strong>Top Viewing Institutions & Labs</strong>
            <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                ["Helen Wills Neuroscience Institute", "UC Berkeley", "68 views"],
                ["Stanford Neurosciences Institute", "Stanford University", "47 views"],
                ["Computer Science & AI Lab (CSAIL)", "MIT", "39 views"],
                ["Center for Neural Basis of Cognition", "CMU", "30 views"],
              ].map(([lab, uni, count]) => (
                <div key={lab} style={{ display: "flex", justifyContent: "space-between", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: 8, fontSize: 12 }}>
                  <div>
                    <strong>{lab}</strong>
                    <span style={{ display: "block", color: "var(--muted)", fontSize: 11 }}>{uni}</span>
                  </div>
                  <b style={{ color: "var(--teal)", alignSelf: "center" }}>{count}</b>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="modal-foot">
          <button className="accent-button" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}

export function AvailabilityModal({ onClose, onSave }: { onClose: () => void; onSave: (msg: string) => void }) {
  const [capstone, setCapstone] = useState(true)
  const [coauthor, setCoauthor] = useState(true)
  const [mentor, setMentor] = useState(false)
  const [equipment, setEquipment] = useState(false)

  const handleSave = () => {
    onSave("Availability settings updated successfully!")
    onClose()
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>Edit Collaboration Availability</h3>
          <button className="icon-button" onClick={onClose}><Icon name="close" /></button>
        </div>
        <div className="modal-body">
          <p style={{ margin: 0, fontSize: 13, color: "var(--muted)" }}>
            Configure how other researchers and faculty across campus discover your availability status.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", border: "1px solid var(--line)", borderRadius: 8, cursor: "pointer" }}>
              <input type="checkbox" checked={capstone} onChange={(e) => setCapstone(e.target.checked)} />
              <div>
                <strong>Capstone & Senior Project Teams</strong>
                <span style={{ display: "block", fontSize: 11, color: "var(--muted)" }}>Open to joining multi-disciplinary capstone projects</span>
              </div>
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", border: "1px solid var(--line)", borderRadius: 8, cursor: "pointer" }}>
              <input type="checkbox" checked={coauthor} onChange={(e) => setCoauthor(e.target.checked)} />
              <div>
                <strong>Co-Authoring & Grant Drafting</strong>
                <span style={{ display: "block", fontSize: 11, color: "var(--muted)" }}>Available for NSF/NIH grant writing and conference submissions</span>
              </div>
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", border: "1px solid var(--line)", borderRadius: 8, cursor: "pointer" }}>
              <input type="checkbox" checked={mentor} onChange={(e) => setMentor(e.target.checked)} />
              <div>
                <strong>Undergraduate Mentorship</strong>
                <span style={{ display: "block", fontSize: 11, color: "var(--muted)" }}>Open to mentoring junior researchers in ML/EEG</span>
              </div>
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", border: "1px solid var(--line)", borderRadius: 8, cursor: "pointer" }}>
              <input type="checkbox" checked={equipment} onChange={(e) => setEquipment(e.target.checked)} />
              <div>
                <strong>Shared Lab Equipment & Compute Exchange</strong>
                <span style={{ display: "block", fontSize: 11, color: "var(--muted)" }}>Open to sharing GPU cluster time for wet lab access</span>
              </div>
            </label>
          </div>
        </div>
        <div className="modal-foot">
          <button className="soft-button" onClick={onClose}>Cancel</button>
          <button className="accent-button" onClick={handleSave}>Save Preferences</button>
        </div>
      </div>
    </div>
  )
}

export function SavedResearchModal({ onClose, onNavigate }: { onClose: () => void; onNavigate: (v: View) => void }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>Saved Research & Bookmarks</h3>
          <button className="icon-button" onClick={onClose}><Icon name="close" /></button>
        </div>
        <div className="modal-body">
          <div style={{ display: "flex", gap: 8 }}>
            <Tag tone="verification">18 Papers</Tag>
            <Tag tone="stage">4 Projects</Tag>
          </div>
          <div>
            <strong>Bookmarked Papers</strong>
            <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 8 }}>
              {initialPapers.slice(0, 3).map((paper) => (
                <div key={paper.title} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", border: "1px solid var(--line)", borderRadius: 8 }}>
                  <div>
                    <h4 style={{ margin: "0 0 2px", fontSize: 13 }}>{paper.title}</h4>
                    <span style={{ fontSize: 11, color: "var(--muted)" }}>{paper.authors}</span>
                  </div>
                  <button className="soft-button" onClick={() => { onNavigate("proof"); onClose(); }} style={{ height: 32, fontSize: 11 }}>
                    Inspect
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="modal-foot">
          <button className="soft-button" onClick={() => { onNavigate("pod"); onClose(); }}>View Evidence Board</button>
          <button className="accent-button" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}

export function PostComposerModal({ onClose, onPublish }: { onClose: () => void; onPublish: (post: any) => void }) {
  const [title, setTitle] = useState("")
  const [body, setBody] = useState("")
  const [dept, setDept] = useState("EECS · AI Research")
  const [stage, setStage] = useState("PROTOTYPE")
  const [offer, setOffer] = useState("Federated learning, PyTorch")
  const [need, setNeed] = useState("EEG dataset, Clinical trials")

  const handlePublish = () => {
    if (!title.trim() && !body.trim()) return
    onPublish({
      author: "Aria Malik",
      dept: "MSCS · " + dept,
      title: title.trim() || "Collaborative Neuro-Engineering Initiative",
      body: body.trim() || "Looking for collaborators to expand cross-site validation.",
      stage,
      offer: offer.split(",").map((s) => s.trim()).filter(Boolean),
      need: need.split(",").map((s) => s.trim()).filter(Boolean),
      time: "Just now",
    })
    onClose()
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>Share with Campus Research Network</h3>
          <button className="icon-button" onClick={onClose}><Icon name="close" /></button>
        </div>
        <div className="modal-body">
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>PROJECT TITLE</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Real-time neural representation alignment under latency constraints"
              style={{ width: "100%", height: 38, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 12px", fontSize: 13 }}
            />
          </div>
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>DESCRIPTION & OBJECTIVES</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Describe what you are working on, the core methodology, and what kind of collaborator or data you need..."
              style={{ width: "100%", height: 80, border: "1px solid var(--line-dark)", borderRadius: 8, padding: 10, fontSize: 13, resize: "none" }}
            />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>STAGE</label>
              <select value={stage} onChange={(e) => setStage(e.target.value)} style={{ width: "100%", height: 38, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 8px", fontSize: 12 }}>
                <option value="DISCOVERY">Discovery & Ideation</option>
                <option value="PROTOTYPE">Prototype & Benchmarking</option>
                <option value="PRE-PRINT">Pre-Print & Grant Drafting</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>DEPARTMENT</label>
              <input value={dept} onChange={(e) => setDept(e.target.value)} style={{ width: "100%", height: 38, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 10px", fontSize: 12 }} />
            </div>
          </div>
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>WHAT YOU CAN OFFER (comma-separated)</label>
            <input value={offer} onChange={(e) => setOffer(e.target.value)} style={{ width: "100%", height: 36, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 10px", fontSize: 12 }} />
          </div>
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>WHAT YOU NEED (comma-separated)</label>
            <input value={need} onChange={(e) => setNeed(e.target.value)} style={{ width: "100%", height: 36, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 10px", fontSize: 12 }} />
          </div>
        </div>
        <div className="modal-foot">
          <button className="soft-button" onClick={onClose}>Cancel</button>
          <button className="accent-button" onClick={handlePublish}>Publish to Feed</button>
        </div>
      </div>
    </div>
  )
}

export function AddTeammateModal({ onClose, onInvite }: { onClose: () => void; onInvite: (email: string) => void }) {
  const [email, setEmail] = useState("collaborator@berkeley.edu")
  const [role, setRole] = useState("Researcher")

  const handleSubmit = () => {
    const targetEmail = email.trim() || "collaborator@berkeley.edu"
    onInvite(targetEmail)
    onClose()
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>Add Teammate to Neural Commons</h3>
          <button className="icon-button" onClick={onClose}><Icon name="close" /></button>
        </div>
        <div className="modal-body">
          <p style={{ margin: 0, fontSize: 13, color: "var(--muted)" }}>
            Invite a collaborator to access the Evidence Board, co-write the NSF proposal, and audit citation trails.
          </p>
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>INSTITUTIONAL EMAIL</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. collaborator@berkeley.edu"
              style={{ width: "100%", height: 38, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 12px", fontSize: 13 }}
            />
          </div>
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>PROJECT ROLE</label>
            <select value={role} onChange={(e) => setRole(e.target.value)} style={{ width: "100%", height: 38, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 10px", fontSize: 12 }}>
              <option value="Co-PI">Co-Principal Investigator</option>
              <option value="Researcher">Senior Researcher / Postdoc</option>
              <option value="Graduate">Graduate Student Researcher</option>
              <option value="Reviewer">Faculty Peer Reviewer (Read Only)</option>
            </select>
          </div>
          <div style={{ padding: 12, background: "#f8faf8", borderRadius: 8, border: "1px solid var(--line)" }}>
            <span style={{ fontSize: 11, color: "var(--teal)", fontWeight: 600 }}>SHAREABLE POD INVITE LINK</span>
            <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
              <input readOnly value="https://nexus.research/pod/neural-commons/invite?token=nx91a4" style={{ flex: 1, height: 32, fontSize: 11, background: "white", border: "1px solid var(--line)", borderRadius: 6, padding: "0 8px" }} />
              <button
                className="soft-button"
                style={{ height: 32, fontSize: 11 }}
                onClick={() => {
                  navigator.clipboard?.writeText("https://nexus.research/pod/neural-commons/invite?token=nx91a4").catch(() => {})
                  onInvite("link-copied")
                }}
              >
                Copy
              </button>
            </div>
          </div>
        </div>
        <div className="modal-foot">
          <button className="soft-button" onClick={onClose}>Cancel</button>
          <button className="accent-button" onClick={handleSubmit}>Send Invitation</button>
        </div>
      </div>
    </div>
  )
}

export function AddPaperModal({ onClose, onAdd }: { onClose: () => void; onAdd: (paper: any) => void }) {
  const [doi, setDoi] = useState("10.1038/s42256-024-00812-x")
  const [title, setTitle] = useState("Cross-Subject EEG Alignment via Optimal Transport")
  const [authors, setAuthors] = useState("Li, Verma et al. · NeurIPS 2024")
  const [verdict, setVerdict] = useState("Supports")

  const handleSubmit = () => {
    if (!title.trim()) return
    onAdd({
      title: title.trim(),
      authors: authors.trim() || "Peer Review 2024",
      score: 93,
      verdict,
      person: "AM",
      color: "gold",
    })
    onClose()
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>Add Research Paper to Evidence Board</h3>
          <button className="icon-button" onClick={onClose}><Icon name="close" /></button>
        </div>
        <div className="modal-body">
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>DOI OR ARXIV IDENTIFIER</label>
            <input
              value={doi}
              onChange={(e) => setDoi(e.target.value)}
              placeholder="e.g. 10.1038/s42256-024-00812-x or arXiv:2403.11284"
              style={{ width: "100%", height: 38, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 12px", fontSize: 13 }}
            />
          </div>
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>PAPER TITLE</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{ width: "100%", height: 38, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 12px", fontSize: 13 }}
            />
          </div>
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>AUTHORS & PUBLICATION</label>
            <input
              value={authors}
              onChange={(e) => setAuthors(e.target.value)}
              style={{ width: "100%", height: 38, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 12px", fontSize: 13 }}
            />
          </div>
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", display: "block", marginBottom: 4 }}>VERDICT ON PROPOSAL HYPOTHESIS</label>
            <select value={verdict} onChange={(e) => setVerdict(e.target.value)} style={{ width: "100%", height: 38, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 10px", fontSize: 12 }}>
              <option value="Supports">Supports (Validates aim or hypothesis)</option>
              <option value="Methodology">Methodology (Provides benchmark/algorithm)</option>
              <option value="Contradicts">Contradicts (Challenges privacy or bounds)</option>
            </select>
          </div>
        </div>
        <div className="modal-foot">
          <button className="soft-button" onClick={onClose}>Cancel</button>
          <button className="accent-button" onClick={handleSubmit}>Index & Add Paper</button>
        </div>
      </div>
    </div>
  )
}

export function AboutCharterModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>Nexus Architecture & Privacy Charter</h3>
          <button className="icon-button" onClick={onClose}><Icon name="close" /></button>
        </div>
        <div className="modal-body">
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <span style={{ width: 36, height: 36, borderRadius: "50%", background: "var(--teal-soft)", color: "var(--teal)", display: "grid", placeItems: "center" }}>
              <Icon name="shield" size={20} />
            </span>
            <div>
              <strong style={{ fontSize: 14 }}>Client-Cryptographic Priority Guarantees</strong>
              <span style={{ display: "block", fontSize: 11, color: "var(--muted)" }}>Zero plaintext transmission of confidential hypotheses</span>
            </div>
          </div>
          <p style={{ margin: 0, fontSize: 13, color: "#3a4a46", lineHeight: 1.6 }}>
            Nexus was engineered to solve the fundamental friction in academic discovery: the fear of idea theft versus
            the urgent need for multi-disciplinary collaborators. Every draft sealed in your Private Vault generates an
            immutable Merkle leaf on-device before non-confidential abstractions are computed.
          </p>
          <div style={{ padding: 12, background: "#f8faf8", borderRadius: 8, border: "1px solid var(--line)", fontSize: 12, lineHeight: 1.5 }}>
            <b style={{ color: "var(--ink)", display: "block", marginBottom: 4 }}>Dual Opt-In Cryptographic Reveal:</b>
            Collaborator identities and project specifics are cryptographically redacted until both parties independently
            review the vector match and execute mutual consent.
          </div>
        </div>
        <div className="modal-foot">
          <button className="accent-button" onClick={onClose}>I Understand</button>
        </div>
      </div>
    </div>
  )
}

// --- APP FRAME WITH SEARCH, ALERTS & ME POPOVERS ---

export function AppFrame({
  view,
  setView,
  children,
  onTelemetry,
  openOverlay,
  showToast,
  openProfile,
  openCharter,
}: {
  view: View
  setView: (view: View) => void
  children: ReactNode
  onTelemetry: () => void
  openOverlay: (overlay: Overlay) => void
  showToast: (msg: string) => void
  openProfile: () => void
  openCharter: () => void
}) {
  const [toolsOpen, setToolsOpen] = useState(false)
  const [alertsOpen, setAlertsOpen] = useState(false)
  const [meOpen, setMeOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  const [notifications, setNotifications] = useState([
    {
      id: "1",
      title: "Citation Verified in §2.1",
      desc: "Maya confirmed SAM 3.1 polygon match for Figure 4b in Nature MI paper.",
      time: "2 min ago",
      unread: true,
      actionView: "proof" as View,
    },
    {
      id: "2",
      title: "Mutual Match Request Accepted",
      desc: "Jordan Lee (Helen Wills EEG Lab) accepted your private connection.",
      time: "18 min ago",
      unread: true,
      actionOverlay: "reveal" as Overlay,
    },
    {
      id: "3",
      title: "NIH R21 Funding Window Open",
      desc: "Smart & Connected Health solicitation matches 8 of 10 pod capabilities.",
      time: "2h ago",
      unread: true,
      actionOverlay: "funding" as Overlay,
    },
  ])

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })))
    showToast("All notifications marked as read")
  }

  const handleNotificationClick = (notif: (typeof notifications)[0]) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === notif.id ? { ...n, unread: false } : n)),
    )
    setAlertsOpen(false)
    if (notif.actionView) setView(notif.actionView)
    if (notif.actionOverlay) openOverlay(notif.actionOverlay)
  }

  const filteredSearch = useMemo(() => {
    if (!searchQuery.trim()) return []
    const q = searchQuery.toLowerCase()
    return searchCatalog.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        item.subtitle.toLowerCase().includes(q) ||
        item.meta.toLowerCase().includes(q),
    )
  }, [searchQuery])

  return (
    <div className="app-shell" onClick={() => { setAlertsOpen(false); setMeOpen(false); setToolsOpen(false); }}>
      <header className="global-header" onClick={(e) => e.stopPropagation()}>
        <button
          className="wordmark"
          onClick={() => setView("home")}
          aria-label="Nexus home"
        >
          <NexusLogo />
        </button>

        <div className="search-wrapper">
          <label className="global-search">
            <Icon name="search" size={17} />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search people, projects, papers, or skills..."
            />
            {searchQuery && (
              <button
                style={{ border: 0, background: "none", cursor: "pointer", color: "var(--muted)", padding: 4 }}
                onClick={() => setSearchQuery("")}
              >
                <Icon name="close" size={14} />
              </button>
            )}
          </label>

          {searchQuery.trim() && (
            <div className="search-dropdown">
              {filteredSearch.length === 0 ? (
                <div style={{ padding: 16, textAlign: "center", color: "var(--muted)", fontSize: 13 }}>
                  No matching items found for "{searchQuery}".
                </div>
              ) : (
                filteredSearch.map((item, idx) => (
                  <button
                    key={idx}
                    className="search-item"
                    onClick={() => {
                      setSearchQuery("")
                      if (item.view === "proof") setView("proof")
                      else if (item.view === "vault") setView("vault")
                      else if (item.view === "pod") setView("pod")
                      else if (item.view === "graph") openOverlay("graph")
                      else setView("campus")
                    }}
                  >
                    <div className="search-item-info">
                      <strong>{item.title}</strong>
                      <span>{item.subtitle}</span>
                    </div>
                    <span className="search-item-badge">{item.meta}</span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        <nav className="continuum" aria-label="Research continuum">
          {mainNavKeys.map((key) => (
            <button
              key={key}
              className={
                view === key || (key === "home" && view === "campus") ? "active" : ""
              }
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
        </nav>

        <div className="header-actions">
          <div className="tools-anchor">
            <button
              className={`header-nav-button ${toolsOpen ? "active" : ""}`}
              onClick={() => {
                setToolsOpen(!toolsOpen)
                setAlertsOpen(false)
                setMeOpen(false)
              }}
            >
              <Icon name="graph" size={18} />
              <span>Tools</span>
            </button>
            {toolsOpen && (
              <div className="tools-menu">
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
                    <small>1,284 campus researchers matched</small>
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
                    <small>Explore topics, authors, and gaps</small>
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

          <button className="header-nav-button" onClick={() => onTelemetry()}>
            <Icon name="message" size={18} />
            <span>Messages</span>
          </button>

          <div className="popover-container">
            <button
              className={`header-nav-button notification ${alertsOpen ? "active" : ""}`}
              aria-label="Notifications"
              onClick={() => {
                setAlertsOpen(!alertsOpen)
                setToolsOpen(false)
                setMeOpen(false)
              }}
            >
              <Icon name="bell" />
              {notifications.some((n) => n.unread) && <i />}
              <span>Alerts</span>
            </button>

            {alertsOpen && (
              <div className="alerts-popover">
                <div className="popover-header">
                  <h3>Notifications ({notifications.filter((n) => n.unread).length})</h3>
                  <button onClick={markAllRead}>Mark all read</button>
                </div>
                <div className="popover-list">
                  {notifications.map((notif) => (
                    <button
                      key={notif.id}
                      className={`notification-row ${notif.unread ? "unread" : ""}`}
                      onClick={() => handleNotificationClick(notif)}
                    >
                      {notif.unread && <span className="notification-dot" />}
                      <div className="notification-content">
                        <strong>{notif.title}</strong>
                        <p>{notif.desc}</p>
                        <time>{notif.time}</time>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="popover-container">
            <button
              className={`me-button ${meOpen ? "active" : ""}`}
              onClick={() => {
                setMeOpen(!meOpen)
                setToolsOpen(false)
                setAlertsOpen(false)
              }}
            >
              <Avatar initials="AM" color="gold" active />
              <span>Me</span>
              <Icon name="chevron" size={11} />
            </button>

            {meOpen && (
              <div className="me-popover">
                <div className="me-card-top">
                  <Avatar initials="AM" color="gold" active />
                  <div className="me-card-meta">
                    <h4>Aria Malik</h4>
                    <p>MS Computer Science · UC Berkeley</p>
                    <small>Hardware Key: 0x9f2a...7c01</small>
                  </div>
                </div>
                <div className="me-menu-actions">
                  <button
                    className="me-menu-item"
                    onClick={() => {
                      setMeOpen(false)
                      openProfile()
                    }}
                  >
                    <Icon name="user" size={16} />
                    <span>View full researcher profile</span>
                  </button>
                  <button
                    className="me-menu-item"
                    onClick={() => {
                      setMeOpen(false)
                      setView("vault")
                    }}
                  >
                    <Icon name="shield" size={16} />
                    <span>Manage protected vault ideas</span>
                  </button>
                  <button
                    className="me-menu-item"
                    onClick={() => {
                      setMeOpen(false)
                      setView("pod")
                    }}
                  >
                    <Icon name="users" size={16} />
                    <span>Active pod: Neural Commons</span>
                  </button>
                  <button
                    className="me-menu-item"
                    onClick={() => {
                      setMeOpen(false)
                      openCharter()
                    }}
                  >
                    <Icon name="lock" size={16} />
                    <span>Privacy charter & hardware keys</span>
                  </button>
                  <button
                    className="me-menu-item"
                    onClick={() => {
                      setMeOpen(false)
                      showToast("Session synced with Berkeley institutional directory")
                    }}
                  >
                    <Icon name="check" size={16} />
                    <span>Directory sync status: Healthy</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>
      <main>{children}</main>
    </div>
  )
}

// --- POD VIEW & WORKSPACE ---

export function PodView({
  setView,
  openOverlay,
  onTelemetry,
  showToast,
  openAddTeammate,
  openAddPaper,
}: {
  setView: (view: View) => void
  openOverlay: (overlay: Overlay) => void
  onTelemetry?: () => void
  showToast: (msg: string) => void
  openAddTeammate: () => void
  openAddPaper: () => void
}) {
  const [activeMilestone, setActiveMilestone] = useState(2)
  const [paperTab, setPaperTab] = useState<"evidence" | "discussion">("evidence")
  const [pinned, setPinned] = useState(2)
  const [activeGrant, setActiveGrant] = useState("NSF Smart & Connected Communities")
  const [showAllSources, setShowAllSources] = useState(false)
  const [activePaperMenu, setActivePaperMenu] = useState<number | null>(null)
  const [activityFilter, setActivityFilter] = useState("All activity")
  const [activityMenuOpen, setActivityMenuOpen] = useState(false)

  const [papersList, setPapersList] = useState(initialPapers)

  const [discussions, setDiscussions] = useState([
    {
      initials: "JL",
      color: "blue",
      author: "Jon Lee",
      text: "Should the privacy bound be the primary contribution, or supporting infrastructure?",
      time: "8 min ago",
    },
    {
      initials: "SR",
      color: "teal",
      author: "Prof. Rao",
      text: "Primary. Tie it directly to Aim 2 and cite Zhang’s cross-site result.",
      time: "3 min ago",
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
    showToast("Reply posted to Neural Commons pod discussion")
  }

  const displayedPapers = showAllSources ? papersList : papersList.slice(0, 3)

  return (
    <div className="view pod-view" onClick={() => { setActivePaperMenu(null); setActivityMenuOpen(false); }}>
      <section className="pod-identity">
        <div>
          <div className="eyebrow">
            <span className="live-dot" /> NEURAL COMMONS · 4 MEMBERS
          </div>
          <h1>Good morning, Aria.</h1>
          <p>Your pod is moving toward the internal methods review on Friday.</p>
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
          <button className="icon-button" onClick={onTelemetry} title="Open pod messages">
            <Icon name="message" />
          </button>
          <button className="dark-button" onClick={openAddTeammate}>
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
          <p>Nexus found the source passages. Confirm the matches and your readiness score will move to 80%.</p>
        </div>
        <div className="focus-meta">
          <span><b>12 min</b> estimated</span>
          <span><b>5</b> claims</span>
        </div>
        <button className="accent-button" onClick={() => setView("proof")}>
          Review claims <Icon name="arrow" />
        </button>
        <button className="focus-audit-button" onClick={() => openOverlay("peer-review")}>
          Run pre-flight audit
        </button>
      </section>

      <section className="milestone-band">
        <div className="milestone-heading">
          <span>GRANT PROGRESS</span>
          <button
            onClick={(e) => {
              e.stopPropagation()
              setActiveGrant((curr) =>
                curr === "NSF Smart & Connected Communities"
                  ? "NIH R21 Exploratory Research"
                  : curr === "NIH R21 Exploratory Research"
                  ? "DARPA Young Faculty Award"
                  : "NSF Smart & Connected Communities"
              )
              showToast("Switched target grant solicitation")
            }}
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
                className={`${i < activeMilestone ? "complete" : ""} ${i === activeMilestone ? "current" : ""}`}
                onClick={() => {
                  setActiveMilestone(i)
                  showToast(`Milestone ${i + 1}: ${item} selected`)
                }}
              >
                <span>{i < activeMilestone ? <Icon name="check" size={14} /> : `0${i + 1}`}</span>
                <b>{item}</b>
                <small>
                  {i < activeMilestone ? "Complete" : i === activeMilestone ? "7 of 12 tasks" : i === 3 ? "Due Oct 18" : "Not started"}
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
                  Evidence board <span>{papersList.length}</span>
                </button>
                <button
                  className={paperTab === "discussion" ? "active" : ""}
                  onClick={() => setPaperTab("discussion")}
                >
                  Discussion <span>{discussions.length}</span>
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
              <button className="soft-button" onClick={openAddPaper}>
                <Icon name="plus" /> Add a paper
              </button>
            </div>
          </div>

          {paperTab === "evidence" ? (
            <div className="paper-list">
              {displayedPapers.map((paper, i) => (
                <article className="paper-row" key={paper.title}>
                  <div className="paper-score" style={{ ["--score" as any]: paper.score }}>
                    <span>{paper.score}</span>
                    <small>%</small>
                  </div>
                  <div className="paper-copy">
                    <div className="paper-tags">
                      <Tag tone={paper.verdict.toLowerCase()}>{paper.verdict}</Tag>
                      <span>FOUNDATIONAL</span>
                    </div>
                    <h3>{paper.title}</h3>
                    <p>{paper.authors}</p>
                    <div className="paper-meta">
                      <Avatar initials={paper.person} color={paper.color} />
                      <span>Added by {paper.person === "MK" ? "Maya" : paper.person === "JL" ? "Jon" : "Aria"}</span>
                    </div>
                  </div>
                  <button
                    className={`pin-button ${i < pinned ? "pinned" : ""}`}
                    onClick={() => {
                      if (paper.verdict === "Contradicts") {
                        openOverlay("conflict")
                      } else {
                        setPinned(i < pinned ? i : i + 1)
                        showToast(i < pinned ? "Unpinned citation from Section 2.1" : "Citation pinned to Section 2.1 Technical Narrative")
                      }
                    }}
                  >
                    <Icon name="pin" /> {i < pinned ? "Pinned to §2.1" : paper.verdict === "Contradicts" ? "Inspect conflict" : "Pin citation"}
                  </button>

                  <div className="options-anchor">
                    <button
                      className="icon-button"
                      onClick={(e) => {
                        e.stopPropagation()
                        setActivePaperMenu(activePaperMenu === i ? null : i)
                      }}
                    >
                      <Icon name="more" />
                    </button>
                    {activePaperMenu === i && (
                      <div className="options-dropdown">
                        <button
                          className="options-item"
                          onClick={() => {
                            setActivePaperMenu(null)
                            setView("proof")
                          }}
                        >
                          <Icon name="book" size={14} /> Open in Studio
                        </button>
                        <button
                          className="options-item"
                          onClick={() => {
                            setActivePaperMenu(null)
                            try {
                              const bib = `@article{zhang2024neural,\n  title={${paper.title}},\n  author={${paper.authors}},\n  year={2024}\n}`
                              const blob = new Blob([bib], { type: "text/plain" })
                              const url = URL.createObjectURL(blob)
                              const a = document.createElement("a")
                              a.href = url
                              a.download = "citation.bib"
                              document.body.appendChild(a)
                              a.click()
                              document.body.removeChild(a)
                              URL.revokeObjectURL(url)
                            } catch {}
                            showToast("Downloaded BibTeX entry")
                          }}
                        >
                          <Icon name="download" size={14} /> Download BibTeX
                        </button>
                        <button
                          className="options-item"
                          onClick={() => {
                            setActivePaperMenu(null)
                            navigator.clipboard?.writeText(paper.title).catch(() => {})
                            showToast("Citation title copied to clipboard")
                          }}
                        >
                          <Icon name="copy" size={14} /> Copy citation text
                        </button>
                      </div>
                    )}
                  </div>
                </article>
              ))}

              <button
                className="text-button full"
                onClick={() => setShowAllSources(!showAllSources)}
              >
                {showAllSources ? "Show top foundational sources" : `View all ${papersList.length} sources`} <Icon name="arrow" />
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
            <div className="options-anchor">
              <button
                className="icon-button"
                onClick={(e) => {
                  e.stopPropagation()
                  setActivityMenuOpen(!activityMenuOpen)
                }}
              >
                <Icon name="filter" />
              </button>
              {activityMenuOpen && (
                <div className="options-dropdown">
                  {["All activity", "Citations only", "Model updates", "Comments"].map((f) => (
                    <button
                      key={f}
                      className="options-item"
                      onClick={() => {
                        setActivityFilter(f)
                        setActivityMenuOpen(false)
                        showToast(`Filtered activity: ${f}`)
                      }}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div className="activity-list">
            <div>
              <span className="activity-icon green">
                <Icon name="check" />
              </span>
              <p>
                <b>Maya</b> verified a citation in <strong>Methodology §2.1</strong>
                <small>2 min ago</small>
              </p>
            </div>
            <div>
              <span className="activity-icon violet">
                <Icon name="spark" />
              </span>
              <p>
                <b>Nexus AI</b> drafted <strong>Broader Impacts</strong> summary
                <small>14 min ago</small>
              </p>
            </div>
            <div>
              <span className="activity-icon blue">
                <Icon name="book" />
              </span>
              <p>
                <b>Jon</b> added 3 papers to <strong>Evidence board</strong>
                <small>1h ago</small>
              </p>
            </div>
            <div>
              <span className="activity-icon gold">
                <Icon name="message" />
              </span>
              <p>
                <b>Prof. Rao</b> commented on <strong>Aim 2 feasibility</strong>
                <small>3h ago</small>
              </p>
            </div>
          </div>
          <div className="deadline-card">
            <div>
              <span>INTERNAL DEADLINE</span>
              <strong>Methods section complete</strong>
              <small>Aim 2 grounding required</small>
            </div>
            <b>3<small>d</small></b>
          </div>
        </aside>

        <div className="studio-launch panel">
          <div className="studio-visual">
            <div className="document-mini">
              <span>SECTION 2.1 — CROSS-SITE LATENT ALIGNMENT</span>
              <i className="short" />
              <i className="medium" />
              <mark>94.2% within-subject retention across 5 cohorts</mark>
              <i />
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
              Jon and Maya are in the draft now. Nexus keeps each claim linked to the exact passage, figure, or equation that supports it.
            </p>
            <div style={{ display: "flex", gap: 8 }}>
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

// --- VAULT VIEW & WORKBENCH ---

export function VaultView({
  openOverlay,
  showToast,
}: {
  openOverlay: (overlay: Overlay) => void
  showToast: (msg: string) => void
}) {
  const [step, setStep] = useState<"compose" | "hashing" | "sealed">("compose")
  const [audience, setAudience] = useState<"Stranger" | "Peer student" | "Professor">("Stranger")
  const [text, setText] = useState(
    "A federated adaptation layer can align latent neural representations across institutions without centralizing subject-level EEG data.",
  )
  const [vaultMenuOpen, setVaultMenuOpen] = useState(false)

  const seal = () => {
    setStep("hashing")
    window.setTimeout(() => {
      setStep("sealed")
      showToast("Priority proof generated & sealed on-chain!")
    }, 1400)
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
    showToast("Downloaded Certificate #NX-8492 JSON")
  }

  return (
    <div className="view vault-view" onClick={() => setVaultMenuOpen(false)}>
      <section className="vault-intro">
        <div>
          <div className="eyebrow">
            <Icon name="lock" size={14} /> PRIVATE UNTIL YOU CHOOSE TO SHARE
          </div>
          <h1>
            Prove you had the idea<br />
            <em>without revealing it.</em>
          </h1>
          <p>
            Create a timestamped proof on this device. Then publish a safe summary that reveals only what collaborators need to know.
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
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <Tag tone="verification">
                <Icon name="shield" size={13} /> Stays on this device
              </Tag>
              <div className="options-anchor">
                <button
                  className="icon-button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setVaultMenuOpen(!vaultMenuOpen)
                  }}
                >
                  <Icon name="more" />
                </button>
                {vaultMenuOpen && (
                  <div className="options-dropdown">
                    <button
                      className="options-item"
                      onClick={() => {
                        setVaultMenuOpen(false)
                        setText("")
                        setStep("compose")
                        showToast("Cleared draft")
                      }}
                    >
                      <Icon name="close" size={14} /> Reset draft
                    </button>
                    <button
                      className="options-item"
                      onClick={() => {
                        setVaultMenuOpen(false)
                        openOverlay("verify")
                      }}
                    >
                      <Icon name="verified" size={14} /> Open verification ledger
                    </button>
                  </div>
                )}
              </div>
            </div>
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

        <aside className={`certificate panel ${step === "sealed" ? "issued" : ""}`}>
          <div className="certificate-seal">
            <Icon name="seal" size={40} />
          </div>
          <span>OFFICIAL NEXUS RECORD</span>
          <h2>Proof of Priority</h2>
          <p>
            This certificate verifies that an undisclosed research artifact existed at the time below.
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
              <dd>{step === "sealed" ? "09 Oct 2025 · 14:32:18 UTC" : "Pending seal"}</dd>
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
              Publicly verifiable<br />
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
            Nexus drafted a summary that explains what you can offer and what help you need. Sensitive details stay out, and nothing posts until you approve it.
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
              {(["Stranger", "Peer student", "Professor"] as const).map((aud) => (
                <button
                  key={aud}
                  className={audience === aud ? "active" : ""}
                  onClick={() => {
                    setAudience(aud)
                    showToast(`Audience preview switched to: ${aud}`)
                  }}
                >
                  {aud}
                </button>
              ))}
            </div>
          </div>
          <div className="project-preview">
            <div className="preview-head">
              <span className="project-glyph">
                <Icon name="spark" />
              </span>
              <div>
                <Tag tone="stage">PROTOTYPE</Tag>
                <small>{audience === "Stranger" ? "UC Berkeley Researcher" : "Aria Malik · EECS & Neuroscience"}</small>
              </div>
            </div>
            <h3>
              {audience === "Stranger"
                ? "Privacy-preserving adaptation for distributed neural telemetry"
                : "Federated adaptation layer for cross-institution EEG decoding"}
            </h3>
            <p>
              {audience === "Stranger"
                ? "Looking for collaborators with multi-subject sensor data to validate a low-overhead transfer method. Core architecture remains sealed."
                : "We train localized adapters against non-invasive EEG distributions to retain cross-subject accuracy without pooling protected patient data."}
            </p>
            <div className="offer-need">
              <span>OFFERS</span>
              <Tag tone="offer">Federated learning</Tag>
              <Tag tone="offer">Adapter weights</Tag>
            </div>
            <div className="offer-need">
              <span>NEEDS</span>
              <Tag tone="need">Longitudinal EEG</Tag>
              <Tag tone="need">Clinical sleep cohorts</Tag>
            </div>
            <div className="blurred-owner">
              <Icon name="lock" size={16} />
              <span>
                <b>{audience === "Stranger" ? "Identity hidden until mutual match" : "Verified Berkeley Student"}</b>
                Double opt-in privacy guarantee
              </span>
              <button onClick={() => openOverlay("reveal")}>Request a private match</button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

// --- CAMPUS DISCOVERY VIEW ---

export function CampusView({
  setView,
  openOverlay,
  showToast,
  openProfile,
}: {
  setView: (view: View) => void
  openOverlay: (overlay: Overlay) => void
  showToast: (msg: string) => void
  openProfile: () => void
}) {
  const [accepted, setAccepted] = useState(false)
  const [query, setQuery] = useState("")
  const [activePill, setActivePill] = useState("All campus")
  const [sortOrder, setSortOrder] = useState<"best" | "recent" | "views">("best")

  const filtered = useMemo(() => {
    return initialProjects.filter((p) => {
      const matchesQuery = (p.title + p.body + p.dept).toLowerCase().includes(query.toLowerCase())
      if (activePill === "All campus") return matchesQuery
      if (activePill === "EECS") return matchesQuery && p.dept.includes("EECS")
      if (activePill === "Neuroscience") return matchesQuery && p.dept.includes("Neuroscience")
      if (activePill === "Prototype") return matchesQuery && p.stage.toUpperCase() === "PROTOTYPE"
      return matchesQuery
    })
  }, [query, activePill])

  return (
    <div className="view campus-view">
      <div style={{ marginBottom: 16 }}>
        <button
          className="text-button"
          onClick={() => setView("home")}
          style={{ display: "inline-flex", alignItems: "center", gap: 6, fontWeight: 600, fontSize: 13 }}
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
            Find the people and projects<br />
            <em>that move your work forward.</em>
          </h1>
          <p>Search work happening now—not just what was published last year.</p>
        </div>
        <div className="campus-profile">
          <Avatar initials="AM" color="gold" active />
          <div>
            <span>YOUR MATCH PROFILE</span>
            <strong>Aria Malik · MSCS</strong>
            <small>Representation learning · Federated systems · EEG</small>
          </div>
          <button onClick={openProfile} title="View full profile">
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
            onClick={() => {
              setActivePill(pill)
              showToast(`Filtered by: ${pill}`)
            }}
          >
            {pill} {pill === "All campus" && <span>1,284</span>}
          </button>
        ))}
        <button
          className="filter-pill"
          onClick={() => {
            openOverlay("graph")
            showToast("Opening Knowledge Graph Gap Explorer")
          }}
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
            <button
              onClick={() => {
                setSortOrder((curr) => (curr === "best" ? "recent" : curr === "recent" ? "views" : "best"))
                showToast(`Sorted by: ${sortOrder === "best" ? "Most recent" : sortOrder === "recent" ? "Most viewed" : "Best match"}`)
              }}
            >
              {sortOrder === "best" ? "Best match first" : sortOrder === "recent" ? "Most recent first" : "Most viewed first"}{" "}
              <Icon name="chevron" size={14} />
            </button>
          </div>
          <div className="project-grid">
            {filtered.map((project, i) => (
              <article className="project-card" key={project.title}>
                <div className={`project-art art-${project.color}`}>
                  <span>{String(i + 1).padStart(2, "0")}</span>
                  <Icon
                    name={i === 0 ? "shield" : i === 1 ? "spark" : i === 2 ? "brain" : "graph"}
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
                      <Tag tone="offer" key={x}>{x}</Tag>
                    ))}
                  </div>
                  <div className="offer-need">
                    <span>NEEDS</span>
                    {project.need.map((x) => (
                      <Tag tone="need" key={x}>{x}</Tag>
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
              They operate a <strong>128-channel mobile EEG facility</strong> and need your expertise in{" "}
              <strong>federated representation learning</strong> to compare cohorts without pooling protected data.
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
              onClick={() => {
                setAccepted(!accepted)
                showToast(accepted ? "Private interest withdrawn" : "Private interest sent to Helen Wills lab!")
              }}
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
              <Icon name="lock" size={12} /> Identity and work reveal only after both accept
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

// --- HOME VIEW (LINKEDIN-STYLE RESEARCH NETWORK) ---

export function HomeView({
  setView,
  openOverlay,
  onTelemetry,
  showToast,
  openProfile,
  openViews,
  openAvailability,
  openSaved,
  openComposer,
  openCharter,
}: {
  setView: (view: View) => void
  openOverlay: (overlay: Overlay) => void
  onTelemetry: (prompt?: string) => void
  showToast: (msg: string) => void
  openProfile: () => void
  openViews: () => void
  openAvailability: () => void
  openSaved: () => void
  openComposer: () => void
  openCharter: () => void
}) {
  const [connected, setConnected] = useState(false)
  const [followingProject, setFollowingProject] = useState(false)
  const [sortOrder, setSortOrder] = useState<"relevant" | "recent">("relevant")
  const [followingPeople, setFollowingPeople] = useState<Record<string, boolean>>({})

  // Dropdown states
  const [matchMenuOpen, setMatchMenuOpen] = useState(false)
  const [projectMenuOpen, setProjectMenuOpen] = useState(false)
  const [peopleMenuOpen, setPeopleMenuOpen] = useState(false)

  // Comments state
  const [commentsOpen, setCommentsOpen] = useState(false)
  const [commentsList, setCommentsList] = useState([
    { author: "Dr. Elena Rostova", text: "Are you planning to test resilience against fungal spores during rainy season?" },
    { author: "Maya Rodriguez", text: "Yes! Aim 3 specifically benchmarks hydrophobic silicone skins against spore penetration." },
  ])
  const [commentInput, setCommentInput] = useState("")

  const addComment = () => {
    if (!commentInput.trim()) return
    setCommentsList((prev) => [...prev, { author: "Aria Malik", text: commentInput.trim() }])
    setCommentInput("")
    showToast("Comment added to Maya's project thread")
  }

  const toggleFollowPerson = (name: string) => {
    setFollowingPeople((prev) => {
      const next = !prev[name]
      showToast(next ? `Now following ${name}` : `Unfollowed ${name}`)
      return { ...prev, [name]: next }
    })
  }

  return (
    <div
      className="home-view"
      onClick={() => {
        setMatchMenuOpen(false)
        setProjectMenuOpen(false)
        setPeopleMenuOpen(false)
      }}
    >
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
              <small>Federated learning, neural decoding, and privacy-preserving AI</small>
              <button onClick={openProfile}>View profile</button>
            </div>
            <div className="profile-stats">
              <button onClick={openViews}>
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
            <button onClick={openAvailability}>Edit availability</button>
          </section>

          <section className="saved-card clean-card">
            <button onClick={openSaved}>
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
              <button onClick={openComposer}>
                Share what you’re working on or looking for…
              </button>
            </div>
            <div className="share-actions">
              <button onClick={openComposer}>
                <Icon name="plus" /> Post a project
              </button>
              <button onClick={() => setView("campus")}>
                <Icon name="users" /> Find a collaborator
              </button>
              <button onClick={() => setView("vault")}>
                <Icon name="shield" /> Protect an idea
              </button>
            </div>
          </div>

          <div className="feed-sort">
            <span />
            <button
              onClick={() => {
                const nextSort = sortOrder === "relevant" ? "recent" : "relevant"
                setSortOrder(nextSort)
                showToast(`Feed sorted by: ${nextSort === "relevant" ? "Most relevant" : "Most recent"}`)
              }}
            >
              Sort by: <b>{sortOrder === "relevant" ? "Most relevant" : "Most recent"}</b>{" "}
              <Icon name="chevron" size={12} />
            </button>
          </div>

          {/* Collaborator Match Card */}
          <article className="feed-card clean-card match-post">
            <header className="feed-card-header">
              <span className="feed-source-icon">
                <Icon name="spark" />
              </span>
              <div>
                <strong>Nexus match</strong>
                <span>Recommended because of your research needs</span>
              </div>
              <div className="options-anchor">
                <button
                  className="icon-button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setMatchMenuOpen(!matchMenuOpen)
                  }}
                >
                  <Icon name="more" />
                </button>
                {matchMenuOpen && (
                  <div className="options-dropdown">
                    <button
                      className="options-item"
                      onClick={() => {
                        setMatchMenuOpen(false)
                        showToast("Saved Jordan Lee's match to your shortlist")
                      }}
                    >
                      <Icon name="pin" size={14} /> Save match
                    </button>
                    <button
                      className="options-item"
                      onClick={() => {
                        setMatchMenuOpen(false)
                        navigator.clipboard?.writeText("https://nexus.research/profile/jordan-lee").catch(() => {})
                        showToast("Profile link copied")
                      }}
                    >
                      <Icon name="copy" size={14} /> Share profile
                    </button>
                    <button
                      className="options-item"
                      onClick={() => {
                        setMatchMenuOpen(false)
                        showToast("Feedback noted: will adjust match weighting")
                      }}
                    >
                      <Icon name="close" size={14} /> Not interested
                    </button>
                  </div>
                )}
              </div>
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
                Jordan runs a mobile EEG lab and is looking for a collaborator with federated learning experience. You’re looking for longitudinal EEG access.
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
                onClick={() => {
                  if (connected) {
                    openOverlay("reveal")
                  } else {
                    setConnected(true)
                    showToast("Private interest sent to Jordan Lee! Awaiting mutual reveal.")
                  }
                }}
              >
                <Icon name={connected ? "check" : "users"} />
                {connected ? "Review connection" : "Connect privately"}
              </button>
              <button onClick={() => onTelemetry("Question for Jordan Lee regarding 128-channel mobile EEG lab calibration protocols:")}>
                <Icon name="message" /> Ask a question
              </button>
              <small>Profiles reveal only after both people accept</small>
            </footer>
          </article>

          {/* Active Project Card */}
          <article className="feed-card clean-card project-post">
            <header className="feed-card-header">
              <Avatar initials="MR" color="violet" active />
              <div>
                <strong>Maya Rodriguez</strong>
                <span>PhD Candidate · Robotics · Posted a project · 2h</span>
              </div>
              <div className="options-anchor">
                <button
                  className="icon-button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setProjectMenuOpen(!projectMenuOpen)
                  }}
                >
                  <Icon name="more" />
                </button>
                {projectMenuOpen && (
                  <div className="options-dropdown">
                    <button
                      className="options-item"
                      onClick={() => {
                        setProjectMenuOpen(false)
                        navigator.clipboard?.writeText("https://nexus.research/project/soft-aerial-sensors").catch(() => {})
                        showToast("Project link copied to clipboard")
                      }}
                    >
                      <Icon name="copy" size={14} /> Copy link
                    </button>
                    <button
                      className="options-item"
                      onClick={() => {
                        setProjectMenuOpen(false)
                        showToast("Bookmarked project to Saved Research")
                      }}
                    >
                      <Icon name="pin" size={14} /> Bookmark project
                    </button>
                  </div>
                )}
              </div>
            </header>
            <div className="project-post-copy">
              <p>We’re starting a cross-department project on biodegradable aerial sensors for forest canopy health.</p>
              <div className="project-post-panel">
                <span className="project-post-art">
                  <Icon name="spark" size={36} />
                </span>
                <div>
                  <Tag tone="stage">PROTOTYPE</Tag>
                  <h2>Soft aerial sensors for forest canopy health</h2>
                  <p>Looking for plant pathology expertise to help validate early stress indicators from field trials.</p>
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
                className={followingProject ? "connected" : ""}
                onClick={() => {
                  const next = !followingProject
                  setFollowingProject(next)
                  showToast(next ? "Following Maya's project updates" : "Unfollowed project")
                }}
              >
                <Icon name={followingProject ? "check" : "plus"} />
                {followingProject ? "Following" : "Follow project"}
              </button>
              <button onClick={() => setCommentsOpen(!commentsOpen)}>
                <Icon name="message" /> Comment ({commentsList.length})
              </button>
              <button
                onClick={() => {
                  try {
                    navigator.clipboard?.writeText(typeof window !== "undefined" ? window.location.origin + "/project/soft-aerial-sensors" : "").catch(() => {})
                  } catch {}
                  showToast("Project link copied to clipboard!")
                }}
              >
                <Icon name="send" /> Share
              </button>
            </footer>

            {commentsOpen && (
              <div className="comment-thread">
                {commentsList.map((c, idx) => (
                  <div key={idx} className="comment-item">
                    <Avatar initials={c.author.split(" ").map((n) => n[0]).join("")} color="teal" />
                    <div>
                      <strong>{c.author}</strong>
                      <p>{c.text}</p>
                    </div>
                  </div>
                ))}
                <div className="comment-composer">
                  <input
                    value={commentInput}
                    onChange={(e) => setCommentInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addComment()}
                    placeholder="Write a comment or suggest a resource..."
                  />
                  <button onClick={addComment}>Post</button>
                </div>
              </div>
            )}
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
              <div className="options-anchor">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setPeopleMenuOpen(!peopleMenuOpen)
                  }}
                >
                  <Icon name="more" />
                </button>
                {peopleMenuOpen && (
                  <div className="options-dropdown">
                    <button
                      className="options-item"
                      onClick={() => {
                        setPeopleMenuOpen(false)
                        showToast("Suggestions refreshed")
                      }}
                    >
                      <Icon name="spark" size={14} /> Refresh list
                    </button>
                    <button
                      className="options-item"
                      onClick={() => {
                        setPeopleMenuOpen(false)
                        setView("campus")
                      }}
                    >
                      <Icon name="users" size={14} /> View all campus
                    </button>
                  </div>
                )}
              </div>
            </div>
            {[
              ["SC", "blue", "Sam Chen", "Computational biology", "Python · Genomics"],
              ["NP", "teal", "Nina Patel", "Clinical neuroscience", "EEG · fMRI"],
              ["EO", "violet", "Eli Okafor", "Privacy and security", "DP · Formal methods"],
            ].map(([initials, color, name, role, skills]) => (
              <div className="person-suggestion" key={name}>
                <Avatar initials={initials} color={color} />
                <span>
                  <b>{name}</b>
                  <small>{role}</small>
                  <em>{skills}</em>
                </span>
                <button onClick={() => toggleFollowPerson(name)}>
                  <Icon name={followingPeople[name] ? "check" : "plus"} size={14} />
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
            <button onClick={openCharter}>About</button>
            <button onClick={openCharter}>Privacy</button>
            <button onClick={openCharter}>Trust & safety</button>
            <button onClick={openCharter}>Help</button>
            <span>Nexus © 2025</span>
          </footer>
        </aside>
      </div>
    </div>
  )
}

// --- PROPOSAL AND PIXEL-TO-PROOF STUDIO ---

export function ProofView({
  setView,
  openOverlay,
  onTelemetry,
  showToast,
}: {
  setView: (view: View) => void
  openOverlay: (overlay: Overlay) => void
  onTelemetry: (prompt?: string) => void
  showToast: (msg: string) => void
}) {
  const [claim, setClaim] = useState(0)
  const [verifying, setVerifying] = useState(false)
  const [verified, setVerified] = useState(false)
  const [zoom, setZoom] = useState(118)
  const [sourceTab, setSourceTab] = useState<"pdf" | "extraction" | "audit">("pdf")
  const [expandedSource, setExpandedSource] = useState(false)

  // Formatting state
  const [boldActive, setBoldActive] = useState(false)
  const [italicActive, setItalicActive] = useState(false)
  const [formatStyle, setFormatStyle] = useState("Body Text")
  const [formatMenuOpen, setFormatMenuOpen] = useState(false)
  const [toolbarMenuOpen, setToolbarMenuOpen] = useState(false)

  // AI suggestion state
  const [aiAccepted, setAiAccepted] = useState(false)
  const [aiDismissed, setAiDismissed] = useState(false)

  const verify = () => {
    setVerifying(true)
    setVerified(false)
    window.setTimeout(() => {
      setVerifying(false)
      setVerified(true)
      showToast("Source checked: 0 contradictions found across 5 held-out cohorts")
    }, 2200)
  }

  const downloadBibtex = () => {
    const bib = `@article{zhang2024federated,\n  title={Federated Foundation Models for Privacy-Preserving Neural Decoding},\n  author={Zhang, Wei and Chen, Sam and Lee, Jon},\n  journal={Nature Machine Intelligence},\n  volume={6},\n  pages={312--324},\n  year={2024},\n  doi={10.1038/s42256-024-00812-x}\n}`
    const blob = new Blob([bib], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "zhang2024_neural_decoding.bib"
    a.click()
    URL.revokeObjectURL(url)
    showToast("Downloaded BibTeX entry for Zhang et al. (2024)")
  }

  return (
    <div
      className="proof-view"
      onClick={() => {
        setFormatMenuOpen(false)
        setToolbarMenuOpen(false)
      }}
    >
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
          <button className="soft-button" onClick={() => onTelemetry("Explain why the differential privacy bound is critical in Aim 2:")}>
            <Icon name="message" /> Discuss
          </button>
          <button className="dark-button" onClick={() => openOverlay("export")}>
            Export <Icon name="chevron" size={14} />
          </button>
        </div>
      </header>

      <div className={`proof-layout ${expandedSource ? "expanded-source" : ""}`}>
        <section className="editor-pane">
          <div className="editor-toolbar">
            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <div className="options-anchor">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setFormatMenuOpen(!formatMenuOpen)
                  }}
                >
                  {formatStyle} <Icon name="chevron" size={12} />
                </button>
                {formatMenuOpen && (
                  <div className="options-dropdown">
                    {["Body Text", "Heading 1", "Heading 2", "Code Block", "Equation"].map((style) => (
                      <button
                        key={style}
                        className="options-item"
                        onClick={() => {
                          setFormatStyle(style)
                          setFormatMenuOpen(false)
                          showToast(`Applied format: ${style}`)
                        }}
                      >
                        {style}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                className={boldActive ? "active-toolbar-btn" : ""}
                style={{ fontWeight: boldActive ? 700 : 400 }}
                onClick={() => {
                  setBoldActive(!boldActive)
                  showToast(boldActive ? "Bold disabled" : "Bold enabled")
                }}
              >
                <b>B</b>
              </button>

              <button
                className={italicActive ? "active-toolbar-btn" : ""}
                style={{ fontStyle: italicActive ? "italic" : "normal" }}
                onClick={() => {
                  setItalicActive(!italicActive)
                  showToast(italicActive ? "Italic disabled" : "Italic enabled")
                }}
              >
                <i>I</i>
              </button>

              <button
                onClick={() => {
                  setFormatStyle("Heading 2")
                  showToast("Formatted selection as Heading 2")
                }}
              >
                H₂
              </button>

              <button
                onClick={() => {
                  setFormatStyle("Equation")
                  showToast("Switched to LaTeX Equation Mode")
                }}
              >
                <Icon name="code" />
              </button>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span className="ai-working">
                <i /> Nexus active
              </span>
              <div className="options-anchor">
                <button
                  className="icon-button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setToolbarMenuOpen(!toolbarMenuOpen)
                  }}
                >
                  <Icon name="more" />
                </button>
                {toolbarMenuOpen && (
                  <div className="options-dropdown">
                    <button
                      className="options-item"
                      onClick={() => {
                        setToolbarMenuOpen(false)
                        showToast("Word count: 1,420 words · 18 citations")
                      }}
                    >
                      <Icon name="book" size={14} /> Document statistics
                    </button>
                    <button
                      className="options-item"
                      onClick={() => {
                        setToolbarMenuOpen(false)
                        openOverlay("peer-review")
                      }}
                    >
                      <Icon name="verified" size={14} /> Run pre-flight audit
                    </button>
                    <button
                      className="options-item"
                      onClick={() => {
                        setToolbarMenuOpen(false)
                        openOverlay("export")
                      }}
                    >
                      <Icon name="download" size={14} /> Export LaTeX package
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="document">
            <div className="doc-meta">
              <span>PROJECT DESCRIPTION</span>
              <span>4 / 15 PAGES</span>
            </div>
            <h1>2. Technical Approach</h1>
            <p>
              Our central premise is that institution-specific neural representations can be aligned without transferring
              protected subject-level data. We propose a three-part system that couples private local adaptation with a
              globally shared latent reference.
            </p>
            <h2>2.1 Cross-site latent alignment</h2>
            <p>
              Each participating institution trains an adapter against its local EEG distribution. Only clipped, noised
              parameter deltas leave the institutional boundary.
            </p>

            <p
              className={`audited-claim ${claim === 0 ? "selected" : ""}`}
              onClick={() => {
                setClaim(0)
                setVerified(false)
                showToast("Selected Claim 1: Zhang et al. (Figure 4b)")
              }}
            >
              Recent cross-subject alignment methods retain{" "}
              <mark>94.2% of within-subject decoding accuracy</mark> while reducing calibration requirements by 61%.<sup>12</sup>
              <span className="claim-badge">
                <Icon name="verified" size={13} /> FIG 4B
              </span>
            </p>

            <div className="equation">
              z<sub>i</sub> = A<sub>k</sub> f<sub>θ</sub>(x<sub>i</sub>) + ε, &nbsp; ε ∼ N(0, σ²I)<span>(1)</span>
            </div>

            <p
              className={`audited-claim ${claim === 1 ? "selected" : ""}`}
              onClick={() => {
                setClaim(1)
                setVerified(false)
                showToast("Selected Claim 2: Dwork et al. (Equation 3)")
              }}
            >
              This formulation preserves the geometry needed for downstream decoding while satisfying an{" "}
              <mark>(ε, δ)-differential privacy bound</mark> at every communication round.<sup>7</sup>
              <span className="claim-badge">
                <Icon name="verified" size={13} /> EQ 3
              </span>
            </p>

            {aiAccepted && (
              <p style={{ background: "#edf7f4", padding: "10px 14px", borderLeft: "3px solid var(--teal)", borderRadius: 4, margin: "14px 0" }}>
                <b>Integrated Suggestion:</b> Unlike conventional federated averaging, our alignment objective treats inter-site
                variance as a first-class signal rather than optimization noise, ensuring that clinical EEG drift between
                hospital recording setups is resolved without relaxing the privacy bound.
              </p>
            )}

            {!aiDismissed && !aiAccepted && (
              <div className="ai-suggestion">
                <div>
                  <Icon name="spark" />
                  <span>
                    <b>Nexus suggestion</b> Explain why this privacy limit matters in a clinical setting before introducing Aim 2.
                  </span>
                </div>
                <p>
                  Unlike conventional federated averaging, our alignment objective treats inter-site variance as a first-class
                  signal rather than optimization noise.
                </p>
                <footer>
                  <span
                    onClick={() => {
                      setAiAccepted(true)
                      showToast("Suggestion accepted & inserted into narrative")
                    }}
                    style={{ cursor: "pointer" }}
                  >
                    <kbd>Tab</kbd> Accept
                  </span>
                  <span
                    onClick={() => {
                      setAiDismissed(true)
                      showToast("Suggestion dismissed")
                    }}
                    style={{ cursor: "pointer" }}
                  >
                    <kbd>Esc</kbd> Dismiss
                  </span>
                </footer>
              </div>
            )}

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
              <h2>{claim === 0 ? "What supports Claim 1 (Figure 4b)" : "What supports Claim 2 (Equation 3)"}</h2>
            </div>
            <div>
              <button
                className="icon-button"
                onClick={() => setExpandedSource(!expandedSource)}
                title={expandedSource ? "Collapse viewer" : "Expand viewer"}
              >
                <Icon name="expand" />
              </button>
              <button
                className="icon-button"
                onClick={() => setView("pod")}
                title="Return to pod workspace"
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
            <div className="paper-thumb">{claim === 0 ? "NMI" : "IEEE"}</div>
            <div>
              <strong>
                {claim === 0
                  ? "Federated Foundation Models for Privacy-Preserving Neural Decoding"
                  : "Differential Privacy in Distributed Representation Learning"}
              </strong>
              <span>
                {claim === 0
                  ? "Zhang et al. · 2024 · Nature Machine Intelligence"
                  : "Dwork, Roth et al. · 2023 · IEEE Security & Privacy"}
              </span>
            </div>
            <button className="icon-button" onClick={downloadBibtex} title="Download BibTeX citation">
              <Icon name="download" />
            </button>
          </div>

          {sourceTab === "pdf" && (
            <div className="pdf-stage">
              <div className="page-number">PAGE {claim === 0 ? "8 / 14" : "12 / 18"}</div>
              <div className="pdf-page" style={{ transform: `scale(${zoom / 100})`, transformOrigin: "top center" }}>
                <div className="pdf-title">
                  {claim === 0
                    ? "Cross-subject alignment preserves decoding performance"
                    : "Formal bounds on non-interactive latent parameter releases"}
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

                {claim === 0 ? (
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
                ) : (
                  <div style={{ background: "#f8f9fa", padding: 14, border: "1px solid #dcdfe3", borderRadius: 8, margin: "14px 0", fontFamily: "'DM Mono', monospace", fontSize: 11 }}>
                    <strong>Theorem 3.2 (Differential Privacy Bound):</strong>
                    <p style={{ margin: "6px 0" }}>
                      Pr[M(D) ∈ S] ≤ exp(ε) · Pr[M(D') ∈ S] + δ, &nbsp; for all ||D - D'||₁ ≤ 1.
                    </p>
                    <span style={{ color: "var(--teal)", fontSize: 10 }}>Validated on-chain via Merkle root 0x774a...18fc</span>
                  </div>
                )}

                <div className="caption">
                  <b>{claim === 0 ? "Figure 4." : "Equation 3."}</b>{" "}
                  {claim === 0 ? (
                    <mark>(b) Latent alignment retains 94.2% of within-subject performance across five held-out cohorts.</mark>
                  ) : (
                    <mark>Formal proof that clipped gradients satisfy (0.5, 10⁻⁵)-differential privacy per communication round.</mark>
                  )}
                </div>
              </div>
              <div className="zoom-tools">
                <button onClick={() => setZoom((z) => Math.max(70, z - 10))}>−</button>
                <span>{zoom}%</span>
                <button onClick={() => setZoom((z) => Math.min(180, z + 10))}>+</button>
              </div>
            </div>
          )}

          {sourceTab === "extraction" && (
            <div className="source-tab-content">
              <div className="extraction-grid">
                <div className="extraction-field">
                  <span>OCR TEXT STREAM</span>
                  <code>{claim === 0 ? "Across 5 held-out cohorts (N=42), the aligned representation maintained 94.2% ± 1.8% of dedicated within-subject calibration decoding performance." : "Equation (3) bounds the total information leakage under Gaussian noise calibration with variance sigma squared."}</code>
                </div>
                <div className="extraction-field">
                  <span>VISION SEGMENTATION BOUNDING BOX</span>
                  <code>{claim === 0 ? "SAM 3.1 Polygon Coordinates: [x: 142.4, y: 388.1, width: 320.0, height: 184.5] - Figure 4b" : "Formula Region: [x: 88.0, y: 412.0, width: 410.0, height: 64.0]"}</code>
                </div>
                <div className="extraction-field">
                  <span>EXTRACTION PIPELINE CONFIDENCE</span>
                  <strong>98.4% (Multi-modal agreement: Text + SAM 3.1 Polygon)</strong>
                </div>
              </div>
            </div>
          )}

          {sourceTab === "audit" && (
            <div className="source-tab-content">
              <div className="extraction-grid">
                <div className="extraction-field">
                  <span>SOURCE DOCUMENT SHA-256 HASH</span>
                  <code>{claim === 0 ? "sha256:b3e1c8f47a8291f09277c1d29481aa09819284fa" : "sha256:9f28a716c0291ba48810c9217834bcdef901823a"}</code>
                </div>
                <div className="extraction-field">
                  <span>INDEXING TIMESTAMP & RUNNER</span>
                  <code>2025-10-09 14:32:18 UTC · Meta AI Extraction Fleet</code>
                </div>
                <div className="extraction-field">
                  <span>VERIFICATION MERKLE PATH</span>
                  <code>Leaf 04: Root 0x774ab92d18fc4e8932bce10871982aef12d094 (Verified on L2)</code>
                </div>
              </div>
            </div>
          )}

          <div className="audit-bar">
            <div className="audit-result">
              <span className={verifying ? "scan-icon scanning" : "scan-icon"}>
                <Icon name={verified ? "check" : "shield"} />
              </span>
              <div>
                <small>SOURCE CHECK</small>
                <strong>
                  {verifying
                    ? "Checking against source PDF…"
                    : verified
                    ? "The source supports this claim"
                    : "Strong source match"}
                </strong>
                <span>
                  {verifying
                    ? "Comparing claim semantics with Figure 4b"
                    : verified
                    ? "Checked just now · 0 contradictions found"
                    : "Last checked from the indexed paper"}
                </span>
              </div>
            </div>
            <button className="verify-button" onClick={verify} disabled={verifying}>
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
          <span className="rail-label">CLAIMS ON CURRENT PAGE</span>
          <div className="rail-claims">
            <button
              className={claim === 0 ? "active" : ""}
              onClick={() => {
                setClaim(0)
                setVerified(false)
                showToast("Focused Claim 1 in technical narrative")
              }}
            >
              <span>FIG 4B</span>
              <p>94.2% within-subject retention across cohorts</p>
            </button>
            <button
              className={claim === 1 ? "active" : ""}
              onClick={() => {
                setClaim(1)
                setVerified(false)
                showToast("Focused Claim 2 in technical narrative")
              }}
            >
              <span>EQ 3</span>
              <p>(ε, δ)-differential privacy guarantee</p>
            </button>
          </div>
          <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column", gap: 8 }}>
            <button
              className="soft-button"
              style={{ width: "100%", justifyContent: "center", fontSize: 11 }}
              onClick={() => onTelemetry(`Audit question for Claim ${claim + 1}: How does this source compare with recent baselines?`)}
            >
              <Icon name="message" /> <span>Ask literature</span>
            </button>
            <button
              className="soft-button"
              style={{ width: "100%", justifyContent: "center", fontSize: 11 }}
              onClick={() => openOverlay("reasoning")}
            >
              <Icon name="brain" /> <span>Reasoning</span>
            </button>
          </div>
        </aside>
      </div>
    </div>
  )
}

// --- TELEMETRY DRAWER (ASK NEXUS) ---

export function TelemetryDrawer({
  onClose,
  openOverlay,
  initialPrompt,
  onNavigate,
}: {
  onClose: () => void
  openOverlay: (overlay: Overlay) => void
  initialPrompt?: string
  onNavigate: (v: View) => void
}) {
  const [question, setQuestion] = useState(typeof initialPrompt === "string" ? initialPrompt : "")
  const [answer, setAnswer] = useState(typeof initialPrompt === "string" && Boolean(initialPrompt))
  const [telemetryData, setTelemetryData] = useState({
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
    "What evidence is missing for Aim 2?",
    "Summarize pod decisions this week",
    "Check Figure 4b for sample size discrepancies",
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
          <button className="icon-button" onClick={onClose} title="Close drawer">
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
              onChange={(e) => {
                setQuestion(e.target.value)
                setAnswer(false)
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  ask()
                }
              }}
            />
          </div>
          <button onClick={ask} disabled={!question.trim()}>
            Ask Nexus <Icon name="arrow" />
          </button>
        </div>

        {answer && (
          <div className="assistant-answer">
            <div>
              <Icon name="spark" />
              <strong>Nexus Synthesis</strong>
              <Tag tone="verification">3 verified sources</Tag>
            </div>
            <p>
              Aim 2 calibration reduction (61%) is strongly supported across 5 held-out cohorts in Zhang et al. (2024),
              provided parameter clipping bounds are enforced at communication round boundaries.
            </p>
            <button
              onClick={() => {
                onClose()
                onNavigate("pod")
              }}
            >
              Open supporting papers on Evidence Board <Icon name="arrow" />
            </button>
          </div>
        )}

        <div className="prompt-chips">
          {prompts.map((prompt) => (
            <button
              key={prompt}
              onClick={() => {
                setQuestion(prompt)
                setAnswer(true)
              }}
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="drawer-section-title">
          <span>AI activity & Telemetry</span>
          <small>muse-wonder-1.0 & sam-3.1 online</small>
        </div>

        <div className="engine-card active">
          <div>
            <span className="engine-icon">
              <Icon name="brain" />
            </span>
            <div>
              <b>muse-wonder-1.0</b>
              <small>Frontier reasoning · 5,813 reasoning tokens</small>
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
            <i /><i /><i /><i /><i /><i /><i /><i /><i /><i />
          </div>
        </div>

        <div className="engine-card">
          <div>
            <span className="engine-icon violet">
              <Icon name="eye" />
            </span>
            <div>
              <b>sam-3.1</b>
              <small>Multimodal vision · Figure extraction</small>
            </div>
            <i />
          </div>
          <dl>
            <div>
              <dt>Polygon latency</dt>
              <dd>312 ms</dd>
            </div>
            <div>
              <dt>Figures parsed</dt>
              <dd>8,412</dd>
            </div>
            <div>
              <dt>Confidence</dt>
              <dd>98.4%</dd>
            </div>
          </dl>
        </div>

        <button
          className="reasoning-trace"
          onClick={() => {
            onClose()
            openOverlay("reasoning")
          }}
        >
          <div>
            <span>REASONING INSPECTOR</span>
            <Tag tone="verification">LIVE</Tag>
          </div>
          <p>
            <code>trace_8f21</code> evaluated claim entailment across caption, figure legend, and plotted values.
          </p>
          <div className="token-line">
            <span>context retrieval</span>
            <i style={{ width: "92%" }} />
          </div>
          <div className="token-line">
            <span>deep reasoning</span>
            <i style={{ width: "76%" }} />
          </div>
          <span className="trace-action">
            Inspect step-by-step chain of thought <Icon name="arrow" size={14} />
          </span>
        </button>
      </aside>
    </div>
  )
}

// --- WORKFLOW OVERLAYS (ALL 9 WORKFLOWS) ---

export function ProductOverlay({
  overlay,
  onClose,
  showToast,
  onNavigate,
}: {
  overlay: Overlay
  onClose: () => void
  showToast: (msg: string) => void
  onNavigate: (v: View) => void
}) {
  // Reveal state
  const [selectedPerson, setSelectedPerson] = useState("Jordan Lee")
  const [revealAccepted, setRevealAccepted] = useState(false)

  // Graph state
  const [graphFilter, setGraphFilter] = useState("All campus")
  const [selectedNode, setSelectedNode] = useState<{ label: string; dept: string; papers: number } | null>(null)

  // Funding state
  const [activeGrantIdx, setActiveGrantIdx] = useState(0)
  const [agencyFilter, setAgencyFilter] = useState("All agencies")
  const [fundingDaysFilter, setFundingDaysFilter] = useState(false)

  // Project creator state
  const [ingestUrl, setIngestUrl] = useState("https://arxiv.org/abs/2403.11284")
  const [ingestStatus, setIngestStatus] = useState<"idle" | "loading" | "done">("idle")
  const [offersTags, setOffersTags] = useState(["Optimal transport", "Adapter weights"])
  const [needsTags, setNeedsTags] = useState(["Longitudinal EEG", "Clinical sleep data"])
  const [newTagInput, setNewTagInput] = useState("")

  // Peer review accordion
  const [expandedQuestion, setExpandedQuestion] = useState<number | null>(0)

  // Export state
  const [exportFormat, setExportFormat] = useState<"tex" | "md" | "pdf">("tex")
  const [includeFigures, setIncludeFigures] = useState(true)
  const [includeAudit, setIncludeAudit] = useState(true)
  const [includeBibtex, setIncludeBibtex] = useState(true)

  const grants = [
    {
      title: "Smart and Connected Health (SCH)",
      agency: "NSF",
      amount: "$1,200,000",
      deadline: "Nov 14",
      fit: 96,
      desc: "Supports multi-disciplinary teams addressing health challenges through computational innovations.",
    },
    {
      title: "Exploratory/Developmental Research Grant (R21)",
      agency: "NIH",
      amount: "$275,000",
      deadline: "Dec 12",
      fit: 91,
      desc: "High-risk, high-reward exploratory research in early stages of model development.",
    },
    {
      title: "Young Faculty Award (YFA)",
      agency: "DARPA",
      amount: "$500,000",
      deadline: "Jan 22",
      fit: 85,
      desc: "Innovative research in neurotelemetry, edge differential privacy, and robust learning.",
    },
  ]

  const handleRunIngest = () => {
    setIngestStatus("loading")
    window.setTimeout(() => {
      setIngestStatus("done")
      showToast("Meta AI successfully parsed abstract, methodology, and requirements!")
    }, 1200)
  }

  const handleDownloadExport = () => {
    let filename = `nsf_scc_proposal.${exportFormat}`
    let content = `% NSF Smart & Connected Communities Proposal\n% Generated by Nexus Collaboration Studio\n\n\\section{Technical Approach}\nRecent cross-subject alignment methods retain 94.2% of within-subject decoding accuracy...`
    if (exportFormat === "md") {
      content = `# NSF Smart & Connected Communities — Technical Narrative\n\n## 2. Technical Approach\nRecent cross-subject alignment methods retain 94.2% of within-subject decoding accuracy while reducing calibration requirements by 61% (Zhang et al. 2024).`
    }
    const blob = new Blob([content], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    try {
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {}
    showToast(`Downloaded submission package: ${filename}`)
    onClose()
  }

  const overlayTitles: Record<Overlay, { eyebrow: string; title: string }> = {
    reveal: { eyebrow: "MUTUAL DISCOVERY", title: "Mutual Double Opt-In Reveal" },
    verify: { eyebrow: "ON-CHAIN RECORD", title: "Proof of Priority Verification" },
    graph: { eyebrow: "KNOWLEDGE GRAPH", title: "Living Campus Graph Explorer" },
    funding: { eyebrow: "SOLICITATION FINDER", title: "Active Grants & Solicitations" },
    project: { eyebrow: "NEW PROJECT", title: "Create & Ingest Project" },
    "peer-review": { eyebrow: "PRE-FLIGHT AUDIT", title: "Simulated NSF Merit Review" },
    conflict: { eyebrow: "CONTRADICTION ANALYSIS", title: "Evidence Conflict Resolution" },
    export: { eyebrow: "SUBMISSION READY", title: "Academic Export Studio" },
    reasoning: { eyebrow: "CHAIN OF THOUGHT", title: "Multi-Stage Reasoning Inspector" },
  }

  return (
    <div className="product-overlay workspace-overlay" onClick={onClose}>
      <div className="overlay-shell" onClick={(e) => e.stopPropagation()}>
        <header className="overlay-header">
          <div>
            <span className="overlay-eyebrow">{overlayTitles[overlay].eyebrow}</span>
            <h2>{overlayTitles[overlay].title}</h2>
          </div>
          <button className="icon-button" onClick={onClose} title="Close overlay">
            <Icon name="close" />
          </button>
        </header>

        {overlay === "reveal" && (
          <div className="reveal-flow">
            <p className="lead">
              Profiles and confidential hypotheses reveal only when both researchers explicitly execute mutual consent.
            </p>
            <div className="reveal-people">
              <div className="reveal-card">
                <Avatar initials="AM" color="gold" active />
                <div className="reveal-meta">
                  <h3>Aria Malik</h3>
                  <span>MSCS · UC Berkeley</span>
                  <Tag tone="stage">Identity Revealed by You</Tag>
                </div>
              </div>
              <div className={`reveal-card ${revealAccepted ? "revealed" : "blurred"}`}>
                <Avatar initials="JL" color="blue" active={revealAccepted} />
                <div className="reveal-meta">
                  <h3>{revealAccepted ? "Jordan Lee" : "Anonymous Researcher"}</h3>
                  <span>{revealAccepted ? "PhD Researcher · Helen Wills Neuroscience Institute" : "Neuroscience · 0.4 miles away"}</span>
                  <Tag tone={revealAccepted ? "verification" : "need"}>
                    {revealAccepted ? "Mutual Consent Verified" : "Awaiting Your Acceptance"}
                  </Tag>
                </div>
              </div>
            </div>
            <div className="overlay-actions">
              <button
                className="soft-button"
                onClick={() => {
                  navigator.clipboard?.writeText("https://nexus.research/reveal/nx-91a").catch(() => {})
                  showToast("Copied mutual disclosure link")
                }}
              >
                <Icon name="copy" /> Copy mutual link
              </button>
              <button
                className="accent-button"
                onClick={() => {
                  setRevealAccepted(true)
                  showToast("Mutual consent verified! Full profile & contact details unblurred.")
                }}
              >
                {revealAccepted ? "Connection Established" : "Accept Connection & Reveal"}
              </button>
            </div>
          </div>
        )}

        {overlay === "verify" && (
          <div className="verification-page">
            <div className="verification-grid">
              <div className="qr-placeholder">
                <Icon name="seal" size={54} />
                <small>SHA-256 Merkle Proof</small>
              </div>
              <div className="verification-details">
                <Tag tone="verification">SEALED & IMMUTABLE</Tag>
                <h3>Official Proof of Priority #NX-8492</h3>
                <dl>
                  <div>
                    <dt>Owner</dt>
                    <dd>Aria Malik (UC Berkeley)</dd>
                  </div>
                  <div>
                    <dt>Timestamp</dt>
                    <dd>09 Oct 2025 · 14:32:18 UTC</dd>
                  </div>
                  <div>
                    <dt>Merkle Root</dt>
                    <dd>0x774ab92d18fc4e8932bce10871982aef12d094</dd>
                  </div>
                  <div>
                    <dt>Hardware Anchor</dt>
                    <dd>Device Key 0x9f2a...7c01 (Ed25519)</dd>
                  </div>
                </dl>
              </div>
            </div>
            <div className="overlay-actions">
              <button
                className="soft-button"
                onClick={() => {
                  navigator.clipboard?.writeText("https://nexus.research/verify/NX-8492").catch(() => {})
                  showToast("Public verification URL copied to clipboard")
                }}
              >
                <Icon name="copy" /> Copy verification link
              </button>
              <button
                className="accent-button"
                onClick={() => {
                  const receipt = {
                    certificateId: "NX-8492",
                    merkleRoot: "0x774ab92d18fc4e8932bce10871982aef12d094",
                    blockHeight: 18492041,
                    timestamp: "2025-10-09T14:32:18Z",
                    owner: "Aria Malik",
                    status: "SEALED_ON_CHAIN",
                  }
                  const blob = new Blob([JSON.stringify(receipt, null, 2)], { type: "application/json" })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement("a")
                  a.href = url
                  a.download = "nexus_verification_receipt_NX8492.json"
                  a.click()
                  URL.revokeObjectURL(url)
                  showToast("Downloaded official on-chain receipt")
                }}
              >
                <Icon name="download" /> Download receipt (.json)
              </button>
            </div>
          </div>
        )}

        {overlay === "graph" && (
          <div className="graph-workspace">
            <div className="graph-toolbar">
              <label>
                <Icon name="search" />
                <input placeholder="Search people, topics, or papers in graph..." />
              </label>
              {["All campus", "People", "Projects", "Papers"].map((tab) => (
                <button
                  key={tab}
                  className={graphFilter === tab ? "active" : ""}
                  onClick={() => {
                    setGraphFilter(tab)
                    showToast(`Graph filtered by: ${tab}`)
                  }}
                >
                  {tab}
                </button>
              ))}
            </div>
            <div className="graph-main">
              <div className="graph-canvas">
                <svg viewBox="0 0 800 520" aria-label="Research graph">
                  <g stroke="#bfd0df" strokeWidth="1.2">
                    <path d="M150 190 350 110 520 180 650 95M150 190 280 330 470 360 650 95M350 110 470 360M520 180 280 330M470 360 680 390M280 330 120 410" />
                  </g>
                  {[
                    [150, 190, 32, "#0a66c2", "Federated Learning", "EECS"],
                    [350, 110, 27, "#6755a6", "EEG Telemetry", "Neuroscience"],
                    [520, 180, 36, "#2d8067", "Neural Decoding", "Helen Wills"],
                    [650, 95, 23, "#a46d27", "Mobile Hardware", "Bioengineering"],
                    [280, 330, 34, "#0a66c2", "Differential Privacy", "EECS"],
                    [470, 360, 29, "#6755a6", "Sleep Staging", "Clinical Precision"],
                  ].map(([cx, cy, r, fill, label, dept], idx) => (
                    <g
                      key={idx}
                      className="graph-node"
                      style={{ cursor: "pointer" }}
                      onClick={() => setSelectedNode({ label: String(label), dept: String(dept), papers: 8 + idx * 3 })}
                    >
                      <circle cx={Number(cx)} cy={Number(cy)} r={Number(r)} fill={String(fill)} opacity=".92" />
                      <circle cx={Number(cx)} cy={Number(cy)} r={Number(r) + 7} fill="none" stroke={String(fill)} opacity=".2" />
                      <text x={Number(cx)} y={Number(cy) + 4} textAnchor="middle" fill="#fff" fontSize={10} fontWeight={600}>
                        {String(label).split(" ")[0]}
                      </text>
                    </g>
                  ))}
                </svg>
              </div>
              <aside className="graph-inspector">
                <h3>{selectedNode ? selectedNode.label : "Knowledge Gap Found"}</h3>
                <Tag tone="stage">{selectedNode ? selectedNode.dept : "CROSS-DISCIPLINARY OPPORTUNITY"}</Tag>
                <p style={{ margin: "10px 0", fontSize: 12, lineHeight: 1.5, color: "var(--muted)" }}>
                  {selectedNode
                    ? `Connected across ${selectedNode.papers} indexed publications and 3 active Berkeley research pods.`
                    : "No lab in EECS is currently paired with Helen Wills EEG Mobile Rig despite 14 overlapping citations on latent alignment."}
                </p>
                <button
                  className="accent-button"
                  style={{ width: "100%", justifyContent: "center" }}
                  onClick={() => {
                    onClose()
                    onNavigate("campus")
                  }}
                >
                  Bridge this gap on Campus <Icon name="arrow" />
                </button>
              </aside>
            </div>
          </div>
        )}

        {overlay === "funding" && (
          <div className="funding-workspace">
            <aside className="funding-filters">
              <label>
                <Icon name="search" />
                <input placeholder="Filter solicitations..." />
              </label>
              <strong>Agency</strong>
              {["All agencies", "NSF", "NIH", "DARPA"].map((agency) => (
                <button
                  key={agency}
                  className={agencyFilter === agency ? "active" : ""}
                  onClick={() => {
                    setAgencyFilter(agency)
                    showToast(`Filtered by: ${agency}`)
                  }}
                >
                  {agency}
                </button>
              ))}
              <strong>Deadline</strong>
              <button
                className={fundingDaysFilter ? "active" : ""}
                onClick={() => setFundingDaysFilter(!fundingDaysFilter)}
              >
                {fundingDaysFilter ? "All deadlines" : "Next 90 days"}
              </button>
            </aside>
            <div className="grant-list">
              {grants.map((grant, idx) => (
                <button
                  key={grant.title}
                  className={activeGrantIdx === idx ? "active" : ""}
                  onClick={() => setActiveGrantIdx(idx)}
                >
                  <span className="agency-mark">{grant.agency}</span>
                  <div>
                    <small>{grant.agency} · Deadline {grant.deadline}</small>
                    <b>{grant.title}</b>
                    <em>{grant.amount}</em>
                  </div>
                </button>
              ))}
            </div>
            <aside className="grant-detail">
              <span>{grants[activeGrantIdx].agency} OPPORTUNITY</span>
              <h2>{grants[activeGrantIdx].title}</h2>
              <p>{grants[activeGrantIdx].desc}</p>
              <button
                className="accent-button"
                style={{ width: "100%", justifyContent: "center", marginBottom: 8 }}
                onClick={() => {
                  showToast(`Linked ${grants[activeGrantIdx].title} to Neural Commons pod milestones!`)
                  onClose()
                }}
              >
                Link to Neural Commons pod
              </button>
              <button
                className="soft-button"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={() => window.open("https://www.nsf.gov", "_blank")}
              >
                Open official solicitation
              </button>
            </aside>
          </div>
        )}

        {overlay === "project" && (
          <div className="project-creator">
            <div className="ingest-box">
              <span><Icon name="spark" size={24} /></span>
              <div>
                <strong>1-Click Meta AI Project Ingest</strong>
                <p style={{ margin: "2px 0 0", fontSize: 11, color: "var(--muted)" }}>
                  Paste an arXiv abstract or GitHub repository to auto-populate offers, needs, and research stage.
                </p>
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, margin: "14px 0" }}>
              <input
                value={ingestUrl}
                onChange={(e) => setIngestUrl(e.target.value)}
                placeholder="https://arxiv.org/abs/..."
                style={{ flex: 1, height: 38, border: "1px solid var(--line-dark)", borderRadius: 8, padding: "0 12px", fontSize: 12 }}
              />
              <button className="accent-button" onClick={handleRunIngest}>
                {ingestStatus === "loading" ? "Parsing…" : "Parse with Meta AI"}
              </button>
            </div>
            <div>
              <strong>What your project offers:</strong>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", margin: "6px 0 12px" }}>
                {offersTags.map((t) => (
                  <Tag tone="offer" key={t}>{t}</Tag>
                ))}
              </div>
              <strong>What your project needs:</strong>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", margin: "6px 0 14px" }}>
                {needsTags.map((t) => (
                  <Tag tone="need" key={t}>{t}</Tag>
                ))}
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  value={newTagInput}
                  onChange={(e) => setNewTagInput(e.target.value)}
                  placeholder="Add custom need (e.g. 128-channel EEG)..."
                  style={{ flex: 1, height: 34, border: "1px solid var(--line-dark)", borderRadius: 6, padding: "0 10px", fontSize: 12 }}
                />
                <button
                  className="soft-button"
                  style={{ height: 34, fontSize: 11 }}
                  onClick={() => {
                    if (newTagInput.trim()) {
                      setNeedsTags([...needsTags, newTagInput.trim()])
                      setNewTagInput("")
                      showToast("Added custom requirement tag")
                    }
                  }}
                >
                  <Icon name="plus" size={14} /> Add Need
                </button>
              </div>
            </div>
            <div className="overlay-actions" style={{ marginTop: 20 }}>
              <button className="soft-button" onClick={onClose}>Cancel</button>
              <button
                className="accent-button"
                onClick={() => {
                  showToast("Project created & published to Campus Discovery!")
                  onClose()
                  onNavigate("campus")
                }}
              >
                Create Project
              </button>
            </div>
          </div>
        )}

        {overlay === "peer-review" && (
          <div className="peer-review">
            <div className="review-overall">
              <MetricRing value={92} label="SCORE" tone="teal" size={74} />
              <div>
                <strong>Recommendation: Highly Competitive</strong>
                <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--muted)" }}>
                  NSF Smart & Connected Communities panel pre-flight audit.
                </p>
              </div>
            </div>
            <div className="rubric-grid">
              <div className="rubric-card">
                <b>Intellectual Merit: Excellent</b>
                <p style={{ margin: "4px 0 0", fontSize: 11, color: "var(--muted)" }}>
                  Latent alignment geometry avoids pooling sensitive data while matching baseline accuracy.
                </p>
              </div>
              <div className="rubric-card">
                <b>Broader Impacts: Very Good</b>
                <p style={{ margin: "4px 0 0", fontSize: 11, color: "var(--muted)" }}>
                  Open-source differential privacy tooling strengthens cross-institutional clinical trials.
                </p>
              </div>
            </div>
            <div className="review-questions">
              <strong>Panel Clarification Questions (Click to Expand)</strong>
              {[
                {
                  id: 0,
                  q: "Add a measurable Broader Impacts outcome for rural hospitals",
                  detail: "Reviewers suggest committing to a 3-clinic deployment pilot to validate low-bandwidth performance.",
                },
                {
                  id: 1,
                  q: "Clarify the fallback strategy if site adaptation fails to converge",
                  detail: "Specify whether federated averaging or gradient clipping is applied when loss exceeds threshold delta.",
                },
              ].map((item) => (
                <button
                  key={item.id}
                  className="question-card"
                  onClick={() => setExpandedQuestion(expandedQuestion === item.id ? null : item.id)}
                  style={{ textAlign: "left", width: "100%", display: "block", marginBottom: 8, padding: 12, border: "1px solid var(--line)", borderRadius: 8, background: "white" }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <b>{item.q}</b>
                    <Icon name="chevron" size={14} />
                  </div>
                  {expandedQuestion === item.id && (
                    <p style={{ margin: "8px 0 0", fontSize: 11, color: "var(--teal)", lineHeight: 1.5 }}>
                      {item.detail}
                    </p>
                  )}
                </button>
              ))}
            </div>
            <div className="overlay-actions">
              <button
                className="soft-button"
                onClick={() => {
                  const rpt = `# NSF SCC Merit Review Audit Report\n\nOverall Score: 92/100 (Highly Competitive)\n\nIntellectual Merit: Excellent\nBroader Impacts: Very Good\n\nActions Required:\n1. Measure broader impact on rural clinics.\n2. Add fallback mechanism for inter-site divergence.`
                  const blob = new Blob([rpt], { type: "text/markdown" })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement("a")
                  a.href = url
                  a.download = "nsf_merit_review_audit_report.md"
                  a.click()
                  URL.revokeObjectURL(url)
                  showToast("Downloaded NSF Merit Review Audit Report")
                }}
              >
                <Icon name="download" /> Full Report (.md)
              </button>
              <button
                className="accent-button"
                onClick={() => {
                  showToast("Switched to Proposal Studio to address panel recommendations")
                  onClose()
                  onNavigate("proof")
                }}
              >
                Fix Issues in Proposal Studio
              </button>
            </div>
          </div>
        )}

        {overlay === "conflict" && (
          <div className="conflict-view">
            <p className="lead">
              Methodological discrepancy detected between Zhang et al. (2024) and Li et al. (2024).
            </p>
            <div className="paper-comparison">
              <article>
                <Tag tone="supports">Nature MI 2024</Tag>
                <h3>Zhang et al.</h3>
                <p>Reports 94.2% retention under optimal transport with bounded client drift.</p>
              </article>
              <div className="versus">VS</div>
              <article>
                <Tag tone="contradicts">ACM FAccT 2023</Tag>
                <h3>Rao et al.</h3>
                <p>Argues that membership inference attacks succeed if client loss variance is non-zero.</p>
              </article>
            </div>
            <div className="conflict-recommendation">
              <Icon name="spark" />
              <span>
                <b>Recommended Synthesis for Section 2.1:</b> State that client drift is bounded under non-interactive DP noise, while active participant attacks remain an open empirical limitation.
              </span>
              <button
                className="accent-button"
                onClick={() => {
                  showToast("Balanced synthesis inserted into Section 2.1!")
                  onClose()
                  onNavigate("proof")
                }}
              >
                Insert Balanced Claim
              </button>
            </div>
          </div>
        )}

        {overlay === "export" && (
          <div className="export-dialog">
            <div className="format-grid">
              {(["tex", "pdf", "md"] as const).map((fmt) => (
                <button
                  key={fmt}
                  className={exportFormat === fmt ? "active" : ""}
                  onClick={() => setExportFormat(fmt)}
                >
                  <b>{fmt.toUpperCase()}</b>
                  <small>{fmt === "tex" ? "LaTeX + BibTeX" : fmt === "pdf" ? "Compiled PDF" : "Markdown + Math"}</small>
                </button>
              ))}
            </div>
            <div className="export-options">
              <label>
                <input type="checkbox" checked={includeFigures} onChange={(e) => setIncludeFigures(e.target.checked)} />
                <span>Include SAM 3.1 figure polygons & vector crops</span>
              </label>
              <label>
                <input type="checkbox" checked={includeAudit} onChange={(e) => setIncludeAudit(e.target.checked)} />
                <span>Include cryptographic citation audit trail</span>
              </label>
              <label>
                <input type="checkbox" checked={includeBibtex} onChange={(e) => setIncludeBibtex(e.target.checked)} />
                <span>Include complete BibTeX database (.bib)</span>
              </label>
            </div>
            <div className="overlay-actions">
              <button
                className="soft-button"
                onClick={() => showToast("Export preset saved as default")}
              >
                Save preset
              </button>
              <button className="accent-button" onClick={handleDownloadExport}>
                <Icon name="download" /> Download Package ({exportFormat.toUpperCase()})
              </button>
            </div>
          </div>
        )}

        {overlay === "reasoning" && (
          <div className="reasoning-inspector">
            <div className="reasoning-question">
              <span>TRACE EVALUATION: TRACE_8F21</span>
              <p>Claim: "Latent alignment retains 94.2% within-subject accuracy across cohorts."</p>
            </div>
            <div className="reasoning-layout">
              <div className="reasoning-tree">
                {[
                  { step: "01", title: "Visual Grounding Check", text: "SAM 3.1 isolated Figure 4b bar charts from page 8 of Nature MI paper." },
                  { step: "02", title: "Numerical Data Extraction", text: "Plotted values for Cohorts 1-5 verify mean of 94.2% ± 1.8%." },
                  { step: "03", title: "Contradiction Audit", text: "Compared with Li et al. (2024); methodology conditions are compatible." },
                ].map((s) => (
                  <div key={s.step} className="reasoning-step">
                    <span>{s.step}</span>
                    <div>
                      <b>{s.title}</b>
                      <p>{s.text}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="reasoning-evidence">
                <b>Cryptographic Validation</b>
                <p style={{ fontSize: 11, color: "var(--muted)" }}>
                  Verified against immutable SHA-256 Merkle leaf on-device. Zero unverified assertions.
                </p>
                <button
                  className="accent-button"
                  style={{ width: "100%", justifyContent: "center", marginTop: 12, fontSize: 11 }}
                  onClick={() => {
                    showToast("Reasoning certificate verified against L2 ledger")
                    onClose()
                  }}
                >
                  Verify on Ledger
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// --- ROOT APPLICATION COMPONENT ---

export default function App() {
  const [view, setView] = useState<View>("home")
  const [telemetry, setTelemetry] = useState(false)
  const [telemetryPrompt, setTelemetryPrompt] = useState<string | undefined>()
  const [overlay, setOverlay] = useState<Overlay | null>(null)
  const [toastMsg, setToastMsg] = useState<string | null>(null)

  // Modals
  const [profileOpen, setProfileOpen] = useState(false)
  const [viewsOpen, setViewsOpen] = useState(false)
  const [availOpen, setAvailOpen] = useState(false)
  const [savedOpen, setSavedOpen] = useState(false)
  const [composerOpen, setComposerOpen] = useState(false)
  const [addTeammateOpen, setAddTeammateOpen] = useState(false)
  const [addPaperOpen, setAddPaperOpen] = useState(false)
  const [charterOpen, setCharterOpen] = useState(false)
  const toastTimeoutRef = useRef<any>(null)

  const showToast = useCallback((msg: string) => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current)
    }
    setToastMsg(msg)
    toastTimeoutRef.current = window.setTimeout(() => {
      setToastMsg(null)
      toastTimeoutRef.current = null
    }, 3200)
  }, [])

  const handleOpenTelemetry = (prompt?: unknown) => {
    setTelemetryPrompt(typeof prompt === "string" ? prompt : undefined)
    setTelemetry(true)
  }

  return (
    <AppFrame
      view={view}
      setView={setView}
      onTelemetry={handleOpenTelemetry}
      openOverlay={setOverlay}
      showToast={showToast}
      openProfile={() => setProfileOpen(true)}
      openCharter={() => setCharterOpen(true)}
    >
      {view === "home" && (
        <HomeView
          setView={setView}
          openOverlay={setOverlay}
          onTelemetry={handleOpenTelemetry}
          showToast={showToast}
          openProfile={() => setProfileOpen(true)}
          openViews={() => setViewsOpen(true)}
          openAvailability={() => setAvailOpen(true)}
          openSaved={() => setSavedOpen(true)}
          openComposer={() => setComposerOpen(true)}
          openCharter={() => setCharterOpen(true)}
        />
      )}

      {view === "campus" && (
        <CampusView
          setView={setView}
          openOverlay={setOverlay}
          showToast={showToast}
          openProfile={() => setProfileOpen(true)}
        />
      )}

      {view === "vault" && (
        <VaultView
          openOverlay={setOverlay}
          showToast={showToast}
        />
      )}

      {view === "pod" && (
        <PodView
          setView={setView}
          openOverlay={setOverlay}
          onTelemetry={handleOpenTelemetry}
          showToast={showToast}
          openAddTeammate={() => setAddTeammateOpen(true)}
          openAddPaper={() => setAddPaperOpen(true)}
        />
      )}

      {view === "proof" && (
        <ProofView
          setView={setView}
          openOverlay={setOverlay}
          onTelemetry={handleOpenTelemetry}
          showToast={showToast}
        />
      )}

      {/* Slide-over Drawers & Overlays */}
      {telemetry && (
        <TelemetryDrawer
          onClose={() => setTelemetry(false)}
          openOverlay={(next) => {
            setTelemetry(false)
            setOverlay(next)
          }}
          initialPrompt={telemetryPrompt}
          onNavigate={(v) => {
            setTelemetry(false)
            setView(v)
          }}
        />
      )}

      {overlay && (
        <ProductOverlay
          overlay={overlay}
          onClose={() => setOverlay(null)}
          showToast={showToast}
          onNavigate={(v) => {
            setOverlay(null)
            setView(v)
          }}
        />
      )}

      {/* Rich Modals */}
      {profileOpen && <ProfileModal onClose={() => setProfileOpen(false)} onNavigate={setView} />}
      {viewsOpen && <ViewsModal onClose={() => setViewsOpen(false)} />}
      {availOpen && <AvailabilityModal onClose={() => setAvailOpen(false)} onSave={showToast} />}
      {savedOpen && <SavedResearchModal onClose={() => setSavedOpen(false)} onNavigate={setView} />}
      {composerOpen && (
        <PostComposerModal
          onClose={() => setComposerOpen(false)}
          onPublish={(post) => {
            showToast(`Project "${post.title}" published to network!`)
          }}
        />
      )}
      {addTeammateOpen && (
        <AddTeammateModal
          onClose={() => setAddTeammateOpen(false)}
          onInvite={(email) => {
            showToast(email === "link-copied" ? "Invite link copied to clipboard!" : `Invitation sent to ${email}`)
          }}
        />
      )}
      {addPaperOpen && (
        <AddPaperModal
          onClose={() => setAddPaperOpen(false)}
          onAdd={(paper) => {
            showToast(`Paper "${paper.title}" indexed into Evidence Board!`)
          }}
        />
      )}
      {charterOpen && <AboutCharterModal onClose={() => setCharterOpen(false)} />}

      {/* Feedback Toast */}
      {toastMsg && <Toast message={toastMsg} />}
    </AppFrame>
  )
}
