"""Research idea synthesis, federal funding alignment, and collaborator matchmaking."""

from __future__ import annotations

import re
from typing import Any
from sqlalchemy.orm import Session

from .matching import match_collaborators
from ..discovery.graph import CONCEPT_TAXONOMY


AGENCY_DOMAINS = [
    {
        'agency': 'NSF CISE (Computer & Information Science & Engineering)',
        'keywords': ['ai', 'machine learning', 'computer vision', 'natural language', 'robotics', 'software engineering', 'theory', 'algorithms'],
        'programs': ['Core Programs (IIS, CCF, CNS)', 'CAREER Award', 'National AI Research Institutes']
    },
    {
        'agency': 'NIH (National Institutes of Health)',
        'keywords': ['biomedical', 'health', 'clinical', 'medical', 'neuroscience', 'bioinformatics'],
        'programs': ['R01 Research Project Grant', 'R21 Exploratory Grant', 'BRAIN Initiative']
    },
    {
        'agency': 'DARPA (Defense Advanced Research Projects Agency)',
        'keywords': ['autonomous', 'cybersecurity', 'adversarial', 'quantum', 'robotics', 'sensing'],
        'programs': ['Young Faculty Award (YFA)', 'Information Innovation Office (I2O)', 'Defense Sciences Office']
    },
    {
        'agency': 'DOE (Department of Energy - Office of Science)',
        'keywords': ['energy', 'battery', 'distributed systems', 'quantum', 'high performance', 'materials'],
        'programs': ['Early Career Research Program', 'Advanced Scientific Computing Research (ASCR)']
    },
    {
        'agency': 'NSF SaTC (Secure and Trustworthy Cyberspace)',
        'keywords': ['cybersecurity', 'privacy', 'cryptography', 'malware', 'zero-trust', 'authentication'],
        'programs': ['SaTC Core', 'Cybersecurity Innovation for Cyberinfrastructure (CICI)']
    }
]

SDG_MAPPINGS = [
    ('Good Health and Well-being (SDG 3)', ['biomedical', 'health', 'medical', 'clinical', 'neuroscience']),
    ('Quality Education (SDG 4)', ['education', 'pedagogy', 'curriculum', 'learning technologies']),
    ('Affordable and Clean Energy (SDG 7)', ['energy', 'battery', 'solar', 'sensor', 'power']),
    ('Industry, Innovation and Infrastructure (SDG 9)', ['robotics', 'networks', 'software', 'cloud', 'ai', 'machine learning']),
    ('Sustainable Cities and Communities (SDG 11)', ['greenhouse', 'water', 'urban', 'autonomous', 'transportation']),
    ('Climate Action (SDG 13)', ['climate', 'environmental', 'monitoring', 'remote sensing', 'weather'])
]


def synthesize_idea(
    session: Session,
    title: str,
    description: str,
    college: str | None = None,
    tags: str | None = None
) -> dict[str, Any]:
    """Analyze a research concept for novelty, funding agency alignment, and faculty collaboration leads."""
    combined_text = f"{title}. {tags or ''}. {description}".lower()

    # 1. Evidence-backed faculty matches from PostgreSQL
    match_result = match_collaborators(session, f"{title} {tags or ''} {description}"[:1000], limit=8)
    matches = match_result.get('items', [])

    # 2. Extract detected academic domains
    detected_domains = []
    for domain_name, regex_pattern in CONCEPT_TAXONOMY.items():
        if re.search(regex_pattern, combined_text, re.IGNORECASE):
            detected_domains.append(domain_name)
    if not detected_domains:
        detected_domains = ['Computer Science & Information Technology']

    # 3. Target federal funding agency alignment
    matched_agencies = []
    for entry in AGENCY_DOMAINS:
        if any(kw in combined_text for kw in entry['keywords']):
            matched_agencies.append({
                'agency': entry['agency'],
                'suggested_programs': entry['programs']
            })
    if not matched_agencies:
        matched_agencies.append({
            'agency': 'NSF (National Science Foundation) - Broad Agency Announcement',
            'suggested_programs': ['Exploratory & Early-Concept Grants for Exploratory Research (EAGER)']
        })

    # 4. UN Sustainable Development Goals (SDGs)
    aligned_sdgs = []
    for sdg_name, keywords in SDG_MAPPINGS:
        if any(kw in combined_text for kw in keywords):
            aligned_sdgs.append(sdg_name)
    if not aligned_sdgs:
        aligned_sdgs.append('Industry, Innovation and Infrastructure (SDG 9)')

    # 5. Interdisciplinary cross-departmental synergy
    colleges_involved = set()
    if college:
        colleges_involved.add(college)
    for m in matches:
        text_blob = f"{m.get('origin', '')} {m.get('snippet', '')}".lower()
        if 'computing' in text_blob or 'gccis' in text_blob or 'computer' in text_blob:
            colleges_involved.add('Golisano College of Computing & Information Sciences')
        if 'engineering' in text_blob or 'kgcoe' in text_blob or 'electrical' in text_blob or 'mechanical' in text_blob:
            colleges_involved.add('Kate Gleason College of Engineering')
        if 'science' in text_blob or 'physics' in text_blob or 'chemistry' in text_blob or 'mathematics' in text_blob:
            colleges_involved.add('College of Science')
        if 'health' in text_blob or 'medical' in text_blob or 'biomedical' in text_blob or 'clinical' in text_blob:
            colleges_involved.add('College of Health Sciences & Technology')
        if 'business' in text_blob or 'saunders' in text_blob or 'management' in text_blob:
            colleges_involved.add('Saunders College of Business')
        if 'liberal' in text_blob or 'ethics' in text_blob or 'policy' in text_blob or 'psychology' in text_blob:
            colleges_involved.add('College of Liberal Arts')

    if len(colleges_involved) >= 2:
        synergy = (
            f"High cross-college synergy identified across {', '.join(sorted(colleges_involved))}. "
            f"Teaming computational and algorithmic faculty with engineering or domain scientists significantly strengthens "
            f"the Broader Impacts and Interdisciplinary Collaboration scoring criteria required by federal review panels."
        )
    elif len(colleges_involved) == 1:
        synergy = (
            f"Core research expertise is currently anchored in {list(colleges_involved)[0]}. "
            f"For large-scale team solicitations (such as NSF Medium/Large or NIH Multi-PI), consider inviting a co-PI "
            f"from an application or human-factors department to expand translational impact."
        )
    else:
        synergy = (
            "Broad exploratory concept across multiple computing subfields. "
            "Pairing foundational algorithmic investigators with empirical or field testbed researchers will provide a competitive edge."
        )

    # 6. Specific Aims Suggestions (standard federal peer-review format)
    d1 = detected_domains[0]
    d2 = detected_domains[1] if len(detected_domains) > 1 else "Empirical Systems"
    primary_agency = matched_agencies[0]['agency']

    suggested_aims = [
        f"Specific Aim 1 (Foundations & Modeling): Formalize the theoretical and algorithmic architecture for {title.lower()}, establishing mathematical bounds and reproducible data representations in {d1}.",
        f"Specific Aim 2 (Prototyping & Benchmark Evaluation): Implement robust experimental pipelines and benchmark performance against standardized state-of-the-art baselines across {d2}.",
        f"Specific Aim 3 (Translation & Testbed Deployment): Validate scalability, robustness under real-world constraints, and usability with domain stakeholders to satisfy {primary_agency} translational milestones."
    ]

    # Executive novelty summary
    top_domains_str = ', '.join(detected_domains[:3])
    novelty = (
        f"The proposed initiative addresses high-priority scientific challenges at the intersection of {top_domains_str}. "
        f"By unifying methodological rigor with empirical validation, the project offers strong alignment with {primary_agency} solicitations. "
        f"The proposed investigation bridges theoretical foundations with actionable translational outcomes."
    )

    return {
        'impact_analysis': {
            'novelty_summary': novelty,
            'target_agencies': matched_agencies,
            'aligned_sdgs': aligned_sdgs,
            'detected_domains': detected_domains,
            'interdisciplinary_synergies': synergy,
            'suggested_aims': suggested_aims,
            'disclaimer': 'Impact and funding summaries are exploratory suggestions; collaborator matches are evidence-backed directory leads and do not automatically enroll faculty.'
        },
        'matches': matches,
        'coverage': match_result.get('coverage', {})
    }
