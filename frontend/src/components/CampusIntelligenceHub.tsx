"use client";

import React, { useState, useEffect } from "react";
import { 
  ShieldCheck, 
  Sparkles, 
  FileText, 
  Cpu, 
  Lock, 
  Unlock, 
  Eye, 
  CheckCircle2, 
  ExternalLink, 
  Compass, 
  ChevronRight, 
  Activity, 
  Zap, 
  ArrowRight,
  Layers,
  GraduationCap,
  Users,
  Check,
  Share2,
  Bookmark,
  MessageSquare,
  Send,
  Plus,
  SlidersHorizontal,
  Clock,
  Pin,
  Flame,
  Search
} from "lucide-react";

interface Project {
  project_id: string;
  title: string;
  teaser: string;
  stage: string;
  department: string;
  degree_level: string;
  offers: string[];
  needs: string[];
  certificate_id?: string;
  owner_id: string;
}

interface SerendipityMatch {
  match_id: string;
  peer_title: string;
  peer_teaser: string;
  peer_department: string;
  peer_degree_level: string;
  peer_offers: string[];
  peer_needs: string[];
  synergy_score: number;
  complementarity_score: number;
  distance_miles: number;
  bridge_sentence: string;
  reveal_status: string;
  meta_reasoning_tokens: number;
}

export default function CampusIntelligenceHub() {
  // Navigation: The 3 Flagship Screens + Telemetry
  const [activeScreen, setActiveScreen] = useState<"discovery" | "pod" | "vault" | "proof">("discovery");
  
  // Screen 3: Discovery Feed State
  const [projects, setProjects] = useState<Project[]>([]);
  const [matches, setMatches] = useState<SerendipityMatch[]>([]);
  const [revealedMatches, setRevealedMatches] = useState<Record<string, boolean>>({});
  const [feedFilter, setFeedFilter] = useState<string>("All");

  // Screen 2: Vault State
  const [previewAs, setPreviewAs] = useState<"stranger" | "peer" | "professor">("peer");
  const [vaultTitle, setVaultTitle] = useState("");
  const [vaultText, setVaultText] = useState("");
  const [sealedCert, setSealedCert] = useState<any>(null);
  const [isSealing, setIsSealing] = useState(false);
  const [scrambleHash, setScrambleHash] = useState("9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08");

  // Screen 1: Pod Headquarters State
  const [activeMilestone, setActiveMilestone] = useState<number>(2); // 0: Discovery, 1: Drafting, 2: Review, 3: Submitted
  const [pinnedEvidence, setPinnedEvidence] = useState<string[]>(["ev_1", "ev_2"]);
  const [proposalText, setProposalText] = useState(
    `# Project Summary: Decentralized Swarm Intelligence for Autonomous Clinical Triage\n\n` +
    `### Specific Aims & Technical Approach\n` +
    `Under adversarial wireless environments with high packet loss (40%), current multi-agent consensus protocols experience cascading failover.\n\n` +
    `Our preliminary benchmark demonstrates that weighted gossip consensus preserves sub-50ms latency across 64 edge nodes [Xia et al., 2024], enabling real-time ambulatory EEG event processing [Patel et al., 2024].\n\n` +
    `### Broader Impacts & Validation\n` +
    `This platform bridges the gap between field robotics and decentralized emergency medicine, establishing an open-source hardware reference design.`
  );

  useEffect(() => {
    fetch(`/api/v2/campus/projects?preview_as=${previewAs}`)
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) setProjects(data);
      })
      .catch(() => {});

    fetch("/api/v2/campus/serendipity/matches")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) setMatches(data);
      })
      .catch(() => {});
  }, [previewAs]);

  const handleSealHypothesis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vaultTitle || !vaultText) return;
    setIsSealing(true);

    // Character scramble effect
    let count = 0;
    const interval = setInterval(() => {
      const chars = "0123456789abcdef";
      let randomHex = "";
      for (let i = 0; i < 64; i++) randomHex += chars[Math.floor(Math.random() * chars.length)];
      setScrambleHash(randomHex);
      count++;
      if (count > 8) {
        clearInterval(interval);
      }
    }, 80);

    try {
      const res = await fetch("/api/v2/campus/vault/seal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: vaultTitle,
          hypothesis_text: vaultText,
          author_id: "anurag_mscs_26",
          department: "Computer Science",
          degree_level: "MSCS '26"
        })
      });
      const data = await res.json();
      setSealedCert(data);
      setScrambleHash(data.fingerprint);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSealing(false);
    }
  };

  const handleReveal = async (matchId: string) => {
    try {
      const res = await fetch(`/api/v2/campus/serendipity/reveal?match_id=${matchId}`, {
        method: "POST"
      });
      if (res.ok) {
        setRevealedMatches((prev) => ({ ...prev, [matchId]: true }));
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#07080A] text-slate-100 overflow-hidden font-sans">
      {/* ------------------------------------------------------------- */}
      {/* GLOBAL TOPBAR (56px fixed)                                     */}
      {/* ------------------------------------------------------------- */}
      <header className="h-14 border-b border-white/[0.08] bg-[#0E1015]/95 px-5 flex items-center justify-between shrink-0 z-30 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-[#7C6CFF] via-indigo-600 to-[#00C2FF] flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <div>
              <span className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
                NEXUS
                <span className="text-[10px] font-mono text-[#0EC9A7] bg-[#0EC9A7]/10 px-1.5 py-0.2 rounded border border-[#0EC9A7]/20 uppercase">
                  Living Campus Graph
                </span>
              </span>
            </div>
          </div>

          <div className="hidden md:flex items-center bg-[#15181F] border border-white/[0.08] rounded-full px-3 py-1.5 w-72 text-xs text-slate-400 gap-2 focus-within:border-[#7C6CFF]/50 transition-all">
            <Search className="h-3.5 w-3.5 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search needs, offers, methods... ⌘K"
              className="bg-transparent border-0 p-0 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none w-full"
            />
          </div>
        </div>

        {/* Mode Navigation Buttons */}
        <div className="flex items-center gap-1 bg-[#15181F] p-1 rounded-xl border border-white/[0.08]">
          <button
            onClick={() => setActiveScreen("discovery")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeScreen === "discovery"
                ? "bg-[#7C6CFF] text-white shadow-md shadow-[#7C6CFF]/25 font-semibold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Compass className="h-3.5 w-3.5" />
            Campus Discovery
          </button>

          <button
            onClick={() => setActiveScreen("pod")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeScreen === "pod"
                ? "bg-[#7C6CFF] text-white shadow-md shadow-[#7C6CFF]/25 font-semibold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Users className="h-3.5 w-3.5" />
            Research Pod Studio
          </button>

          <button
            onClick={() => setActiveScreen("vault")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeScreen === "vault"
                ? "bg-[#7C6CFF] text-white shadow-md shadow-[#7C6CFF]/25 font-semibold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            Private Vault
          </button>

          <button
            onClick={() => setActiveScreen("proof")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeScreen === "proof"
                ? "bg-[#7C6CFF] text-white shadow-md shadow-[#7C6CFF]/25 font-semibold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <CheckCircle2 className="h-3.5 w-3.5 text-[#0EC9A7]" />
            Pixel-to-Proof Grounding
          </button>
        </div>

        {/* Right Status Indicator */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400 bg-[#15181F] px-2.5 py-1 rounded-full border border-white/[0.08]">
            <span className="h-2 w-2 rounded-full bg-[#0EC9A7] animate-pulse" />
            <span>Meta Muse Wonder 1.0 Active</span>
          </div>

          <div className="h-7 w-7 rounded-full bg-indigo-600/80 border border-indigo-400/30 flex items-center justify-center text-xs font-bold text-white shadow">
            A
          </div>
        </div>
      </header>

      {/* ------------------------------------------------------------- */}
      {/* SCREEN 3: NEXUS CAMPUS DISCOVERY FEED & SERENDIPITY MATCH      */}
      {/* (LinkedIn-inspired social discovery without demographic bias)   */}
      {/* ------------------------------------------------------------- */}
      {activeScreen === "discovery" && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-[1200px] mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left 3 Cols: Mini Profile & Network Node */}
            <aside className="lg:col-span-3 space-y-4">
              <div className="bg-[#0E1015] border border-white/[0.08] rounded-2xl p-5 space-y-4">
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-lg text-white shadow-md">
                    AR
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">Anurag</h3>
                    <p className="text-xs text-slate-400 font-mono">MSCS '26 • RIT</p>
                    <span className="text-[10px] text-emerald-400 font-medium">● Available for Pods</span>
                  </div>
                </div>

                <div className="pt-3 border-t border-white/[0.06] space-y-2 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Pre-Publication Vault</span>
                    <span className="font-mono text-indigo-400 font-bold">1 Sealed</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Synergy Matches Nearby</span>
                    <span className="font-mono text-[#0EC9A7] font-bold">2 High Fit</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Citation Network Edges</span>
                    <span className="font-mono text-slate-200">14 Links</span>
                  </div>
                </div>

                <div className="pt-3 border-t border-white/[0.06] space-y-2">
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block">My Registered Offers:</span>
                  <div className="flex flex-wrap gap-1">
                    {["Distributed Consensus", "CUDA Kernels", "ROS2 Navigation"].map((tag, i) => (
                      <span key={i} className="text-[11px] px-2 py-0.5 rounded-full bg-[#0EC9A7]/10 text-[#0EC9A7] border border-[#0EC9A7]/20 font-medium flex items-center gap-1">
                        <span className="text-[9px] font-bold">[+]</span> {tag}
                      </span>
                    ))}
                  </div>

                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block pt-2">My Current Needs:</span>
                  <div className="flex flex-wrap gap-1">
                    {["Biomedical Sensor Data", "UAV Flight Arena", "Clinical IRB"].map((tag, i) => (
                      <span key={i} className="text-[11px] px-2 py-0.5 rounded-full bg-[#FFB224]/10 text-[#FFB224] border border-[#FFB224]/20 font-medium flex items-center gap-1">
                        <span className="text-[9px] font-bold">[○]</span> {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Campus Graph Pulse */}
              <div className="bg-[#0E1015] border border-white/[0.08] rounded-2xl p-4 text-xs space-y-2">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5 text-cyan-400" />
                  Campus Research Pulse
                </span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  34 active pre-prints ingested today across Golisano College of Computing and Kate Gleason Engineering.
                </p>
              </div>
            </aside>

            {/* Center 6 Cols: Explainable Match Banner + LinkedIn-Style Campus Feed */}
            <main className="lg:col-span-6 space-y-5">
              {/* Top Banner: Serendipity Match of the Day */}
              {matches.slice(0, 1).map((match) => {
                const isRevealed = revealedMatches[match.match_id] || match.reveal_status === "REVEALED";
                return (
                  <div 
                    key={match.match_id}
                    className="bg-gradient-to-r from-indigo-950/60 via-[#15181F] to-slate-900 border border-[#7C6CFF]/30 rounded-2xl p-5 shadow-2xl relative overflow-hidden"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded-lg bg-[#7C6CFF]/20 flex items-center justify-center text-[#7C6CFF]">
                          <Flame className="h-3.5 w-3.5 text-amber-400" />
                        </div>
                        <span className="text-xs font-bold text-white tracking-wide">
                          Top Serendipity Match Found
                        </span>
                        <span className="text-[10px] font-mono text-[#0EC9A7] bg-[#0EC9A7]/10 px-2 py-0.2 rounded border border-[#0EC9A7]/20">
                          {match.synergy_score}% Asymmetric Fit
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {match.distance_miles} mi away on campus
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-white mb-2">
                      {match.peer_title}
                    </h4>

                    {/* Meta AI Muse Wonder Bridge Sentence */}
                    <div className="bg-[#07080A]/70 border border-white/[0.08] rounded-xl p-3 my-2 text-xs">
                      <div className="flex items-center gap-1 text-[11px] font-bold text-[#7C6CFF] mb-1">
                        <Zap className="h-3.5 w-3.5 text-amber-400" />
                        Meta Muse Wonder 1.0 Explainable Synthesis:
                      </div>
                      <p className="text-slate-300 italic text-[11px] leading-relaxed">
                        &ldquo;{match.bridge_sentence}&rdquo;
                      </p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-white/[0.08] flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs text-slate-400">
                        <GraduationCap className="h-4 w-4 text-slate-500" />
                        <span>{match.peer_department}</span>
                      </div>

                      {isRevealed ? (
                        <span className="text-xs font-bold text-[#0EC9A7] flex items-center gap-1">
                          <Unlock className="h-3.5 w-3.5" /> Mutually Unlocked
                        </span>
                      ) : (
                        <button
                          onClick={() => handleReveal(match.match_id)}
                          className="px-3.5 py-1.5 bg-[#7C6CFF] hover:bg-[#6857eb] text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 shadow-lg shadow-[#7C6CFF]/20"
                        >
                          <Lock className="h-3.5 w-3.5" />
                          Double Opt-In Reveal
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Feed Filter Chips */}
              <div className="flex items-center gap-2 pb-1 overflow-x-auto">
                {["All", "Computer Science", "Biomedical Engineering", "Electrical Engineering", "Hypothesis Stage"].map((f) => (
                  <button
                    key={f}
                    onClick={() => setFeedFilter(f)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                      feedFilter === f
                        ? "bg-white text-black font-bold"
                        : "bg-[#0E1015] text-slate-400 hover:text-white border border-white/[0.08]"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>

              {/* Feed Project Stream */}
              <div className="space-y-4">
                {projects.map((proj) => (
                  <article 
                    key={proj.project_id}
                    className="bg-[#0E1015] border border-white/[0.08] rounded-2xl p-5 hover:border-white/[0.16] transition-all space-y-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-slate-800 to-slate-700 flex items-center justify-center font-bold text-xs text-white border border-white/[0.08]">
                          {proj.department.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <span className="text-[11px] font-mono font-semibold text-[#7C6CFF]">
                            {proj.department} • {proj.degree_level}
                          </span>
                          <h3 className="text-sm font-bold text-white mt-0.5 leading-snug">
                            {proj.title}
                          </h3>
                        </div>
                      </div>

                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-white/[0.06]">
                        {proj.stage}
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      {proj.teaser}
                    </p>

                    {/* Offers & Needs Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 text-xs">
                      <div className="bg-[#15181F]/70 rounded-xl p-2.5 border border-white/[0.04]">
                        <span className="text-[10px] uppercase font-bold text-[#0EC9A7] block mb-1.5 flex items-center gap-1">
                          <span className="text-[9px] font-bold">[+]</span> Offers (Can Provide)
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {proj.offers.map((off, i) => (
                            <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-[#0EC9A7]/10 text-[#0EC9A7] border border-[#0EC9A7]/20">
                              {off}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="bg-[#15181F]/70 rounded-xl p-2.5 border border-white/[0.04]">
                        <span className="text-[10px] uppercase font-bold text-[#FFB224] block mb-1.5 flex items-center gap-1">
                          <span className="text-[9px] font-bold">[○]</span> Needs (Seeking)
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {proj.needs.map((nd, i) => (
                            <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-[#FFB224]/10 text-[#FFB224] border border-[#FFB224]/20">
                              {nd}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Action Bar */}
                    <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-xs text-slate-400">
                      <span className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
                        <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
                        {proj.certificate_id || "Vault Anchored"}
                      </span>

                      <button 
                        onClick={() => setActiveScreen("pod")}
                        className="px-3 py-1.5 bg-[#1D212B] hover:bg-[#7C6CFF] hover:text-white text-slate-200 rounded-lg text-xs font-semibold transition-all flex items-center gap-1"
                      >
                        Request Connection <ArrowRight className="h-3 w-3" />
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </main>

            {/* Right 3 Cols: Active Pods & Grant Opportunities */}
            <aside className="lg:col-span-3 space-y-4">
              <div className="bg-[#0E1015] border border-white/[0.08] rounded-2xl p-5 space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Flame className="h-4 w-4 text-amber-400" />
                  Upcoming Grant Deadlines
                </h4>

                <div className="space-y-3 pt-2 text-xs">
                  <div className="p-3 rounded-xl bg-[#15181F] border border-white/[0.06] space-y-1">
                    <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase">NSF CRII $175K</span>
                    <h5 className="font-semibold text-white">Robust Edge Swarms & Decentralized AI</h5>
                    <p className="text-[11px] text-slate-400">Deadline: in 24 days • 3 faculty PIs looking for student co-leads.</p>
                  </div>

                  <div className="p-3 rounded-xl bg-[#15181F] border border-white/[0.06] space-y-1">
                    <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase">NIH R21 $275K</span>
                    <h5 className="font-semibold text-white">Continuous Ambulatory Biometric Meshes</h5>
                    <p className="text-[11px] text-slate-400">Deadline: in 41 days • Cross-listed with BME & Computer Science.</p>
                  </div>
                </div>
              </div>
            </aside>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* SCREEN 1: RESEARCH POD HEADQUARTERS — STUDIO MODE             */}
      {/* (Linear/Figma velocity + Overleaf split-screen paper rigor)    */}
      {/* ------------------------------------------------------------- */}
      {activeScreen === "pod" && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* A. Pod Presence Bar */}
          <div className="h-14 border-b border-white/[0.08] bg-[#0E1015] px-6 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <h2 className="text-base font-serif font-bold text-white tracking-wide">
                Pod: Autonomous Swarm Robotics x Clinical Triage
              </h2>
              <span className="text-[10px] font-mono uppercase bg-indigo-500/10 text-indigo-300 px-2 py-0.5 rounded border border-indigo-500/20">
                NSF Seed Track
              </span>
            </div>

            {/* Active Teammates Facepile */}
            <div className="flex items-center gap-4">
              <div className="flex items-center -space-x-2">
                <div className="h-8 w-8 rounded-full bg-indigo-600 border-2 border-[#0E1015] flex items-center justify-center text-xs font-bold text-white" title="Anurag (Lead PI) - Editing Methods">
                  A
                </div>
                <div className="h-8 w-8 rounded-full bg-emerald-600 border-2 border-[#0E1015] flex items-center justify-center text-xs font-bold text-white" title="Maya Patel (Clinical Co-PI) - Reviewing Evidence">
                  M
                </div>
                <div className="h-8 w-8 rounded-full bg-amber-600 border-2 border-[#0E1015] flex items-center justify-center text-xs font-bold text-white" title="Marcus Vance (Hardware Fellow) - Online">
                  V
                </div>
              </div>
              <span className="text-xs text-slate-400 font-mono flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-[#0EC9A7] animate-pulse" />
                3 Researchers Online
              </span>
            </div>
          </div>

          {/* B. Milestone Stepper */}
          <div className="h-12 border-b border-white/[0.06] bg-[#15181F] px-6 flex items-center justify-between text-xs">
            <div className="flex items-center gap-6">
              {[
                { step: 0, label: "1. Literature Discovery", done: true },
                { step: 1, label: "2. Evidence Assembly", done: true },
                { step: 2, label: "3. Collaborative Drafting", active: true },
                { step: 3, label: "4. Peer Review Simulation", pending: true },
                { step: 4, label: "5. Final Submission", pending: true }
              ].map((m) => (
                <button
                  key={m.step}
                  onClick={() => setActiveMilestone(m.step)}
                  className={`flex items-center gap-1.5 font-medium transition-all ${
                    m.done 
                      ? "text-[#0EC9A7]" 
                      : m.active 
                      ? "text-white font-bold border-b-2 border-[#7C6CFF] py-3" 
                      : "text-slate-500"
                  }`}
                >
                  {m.done && <Check className="h-3.5 w-3.5 text-[#0EC9A7]" />}
                  {m.active && <span className="h-2 w-2 rounded-full bg-[#7C6CFF] animate-ping" />}
                  <span>{m.label}</span>
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono text-slate-400">Readiness Score: <strong>88/100</strong></span>
              <button className="px-3 py-1 bg-white hover:bg-slate-200 text-black rounded-lg text-xs font-bold transition-all">
                Export to LaTeX
              </button>
            </div>
          </div>

          {/* Split Pane: Left Evidence Cards (40%) | Right Paper Editor (60%) */}
          <div className="flex-1 flex min-h-0">
            {/* Left Evidence Board */}
            <div className="w-[42%] border-r border-white/[0.08] bg-[#07080A] p-5 overflow-y-auto space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Shared Literature Evidence Board
                  </h3>
                  <p className="text-[11px] text-slate-500">Peer-reviewed foundational citations pinned by team</p>
                </div>
                <span className="text-xs font-mono text-indigo-400">4 Papers Selected</span>
              </div>

              {/* Evidence Cards */}
              {[
                {
                  id: "ev_1",
                  title: "Merlin's Whisper: Enabling Efficient Reasoning in Large Language Models",
                  authors: "Xia et al. (2024)",
                  doi: "arXiv:2510.10528",
                  relevance: "96%",
                  verdict: "Supports",
                  badgeColor: "emerald",
                  pinnedBy: "Maya Patel",
                  quote: "Consistently reduces token usage by 42% while preserving step-by-step mathematical reasoning accuracy."
                },
                {
                  id: "ev_2",
                  title: "Decentralized Byzantine Fault Tolerant Control for Swarm Robotics",
                  authors: "Rostova et al. (2024)",
                  doi: "IEEE Transactions on Robotics",
                  relevance: "92%",
                  verdict: "Methodology",
                  badgeColor: "blue",
                  pinnedBy: "Anurag",
                  quote: "Demonstrates asymptotic convergence in 64-agent micro-quadrotor swarms under 35% packet loss."
                }
              ].map((ev) => (
                <div 
                  key={ev.id}
                  className="bg-[#0E1015] border border-white/[0.08] hover:border-indigo-500/40 rounded-xl p-4 space-y-2.5 transition-all"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      {ev.relevance} Match • {ev.verdict}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">Pinned by {ev.pinnedBy}</span>
                  </div>

                  <h4 className="text-xs font-bold text-white leading-snug">
                    {ev.title}
                  </h4>
                  <p className="text-[11px] text-slate-400 font-mono">
                    {ev.authors} • {ev.doi}
                  </p>

                  <div className="bg-[#15181F] p-2.5 rounded-lg border border-white/[0.04] text-[11px] text-slate-300 italic">
                    &ldquo;{ev.quote}&rdquo;
                  </div>

                  <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between text-xs">
                    <button className="text-indigo-400 hover:text-indigo-300 text-[11px] font-semibold flex items-center gap-1">
                      <Pin className="h-3 w-3" /> Pin Citation to Section 2
                    </button>
                    <button className="text-slate-400 hover:text-white text-[11px]">
                      View SAM 3.1 Figure ➔
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Right Split Editor (Bright Paper on Dark OS) */}
            <div className="flex-1 bg-[#15181F] p-6 overflow-y-auto flex justify-center">
              <div className="w-full max-w-3xl bg-[#F7F6F3] text-[#101218] rounded-xl shadow-2xl p-8 space-y-4 font-sans border border-slate-300">
                <div className="border-b border-slate-300 pb-3 flex items-center justify-between text-xs text-slate-500">
                  <span className="font-mono uppercase font-bold text-slate-600">
                    Live Proposal Draft • Collaborative Editor
                  </span>
                  <span>Auto-saved · 3 carets active</span>
                </div>

                <textarea
                  rows={18}
                  value={proposalText}
                  onChange={(e) => setProposalText(e.target.value)}
                  className="w-full bg-transparent border-0 p-0 text-sm text-[#101218] font-sans leading-relaxed focus:outline-none resize-none"
                />

                <div className="mt-4 p-3 rounded-lg bg-indigo-50 border border-indigo-200 text-xs text-indigo-900 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-indigo-600" />
                    <span><strong>Meta Muse Wonder Inline Review:</strong> All citations verified against local peer-reviewed library. 0% hallucination risk.</span>
                  </div>
                  <span className="font-mono text-indigo-700 font-bold">Grade: 94/100</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* SCREEN 2: PRIVATE VAULT & TEASER APPROVAL                     */}
      {/* (Local-file protection + SHA-256 certificate + Preview As)    */}
      {/* ------------------------------------------------------------- */}
      {activeScreen === "vault" && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-[1200px] mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left 6 Cols: Local Hashing & Certificate */}
            <div className="lg:col-span-6 bg-[#0E1015] border border-white/[0.08] rounded-2xl p-6 space-y-5">
              <div>
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-[#7C6CFF]" />
                  <h2 className="text-base font-bold text-white">
                    Private Vault & Priority Insurance
                  </h2>
                </div>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Seal your early hypotheses locally before discussing with anyone. Proof of priority is anchored via SHA-256 to Base Sepolia, insuring your idea against scooping.
                </p>
              </div>

              <form onSubmit={handleSealHypothesis} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Project / Hypothesis Title
                  </label>
                  <input
                    type="text"
                    value={vaultTitle}
                    onChange={(e) => setVaultTitle(e.target.value)}
                    placeholder="e.g. Byzantine Consensus for Drone Swarms under Noise"
                    className="w-full bg-[#07080A] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-[#7C6CFF]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Raw Hypothesis & Secret Sauce (Never Leaves Device)
                  </label>
                  <textarea
                    rows={4}
                    value={vaultText}
                    onChange={(e) => setVaultText(e.target.value)}
                    placeholder="Describe your raw mathematical formulation, target dataset, or algorithmic architecture. This remains 100% encrypted locally."
                    className="w-full bg-[#07080A] border border-white/[0.08] rounded-xl p-3.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-[#7C6CFF] font-mono"
                  />
                </div>

                {/* Scramble Hash Box */}
                <div className="bg-[#07080A] border border-white/[0.06] rounded-xl p-3.5 space-y-1.5 font-mono text-[11px]">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <Lock className="h-3 w-3 text-[#0EC9A7]" />
                      Local SHA-256 Fingerprint:
                    </span>
                    <span className="text-[10px] text-slate-500">Base Sepolia Block #18473920</span>
                  </div>
                  <div className="text-indigo-300 break-all bg-black/40 p-2 rounded border border-white/[0.04]">
                    {scrambleHash}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSealing || !vaultTitle || !vaultText}
                  className="w-full py-2.5 bg-[#7C6CFF] hover:bg-[#6857eb] text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-[#7C6CFF]/25 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <ShieldCheck className="h-4 w-4" />
                  {isSealing ? "Scrambling & Anchoring Proof..." : "Seal Idea & Issue Proof Certificate"}
                </button>
              </form>

              {/* Perforated Certificate Receipt */}
              <div className="border border-dashed border-white/[0.14] bg-[#15181F] rounded-2xl p-5 space-y-3 font-mono text-xs relative">
                <div className="flex items-center justify-between border-b border-white/[0.08] pb-2">
                  <span className="text-[10px] uppercase tracking-wider text-[#0EC9A7] font-bold">
                    Official Priority Certificate
                  </span>
                  <span className="text-slate-400 font-bold">
                    {sealedCert ? sealedCert.certificate_id : "NX-8492"}
                  </span>
                </div>
                <div className="space-y-1.5 text-slate-300 text-[11px]">
                  <div>Author: Anurag (MSCS '26 • Computer Science)</div>
                  <div>Anchored: Base Sepolia #18473920</div>
                  <div>Verified: Mathematical priority established pre-publication.</div>
                </div>
              </div>
            </div>

            {/* Right 6 Cols: Audience Preview Mode */}
            <div className="lg:col-span-6 bg-[#0E1015] border border-white/[0.08] rounded-2xl p-6 space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Eye className="h-4 w-4 text-[#7C6CFF]" />
                    Audience Preview Mode
                  </h3>
                  <p className="text-xs text-slate-400">
                    Verify how your project looks to strangers vs peers before publishing
                  </p>
                </div>

                <div className="flex items-center gap-1 bg-[#07080A] p-1 rounded-lg border border-white/[0.08]">
                  {(["stranger", "peer", "professor"] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setPreviewAs(mode)}
                      className={`px-2.5 py-1 rounded text-xs capitalize transition-all ${
                        previewAs === mode ? "bg-[#7C6CFF] text-white font-bold" : "text-slate-400 hover:text-white"
                      }`}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>

              {/* Live Preview Card */}
              <div className="bg-[#15181F] border border-white/[0.08] rounded-2xl p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono text-indigo-400 font-bold uppercase">
                    Computer Science • {previewAs === "stranger" ? "Anonymous Student" : "MSCS '26"}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    Teaser Mode
                  </span>
                </div>

                <h4 className="text-sm font-bold text-white">
                  {vaultTitle || "Decentralized Byzantine Consensus for Autonomous Swarm Robotics"}
                </h4>

                <p className="text-xs text-slate-300 leading-relaxed">
                  Developing low-latency consensus protocols for UAV swarms under adversarial wireless interference. Raw code and proprietary proofs sealed in vault.
                </p>

                <div className="space-y-2 pt-2">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] uppercase font-bold text-[#0EC9A7]">[+] Offer:</span>
                    <span className="text-[11px] text-slate-300 font-mono">Distributed consensus, CUDA kernels, ROS2</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] uppercase font-bold text-[#FFB224]">[○] Need:</span>
                    <span className="text-[11px] text-slate-300 font-mono">Real-world UAV flight arena, clinical validation</span>
                  </div>
                </div>

                <div className="pt-3 border-t border-white/[0.06] text-right">
                  <span className="text-[11px] text-emerald-400 font-bold">
                    ✓ Verified Safe: Zero proprietary secrets leaked in this view.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* SCREEN 4: PIXEL-TO-PROOF GROUNDING & SAM 3.1 VISUAL AUDIT     */}
      {/* ------------------------------------------------------------- */}
      {activeScreen === "proof" && (
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="max-w-[1200px] mx-auto space-y-5">
            <div className="bg-[#0E1015] border border-white/[0.08] rounded-2xl p-5 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-[#0EC9A7]" />
                  Anti-Hallucination Pixel-to-Proof Grounding Studio
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Every proposal claim is grounded down to the exact pixel of the source peer-reviewed paper using Meta SAM 3.1.
                </p>
              </div>

              <span className="px-3 py-1 rounded-full bg-[#0EC9A7]/10 text-[#0EC9A7] text-xs font-mono border border-[#0EC9A7]/20 font-bold">
                100% Grounded Evidence
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Proposal Text Claim */}
              <div className="lg:col-span-5 bg-[#0E1015] border border-white/[0.08] rounded-2xl p-6 space-y-4">
                <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
                  Synthesized Grant Claim #CLAIM-4B
                </span>

                <div className="bg-[#15181F] border border-white/[0.08] rounded-xl p-4 text-xs space-y-2">
                  <p className="text-slate-200 leading-relaxed">
                    &ldquo;Under adversarial wireless conditions with 40% packet drops, the distributed consensus protocol sustains <span className="bg-[#0EC9A7]/20 text-[#0EC9A7] px-1 py-0.5 rounded border border-[#0EC9A7]/30 font-bold">94% throughput with sub-50ms latency</span>, outperforming Raft and Paxos baselines by 3.8x.&rdquo;
                  </p>
                  <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-slate-400">
                    <span>Citation: [Xia et al., 2024]</span>
                    <span className="text-[#0EC9A7] font-bold">Figure 4(b)</span>
                  </div>
                </div>

                <div className="bg-[#7C6CFF]/10 border border-[#7C6CFF]/20 rounded-xl p-3 text-xs space-y-1">
                  <div className="flex items-center gap-1.5 text-indigo-300 font-bold text-[11px]">
                    <Zap className="h-3.5 w-3.5 text-amber-400" />
                    Meta Muse Wonder 1.0 Reasoner Verification:
                  </div>
                  <p className="text-slate-300 italic text-[11px]">
                    &ldquo;Verified claim matches experimental throughput curve in Figure 4b. Error bars confirm 95% confidence interval across 100 trials.&rdquo;
                  </p>
                </div>
              </div>

              {/* Source PDF SAM 3.1 Highlighting Canvas */}
              <div className="lg:col-span-7 bg-[#07080A] border border-white/[0.08] rounded-2xl p-6 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b border-white/[0.08] pb-2">
                    <span className="text-xs font-mono text-slate-300">
                      heming_merlins_whisper.pdf • Page 4
                    </span>
                    <span className="text-[10px] font-mono text-[#0EC9A7] bg-[#0EC9A7]/10 px-2 py-0.5 rounded border border-[#0EC9A7]/20">
                      SAM 3.1 Polygon Mask #FIG-4B
                    </span>
                  </div>

                  <div className="h-64 bg-[#0E1015] border border-white/[0.08] rounded-xl relative overflow-hidden flex items-center justify-center">
                    <div className="absolute inset-8 border-2 border-dashed border-[#0EC9A7] bg-[#0EC9A7]/10 rounded-xl flex flex-col items-center justify-center p-4">
                      <div className="w-full bg-[#15181F]/90 rounded-lg p-3 border border-[#0EC9A7]/40 space-y-2">
                        <div className="flex justify-between text-[10px] font-mono text-[#0EC9A7]">
                          <span>Figure 4(b): Throughput vs Packet Loss</span>
                          <span>SAM 3.1 Confidence: 0.985</span>
                        </div>
                        <div className="h-16 flex items-end gap-3 px-4">
                          <div className="w-8 h-6 bg-slate-700 rounded-t" />
                          <div className="w-8 h-9 bg-slate-600 rounded-t" />
                          <div className="w-8 h-12 bg-indigo-500 rounded-t" />
                          <div className="w-8 h-16 bg-[#0EC9A7] rounded-t shadow-lg shadow-[#0EC9A7]/50" />
                        </div>
                        <span className="text-[9px] text-slate-400 font-mono text-center block">
                          Bounding Box: [x: 142.5, y: 320.0, w: 337.5, h: 290.5]
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-3 text-right">
                  <span className="text-[11px] text-slate-400 font-mono">
                    Audit Token Usage: 368 reasoning tokens • 0ms latency from cache
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
