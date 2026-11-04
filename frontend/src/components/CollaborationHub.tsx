'use client';

import { useState } from 'react';
import {
  Rocket,
  Target,
  Users,
  Loader2,
  BookmarkPlus,
  Paperclip,
  ExternalLink,
  Award,
  Globe,
  CheckCircle2,
  Compass,
  AlertCircle,
} from 'lucide-react';
import {
  api,
  type CollaboratorMatch,
  type ImpactAnalysis,
} from '@/lib/api';

type CollaborationHubProps = {
  onAttachSource?: (sourceId: string) => Promise<void>;
  onShortlist?: (sourceId: string, title: string, rationale: string) => Promise<void>;
  attachedSourceIds?: string[];
  proposalOpen?: boolean;
};

const SUGGESTIONS = [
  {
    title: 'Self-Supervised Vision Transformers for Crop Disease Detection',
    college: 'Computing',
    tags: 'computer vision, agriculture, transformers, deep learning',
    description: 'Developing lightweight self-supervised visual representation models capable of on-drone leaf lesion classification under variable lighting and occlusion in rural agricultural fields.'
  },
  {
    title: 'Adversarial Defense and Privacy-Preserving Federated Healthcare',
    college: 'Computing',
    tags: 'cybersecurity, healthcare, federated learning, privacy',
    description: 'Investigating differential privacy bounds and Byzantine-resilient aggregation algorithms for decentralized clinical MRI diagnostics across multi-hospital research networks.'
  },
  {
    title: 'Assistive Wearable Gaze-Tracking for Motor-Impaired Mobility',
    college: 'Computing',
    tags: 'human-computer interaction, accessibility, sensors, robotics',
    description: 'Designing low-latency optical gaze-estimation interfaces integrated with powered wheelchair controllers for neurodivergent and spinal-injury rehabilitation patients.'
  }
];

export default function CollaborationHub({
  onAttachSource,
  onShortlist,
  attachedSourceIds = [],
  proposalOpen = false,
}: CollaborationHubProps) {
  const [formData, setFormData] = useState({
    title: '',
    college: 'Computing',
    tags: '',
    description: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [impact, setImpact] = useState<ImpactAnalysis | null>(null);
  const [matches, setMatches] = useState<CollaboratorMatch[]>([]);
  const [shortlistedIds, setShortlistedIds] = useState<Set<string>>(new Set());

  const handleApplySuggestion = (s: typeof SUGGESTIONS[0]) => {
    setFormData(s);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.description.trim()) return;

    setLoading(true);
    setError('');
    try {
      const res = await api.synthesizeIdea({
        title: formData.title.trim(),
        description: formData.description.trim(),
        college: formData.college,
        tags: formData.tags.trim(),
      });
      setImpact(res.impact_analysis);
      setMatches(res.matches);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not synthesize research idea.');
    } finally {
      setLoading(false);
    }
  };

  const handleShortlistClick = async (m: CollaboratorMatch) => {
    if (!onShortlist) return;
    try {
      await onShortlist(m.source_id, m.title, m.reason);
      setShortlistedIds(prev => new Set(prev).add(m.source_id));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to shortlist candidate.');
    }
  };

  const handleAttachClick = async (sourceId: string) => {
    if (!onAttachSource) return;
    try {
      await onAttachSource(sourceId);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to attach source.');
    }
  };

  return (
    <div className="collaboration-hub-root" style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 420px) 1fr', gap: '20px', height: '100%', overflow: 'hidden' }}>
      {/* LEFT COLUMN: IDEA INPUT & STARTERS */}
      <div className="hub-input-panel" style={{ background: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Rocket className="w-5 h-5 text-blue-600" />
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', margin: 0 }}>Research Idea Matrix</h2>
          </div>
          <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>
            Submit your research concept. The platform evaluates academic novelty, federal funding alignment, and matches verified faculty leads.
          </p>
        </div>

        {/* Suggestion Chips */}
        <div>
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '6px' }}>
            Quick Exemplars
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {SUGGESTIONS.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleApplySuggestion(s)}
                style={{
                  textAlign: 'left',
                  fontSize: '11px',
                  padding: '6px 10px',
                  borderRadius: '6px',
                  border: '1px solid #e2e8f0',
                  background: '#f8fafc',
                  color: '#334155',
                  cursor: 'pointer',
                  lineHeight: '1.4',
                }}
              >
                💡 {s.title}
              </button>
            ))}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <label style={{ fontSize: '11px', fontWeight: 600, color: '#475569', display: 'block', marginBottom: '4px' }}>
              Project Title *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={e => setFormData({ ...formData, title: e.target.value })}
              placeholder="e.g. Robust Edge Vision for Precision Agriculture"
              style={{ width: '100%', fontSize: '12px', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none' }}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label style={{ fontSize: '11px', fontWeight: 600, color: '#475569', display: 'block', marginBottom: '4px' }}>
                Primary College
              </label>
              <select
                value={formData.college}
                onChange={e => setFormData({ ...formData, college: e.target.value })}
                style={{ width: '100%', fontSize: '12px', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', background: '#fff' }}
              >
                <option value="Computing">Computing & Info</option>
                <option value="Engineering">Engineering</option>
                <option value="Science">Science & Math</option>
                <option value="Health Sciences">Health Sciences</option>
                <option value="Business">Business</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '11px', fontWeight: 600, color: '#475569', display: 'block', marginBottom: '4px' }}>
                Keywords / Tags
              </label>
              <input
                type="text"
                value={formData.tags}
                onChange={e => setFormData({ ...formData, tags: e.target.value })}
                placeholder="ai, robotics, sensors"
                style={{ width: '100%', fontSize: '12px', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none' }}
              />
            </div>
          </div>

          <div>
            <label style={{ fontSize: '11px', fontWeight: 600, color: '#475569', display: 'block', marginBottom: '4px' }}>
              Idea Description & Technical Methodology *
            </label>
            <textarea
              value={formData.description}
              onChange={e => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe your research hypothesis, technical approach, and anticipated outcomes in detail..."
              rows={5}
              style={{ width: '100%', fontSize: '12px', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', resize: 'vertical' }}
              required
            />
          </div>

          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#b91c1c', background: '#fef2f2', padding: '8px', borderRadius: '6px' }}>
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '10px 16px',
              borderRadius: '6px',
              border: 'none',
              background: '#2563eb',
              color: '#ffffff',
              fontSize: '12px',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              transition: 'background 0.15s ease',
            }}
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Target className="w-4 h-4" />}
            {loading ? 'Synthesizing Idea Matrix…' : 'Analyze & Match Collaborators'}
          </button>
        </form>
      </div>

      {/* RIGHT COLUMN: SYNTHESIS RESULTS */}
      <div className="hub-results-panel" style={{ background: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', padding: '24px', overflowY: 'auto' }}>
        {!impact && !loading && (
          <div style={{ height: '100%', minHeight: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', textAlign: 'center' }}>
            <Compass className="w-12 h-12 text-slate-300" style={{ marginBottom: '12px' }} />
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#334155', margin: '0 0 6px 0' }}>Ready for Idea Synthesis</h3>
            <p style={{ fontSize: '12px', color: '#64748b', maxWidth: '380px', margin: 0 }}>
              Submit your project aims on the left or select a quick exemplar to discover funding agency fit, specific aim recommendations, and verified faculty collaborator matches.
            </p>
          </div>
        )}

        {loading && (
          <div style={{ height: '100%', minHeight: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#2563eb' }}>
            <Loader2 className="w-8 h-8 animate-spin" style={{ marginBottom: '12px' }} />
            <p style={{ fontSize: '13px', fontWeight: 600, margin: 0 }}>Evaluating Academic Novelty & Querying 3,000+ Sources…</p>
            <span style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>Matching cross-disciplinary faculty leads and funding programs</span>
          </div>
        )}

        {impact && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* NOVELTY & EXECUTIVE SUMMARY */}
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                <Award className="w-4 h-4 text-indigo-600" />
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#1e293b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Scientific Novelty & Executive Synthesis
                </span>
              </div>
              <p style={{ fontSize: '13px', color: '#334155', lineHeight: '1.6', margin: 0 }}>
                {impact.novelty_summary}
              </p>

              {/* Domains */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '12px' }}>
                {impact.detected_domains.map((dom, i) => (
                  <span key={i} style={{ fontSize: '11px', background: '#e0e7ff', color: '#3730a3', padding: '3px 8px', borderRadius: '4px', fontWeight: 500 }}>
                    🏷️ {dom}
                  </span>
                ))}
              </div>
            </div>

            {/* FUNDING ALIGNMENT & SPECIFIC AIMS GRID */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
              {/* Target Agencies */}
              <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px', background: '#fafafa' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '10px' }}>
                  <Award className="w-3.5 h-3.5 text-amber-500" /> Target Federal Funding Fit
                </span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {impact.target_agencies.map((agency, i) => (
                    <div key={i} style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '8px 10px' }}>
                      <strong style={{ fontSize: '12px', color: '#0f172a', display: 'block' }}>{agency.agency}</strong>
                      <span style={{ fontSize: '11px', color: '#64748b' }}>
                        Programs: {agency.suggested_programs.join(' · ')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* UN SDGs & Synergies */}
              <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px', background: '#fafafa' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '10px' }}>
                  <Globe className="w-3.5 h-3.5 text-emerald-600" /> Interdisciplinary Synergies
                </span>
                <p style={{ fontSize: '12px', color: '#334155', lineHeight: '1.5', margin: '0 0 10px 0' }}>
                  {impact.interdisciplinary_synergies}
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {impact.aligned_sdgs.map((sdg, i) => (
                    <span key={i} style={{ fontSize: '10px', background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#065f46', padding: '2px 6px', borderRadius: '4px' }}>
                      {sdg}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* RECOMMENDED SPECIFIC AIMS */}
            <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px', background: '#f8fafc' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
                📋 Suggested Proposal Specific Aims Framework
              </span>
              <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {impact.suggested_aims.map((aim, i) => (
                  <li key={i} style={{ fontSize: '12px', color: '#334155', lineHeight: '1.5' }}>
                    {aim}
                  </li>
                ))}
              </ul>
            </div>

            {/* MATCHED FACULTY COLLABORATORS */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Users className="w-4 h-4 text-blue-600" />
                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                    Verified Faculty Collaborator Leads ({matches.length})
                  </h4>
                </div>
                <span style={{ fontSize: '11px', color: '#64748b' }}>
                  Ranked by publication & profile evidence coverage
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {matches.map((m) => {
                  const isShortlisted = shortlistedIds.has(m.source_id);
                  const isAttached = attachedSourceIds.includes(m.source_id);

                  return (
                    <div
                      key={m.source_id}
                      style={{
                        background: '#ffffff',
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px',
                        padding: '12px 14px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px',
                        transition: 'border-color 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <strong style={{ fontSize: '13px', color: '#0f172a' }}>{m.title}</strong>
                          <span style={{ fontSize: '11px', color: '#64748b', marginLeft: '8px' }}>
                            ({m.candidate_status.replace('_', ' ')})
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontSize: '11px', fontWeight: 600, background: '#eff6ff', color: '#1d4ed8', padding: '2px 6px', borderRadius: '4px' }}>
                            {Math.round(m.idea_coverage * 100)}% Match
                          </span>
                        </div>
                      </div>

                      <p style={{ fontSize: '11px', color: '#475569', margin: 0, lineHeight: '1.4' }}>
                        {m.reason}
                      </p>

                      {/* Evidence Terms */}
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', margin: '4px 0' }}>
                        {m.evidence_terms.slice(0, 5).map((term, i) => (
                          <span key={i} style={{ fontSize: '10px', background: '#f1f5f9', color: '#475569', padding: '1px 5px', borderRadius: '3px' }}>
                            ✓ {term}
                          </span>
                        ))}
                      </div>

                      {/* Action Bar */}
                      <div style={{ display: 'flex', gap: '8px', marginTop: '4px', borderTop: '1px solid #f1f5f9', paddingTop: '8px' }}>
                        {onShortlist && (
                          <button
                            type="button"
                            onClick={() => handleShortlistClick(m)}
                            disabled={isShortlisted}
                            style={{
                              fontSize: '11px',
                              padding: '4px 8px',
                              borderRadius: '4px',
                              border: isShortlisted ? '1px solid #86efac' : '1px solid #cbd5e1',
                              background: isShortlisted ? '#f0fdf4' : '#ffffff',
                              color: isShortlisted ? '#15803d' : '#334155',
                              cursor: isShortlisted ? 'default' : 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                            }}
                          >
                            {isShortlisted ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <BookmarkPlus className="w-3.5 h-3.5 text-blue-600" />}
                            {isShortlisted ? 'Shortlisted' : 'Shortlist Candidate'}
                          </button>
                        )}

                        {proposalOpen && onAttachSource && (
                          <button
                            type="button"
                            onClick={() => handleAttachClick(m.source_id)}
                            disabled={isAttached}
                            style={{
                              fontSize: '11px',
                              padding: '4px 8px',
                              borderRadius: '4px',
                              border: isAttached ? '1px solid #cbd5e1' : '1px solid #cbd5e1',
                              background: isAttached ? '#f8fafc' : '#ffffff',
                              color: isAttached ? '#94a3b8' : '#334155',
                              cursor: isAttached ? 'default' : 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                            }}
                          >
                            <Paperclip className="w-3.5 h-3.5 text-indigo-600" />
                            {isAttached ? 'Attached to Proposal' : 'Attach to Proposal'}
                          </button>
                        )}

                        {m.origin && (
                          <a
                            href={m.origin}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              fontSize: '11px',
                              color: '#64748b',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '3px',
                              marginLeft: 'auto',
                              textDecoration: 'none',
                            }}
                          >
                            Profile <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <p style={{ fontSize: '11px', color: '#94a3b8', fontStyle: 'italic', margin: '8px 0 0 0' }}>
              * {impact.disclaimer}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
