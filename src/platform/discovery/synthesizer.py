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
        title_str = m.get('title', '')
        if 'Computing' in title_str:
            colleges_involved.add('Computing & Information Sciences')
        elif 'Engineering' in title_str:
            colleges_involved.add('Engineering')
        elif 'Science' in title_str:
            colleges_involved.add('Science & Mathematics')

    if len(colleges_involved) >= 2:
        synergy = f"High interdisciplinary potential connecting {', '.join(sorted(colleges_involved))}. This collaborative structure strengthens broader impacts for major center and collaborative grant solicitations."
    else:
        synergy = "Focused single-domain proposal. Consider partnering with external application domains or human factors researchers to enhance broader impacts criteria."

    # 6. Specific Aims Suggestions
    suggested_aims = [
        f"Specific Aim 1: Formalize theoretical and algorithmic foundations for {title.lower()}.",
        f"Specific Aim 2: Develop robust experimental prototypes and evaluate against verified baseline benchmarks in {detected_domains[0]}.",
        f"Specific Aim 3: Validate deployment scalability, ethical considerations, and real-world applicability with domain stakeholders."
    ]

    # Executive novelty summary
    top_domains_str = ', '.join(detected_domains[:3])
    novelty = (
        f"The proposed initiative addresses key research challenges bridging {top_domains_str}. "
        f"By combining foundational methodology with empirical validation, the project offers competitive alignment with {matched_agencies[0]['agency']} priorities."
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
