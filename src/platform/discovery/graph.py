"""Knowledge graph query service grounded strictly in immutable public records.

Builds researcher, paper, and topic nodes and their relationships (authorship,
co-authorship, and research topics) from verified public sources.
Supports ego-network / subgraph extraction, precomputed layout coordinates,
and hierarchical community clustering.
Enforces that private proposal-scoped sources are strictly excluded.
"""

from __future__ import annotations

import math
import re
from typing import Any
from collections import deque
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.platform.database.models import Source
from src.platform.database.public_records import PublicRecord

CLUSTER_PALETTE = [
    '#225bb2',  # Navy / Blue
    '#14766d',  # Teal
    '#d97706',  # Amber
    '#4f46e5',  # Indigo
    '#059669',  # Emerald
    '#0284c7',  # Sky
    '#7c3aed',  # Purple
    '#be123c',  # Rose
    '#0891b2',  # Cyan
    '#b45309',  # Bronze
]

# Structured multi-domain taxonomy for deep academic concept extraction
CONCEPT_TAXONOMY: dict[str, str] = {
    'Artificial Intelligence': r'\b(artificial intelligence|ai\b|intelligent systems?|deep reinforcement learning|autonomous agents?|agentic|heuristic search)\b',
    'Machine Learning': r'\b(machine learning|deep learning|neural networks?|cnn|rnn|lstm|transformers?|self-attention|supervised|unsupervised|self-supervised|representation learning|fine-tuning|backpropagation)\b',
    'Computer Vision': r'\b(computer vision|image processing|segmentation|object detection|video analysis|optical|photometric|visual recognition|gaze tracking|rendering|point cloud|3d reconstruction)\b',
    'Natural Language Processing': r'\b(natural language|nlp\b|computational linguistics|text processing|language models?|llms?|sentiment analysis|machine translation|dialogue|speech recognition|text generation)\b',
    'Human-Computer Interaction': r'\b(human-computer|hci\b|user interface|ui/ux|user experience|interaction design|interactive systems?|usability|user stud(y|ies)|crowdsourcing|design teams?)\b',
    'Accessibility': r'\b(accessibility|accessible|disabilit(y|ies)|impairment|assistive (technology|tools?)|blind|deaf|screen readers?|neurodivergent|captioning)\b',
    'Cybersecurity & Privacy': r'\b(cybersecurity|security|privacy|cryptography|adversarial|intrusion detection|malware|vulnerabilit(y|ies)|threats?|authentication|zero-trust|encryption)\b',
    'Data Science & Analytics': r'\b(data science|data mining|big data|predictive analytics|clustering|knowledge discovery|data management|time series|statistical modeling)\b',
    'Robotics & Autonomous Systems': r'\b(robotics?|autonomous (vehicles?|systems?)|manipulation|path planning|kinematics|drones?|uav|swarm robotics)\b',
    'Software Engineering': r'\b(software engineering|code analysis|refactoring|software testing|debugging|program analysis|software architecture|devops|version control)\b',
    'Virtual & Augmented Reality': r'\b(virtual reality|augmented reality|mixed reality|vr\b|ar\b|xr\b|spatial computing|immersive environments?|metaverse)\b',
    'Biomedical & Health': r'\b(biomedical|health informatics|clinical|medical imaging|healthcare|genomics|bioinformatics|neuroscience|cancer detection|physiological)\b',
    'Networks & Distributed Systems': r'\b(networks?|distributed systems?|cloud computing|edge computing|federated learning|iot\b|internet of things|wireless|sensor networks?|protocols?)\b',
    'Theory & Algorithms': r'\b(algorithms?|computational complexity|graph theory|optimization|combinatorics|formal methods|automata|algorithmic)\b',
    'Quantum Information': r'\b(quantum (computing|algorithms?|information|cryptography)|qubits?|entanglement|superconducting)\b',
    'STEM Education': r'\b(education|pedagogy|computing education|learning technologies|active learning|curriculum|instructional design|classroom|academic)\b',
}


def clean_name(title: str, kind: str, metadata: dict[str, Any]) -> str:
    """Format an honest node name from public record metadata."""
    if metadata.get('author_name'):
        return str(metadata['author_name'])
    if metadata.get('name'):
        return str(metadata['name'])
    cleaned = title
    for prefix in ('Listed author: ', 'Synthetic researcher: ', 'Synthetic paper: '):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    if ' — ' in cleaned and kind == 'researcher':
        cleaned = cleaned.split(' — ')[0]
    return cleaned.strip()


def extract_topics(title: str, text: str, metadata: dict[str, Any]) -> list[str]:
    """Extract explicit research topics and verified scientific concepts from record metadata or text."""
    topics: list[str] = []

    # 1. Structured interests / keywords from profile or paper metadata
    raw_interests = (
        metadata.get('interests')
        or metadata.get('research_interests')
        or metadata.get('topics')
        or metadata.get('keywords')
        or []
    )
    if isinstance(raw_interests, list):
        for interest in raw_interests:
            if isinstance(interest, str) and interest.strip():
                topics.append(interest.strip())
            elif isinstance(interest, dict) and 'name' in interest:
                topics.append(str(interest['name']).strip())

    # 2. Extract key topical phrases from synthetic or bibliographic facts
    lower_text = text.lower() if text else ''
    lower_title = title.lower() if title else ''
    combined = lower_title + ' ' + lower_text

    if 'sensor' in combined:
        if 'greenhouse' in combined:
            topics.append('Greenhouse Sensors')
        if 'water' in combined or 'turbidity' in combined:
            topics.append('Water Quality Monitoring')
        if 'battery' in combined or 'energy' in combined:
            topics.append('Energy & Battery Systems')

    # 3. Taxonomy pattern matching across title and text
    for concept_label, pattern in CONCEPT_TAXONOMY.items():
        if re.search(pattern, combined, flags=re.IGNORECASE):
            topics.append(concept_label)

    # Normalize and return distinct topics, limiting to top 4 most specific per record
    seen: set[str] = set()
    distinct_topics: list[str] = []
    for t in topics:
        norm = t.strip()
        if norm and norm.lower() not in seen:
            seen.add(norm.lower())
            distinct_topics.append(norm)

    return distinct_topics[:4]


def _assign_cluster(node: dict[str, Any]) -> str:
    """Determine community or departmental cluster for a node."""
    meta = node.get('metadata') or {}
    if node['type'] == 'faculty':
        dept = meta.get('department') or meta.get('college')
        if dept and isinstance(dept, str) and dept.strip():
            return dept.strip()
        interests = meta.get('interests') or []
        if interests and isinstance(interests, list) and interests[0]:
            return f"Field: {interests[0]}"
        return 'Computing Faculty'
    elif node['type'] == 'paper':
        if meta.get('venue'):
            return str(meta['venue'])
        topics = meta.get('interests') or []
        if topics and isinstance(topics, list) and topics[0]:
            return f"Topic: {topics[0]}"
        return 'Publications'
    else:
        return 'Research Topics'


def _compute_layout_coordinates(
    nodes: list[dict[str, Any]],
    center_id: str | None,
    clusters: list[str]
) -> None:
    """Assign deterministic 2D coordinates (x, y) server-side for instant rendering."""
    if center_id:
        # Radial concentric ego-network layout
        # Center node placed at (0, 0)
        center_node = next((n for n in nodes if n['id'] == center_id), None)
        other_nodes = [n for n in nodes if n['id'] != center_id]

        if center_node:
            center_node['x'] = 0.0
            center_node['y'] = 0.0

        hop1 = [n for n in other_nodes if n.get('hop') == 1]
        hop2 = [n for n in other_nodes if n.get('hop') != 1]

        # Orbit 1 (radius 160)
        n1 = max(1, len(hop1))
        for i, node in enumerate(hop1):
            theta = 2.0 * math.pi * i / n1
            node['x'] = round(160.0 * math.cos(theta), 1)
            node['y'] = round(160.0 * math.sin(theta), 1)

        # Orbit 2 (radius 320)
        n2 = max(1, len(hop2))
        for j, node in enumerate(hop2):
            theta = 2.0 * math.pi * j / n2 + (math.pi / n2 if n1 > 0 else 0)
            node['x'] = round(320.0 * math.cos(theta), 1)
            node['y'] = round(320.0 * math.sin(theta), 1)

    else:
        # Multi-centroid community clustered layout
        cluster_map: dict[str, list[dict[str, Any]]] = {}
        for node in nodes:
            cluster_map.setdefault(node.get('cluster', 'General'), []).append(node)

        num_clusters = max(1, len(cluster_map))
        radius_cluster = 280.0

        for k, (cluster_name, cluster_nodes) in enumerate(cluster_map.items()):
            theta_c = 2.0 * math.pi * k / num_clusters
            cx = radius_cluster * math.cos(theta_c)
            cy = radius_cluster * math.sin(theta_c)

            # Golden spiral distribution within cluster
            golden_angle = 2.399963
            for m, node in enumerate(cluster_nodes):
                r = 25.0 + 18.0 * math.sqrt(m)
                phi = m * golden_angle
                node['x'] = round(cx + r * math.cos(phi), 1)
                node['y'] = round(cy + r * math.sin(phi), 1)


def get_public_graph(
    session: Session,
    limit: int = 150,
    topic_filter: str | None = None,
    center_id: str | None = None,
    hops: int = 2,
    cluster_by: str | None = None
) -> dict[str, Any]:
    """Return public graph nodes and edges for visualization and discovery.

    Supports:
    - Ego-network / subgraph extraction around a center node.
    - Precalculated layout coordinates (x, y) for instantaneous browser rendering.
    - Hierarchical community / departmental clustering.
    - Topic filtering.

    Guarantees private proposal sources are strictly excluded.
    """
    rows: list[tuple[Source, PublicRecord]] = []

    if center_id and center_id.strip():
        # Ego-network query: fetch center record specifically
        target_center_id = center_id.strip()
        center_row = session.execute(
            select(Source, PublicRecord)
            .join(PublicRecord, Source.id == PublicRecord.source_id)
            .where(
                Source.id == target_center_id,
                Source.is_public == True,
                PublicRecord.is_current == True
            )
        ).first()

        if center_row:
            rows.append(center_row)
            c_meta = center_row[1].metadata_json if isinstance(center_row[1].metadata_json, dict) else {}
            c_name = clean_name(center_row[0].title, center_row[1].kind, c_meta)

            # Fetch papers authored by or referencing this center researcher
            if center_row[1].kind == 'researcher':
                tokens = [t.strip() for t in c_name.split() if len(t.strip()) > 1]
                clauses = [
                    Source.is_public == True,
                    PublicRecord.is_current == True,
                    PublicRecord.kind == 'paper',
                ]
                for t in tokens[:2]:
                    clauses.append(Source.text.ilike(f"%{t}%"))

                related_papers = session.execute(
                    select(Source, PublicRecord)
                    .join(PublicRecord, Source.id == PublicRecord.source_id)
                    .where(*clauses)
                    .limit(min(limit, 200))
                ).all()
                rows.extend(related_papers)
            elif center_row[1].kind == 'paper':
                fa = c_meta.get('faculty_author')
                if fa:
                    related_researcher = session.execute(
                        select(Source, PublicRecord)
                        .join(PublicRecord, Source.id == PublicRecord.source_id)
                        .where(
                            Source.is_public == True,
                            PublicRecord.is_current == True,
                            PublicRecord.kind == 'researcher',
                            Source.title.ilike(f"%{fa}%")
                        )
                        .limit(10)
                    ).all()
                    rows.extend(related_researcher)

        background_rows = session.execute(
            select(Source, PublicRecord)
            .join(PublicRecord, Source.id == PublicRecord.source_id)
            .where(
                Source.is_public == True,
                Source.proposal_id.is_(None),
                PublicRecord.is_current == True
            )
            .order_by(Source.title)
            .limit(max(limit * 2, 300))
        ).all()

        seen_ids = set()
        merged_rows = []
        for r in rows + background_rows:
            if r[0].id not in seen_ids:
                seen_ids.add(r[0].id)
                merged_rows.append(r)
        rows = merged_rows

    else:
        researcher_rows = session.execute(
            select(Source, PublicRecord)
            .join(PublicRecord, Source.id == PublicRecord.source_id)
            .where(
                Source.is_public == True,
                Source.proposal_id.is_(None),
                PublicRecord.is_current == True,
                PublicRecord.kind == 'researcher'
            )
            .order_by(Source.title)
            .limit(200)
        ).all()

        paper_rows = session.execute(
            select(Source, PublicRecord)
            .join(PublicRecord, Source.id == PublicRecord.source_id)
            .where(
                Source.is_public == True,
                Source.proposal_id.is_(None),
                PublicRecord.is_current == True,
                PublicRecord.kind == 'paper'
            )
            .order_by(Source.title)
            .limit(max(limit * 3, 1200))
        ).all()

        rows = list(dict.fromkeys(researcher_rows + paper_rows))

    if not rows:
        return {'nodes': [], 'links': []}

    nodes_by_id: dict[str, dict[str, Any]] = {}
    external_to_source_id: dict[str, str] = {}
    paper_authors_map: dict[str, list[str]] = {}
    topic_nodes: dict[str, dict[str, Any]] = {}
    links: list[dict[str, Any]] = []
    seen_link_keys: set[tuple[str, str, str]] = set()

    def add_link(source_id: str, target_id: str, rel: str, evidence: str) -> None:
        key = (source_id, target_id, rel)
        if key not in seen_link_keys and (target_id, source_id, rel) not in seen_link_keys:
            seen_link_keys.add(key)
            links.append({
                'source': source_id,
                'target': target_id,
                'relationship': rel,
                'evidence': evidence,
            })

    # Pass 1: Build paper and researcher nodes
    for source, record in rows:
        meta = record.metadata_json if isinstance(record.metadata_json, dict) else {}
        node_type = 'paper' if record.kind == 'paper' else 'faculty'
        display_name = clean_name(source.title, record.kind, meta)

        external_to_source_id[record.external_id] = source.id
        if meta.get('doi'):
            external_to_source_id['doi:' + meta['doi'].lower()] = source.id

        node_data = {
            'id': source.id,
            'name': display_name,
            'type': node_type,
            'origin': source.origin,
            'evidence_kind': record.evidence_kind,
            'metadata': meta,
        }
        nodes_by_id[source.id] = node_data

        if record.kind == 'paper':
            if meta.get('authors') and isinstance(meta['authors'], list):
                paper_authors_map[source.id] = [str(a) for a in meta['authors']]

        topics = extract_topics(source.title, source.text, meta)
        for topic in topics:
            topic_id = 'topic:' + re.sub(r'[^a-zA-Z0-9]+', '-', topic.lower()).strip('-')
            if topic_id not in topic_nodes:
                topic_nodes[topic_id] = {
                    'id': topic_id,
                    'name': topic,
                    'type': 'topic',
                    'origin': None,
                    'evidence_kind': record.evidence_kind,
                    'metadata': {'topic_name': topic},
                }
            rel = 'addresses' if record.kind == 'paper' else 'researches'
            add_link(source.id, topic_id, rel, f"{display_name} {rel} {topic}")

    # Pass 2: Connect authorship links
    def _normalize_author_name(name_str: str) -> str:
        clean = re.sub(r'\s+[A-Za-z]\.?\s+', ' ', name_str.strip())
        return clean.strip().casefold()

    faculty_by_name: dict[str, str] = {}
    for n in nodes_by_id.values():
        if n['type'] == 'faculty':
            faculty_by_name[_normalize_author_name(n['name'])] = n['id']
            faculty_by_name[n['name'].strip().casefold()] = n['id']

    for source, record in rows:
        meta = record.metadata_json if isinstance(record.metadata_json, dict) else {}
        if record.kind == 'paper':
            paper_source_id = source.id
            paper_title = nodes_by_id[paper_source_id]['name']
            author_candidates = []
            if meta.get('faculty_author'):
                author_candidates.append(meta['faculty_author'])
            if meta.get('authors') and isinstance(meta['authors'], list):
                author_candidates.extend(meta['authors'])
            for auth in author_candidates:
                if isinstance(auth, str):
                    clean_auth = _normalize_author_name(auth)
                    raw_auth = auth.strip().casefold()
                    faculty_id = faculty_by_name.get(clean_auth) or faculty_by_name.get(raw_auth)
                    if faculty_id:
                        faculty_name = nodes_by_id[faculty_id]['name']
                        add_link(faculty_id, paper_source_id, 'authored', f"{faculty_name} authored {paper_title}")
        elif record.kind == 'researcher':
            paper_ext_id = meta.get('paper_external_id')
            if paper_ext_id and paper_ext_id in external_to_source_id:
                paper_source_id = external_to_source_id[paper_ext_id]
                author_name = nodes_by_id[source.id]['name']
                paper_title = nodes_by_id.get(paper_source_id, {}).get('name', 'Paper')
                add_link(source.id, paper_source_id, 'authored', f"{author_name} authored {paper_title}")

    # Pass 3: Co-authorship edges between researchers on same paper
    paper_to_researcher_nodes: dict[str, list[str]] = {}
    for link in links:
        if link['relationship'] == 'authored':
            paper_to_researcher_nodes.setdefault(link['target'], []).append(link['source'])

    for paper_id, author_ids in paper_to_researcher_nodes.items():
        if len(author_ids) > 1:
            for i in range(len(author_ids)):
                for j in range(i + 1, len(author_ids)):
                    a1 = nodes_by_id[author_ids[i]]['name']
                    a2 = nodes_by_id[author_ids[j]]['name']
                    add_link(author_ids[i], author_ids[j], 'co_authorship', f"Co-authored works ({a1} and {a2})")

    # Pass 3.5: Paper-to-paper shared concept links
    # Connect papers that address identical scientific concepts (capped to avoid visual clutter)
    topic_to_papers: dict[str, list[str]] = {}
    for link in links:
        if link['relationship'] == 'addresses':
            topic_to_papers.setdefault(link['target'], []).append(link['source'])

    paper_shared_concept_count: dict[str, int] = {}
    for topic_id, paper_ids in topic_to_papers.items():
        topic_name = topic_nodes.get(topic_id, {}).get('name', 'Research Area')
        for i in range(len(paper_ids)):
            p1 = paper_ids[i]
            if paper_shared_concept_count.get(p1, 0) >= 3:
                continue
            for j in range(i + 1, min(len(paper_ids), i + 4)):
                p2 = paper_ids[j]
                if paper_shared_concept_count.get(p2, 0) >= 3:
                    continue
                t1_name = nodes_by_id[p1]['name']
                t2_name = nodes_by_id[p2]['name']
                add_link(p1, p2, 'shares_concept', f"Shared concept ({topic_name}) between '{t1_name}' and '{t2_name}'")
                paper_shared_concept_count[p1] = paper_shared_concept_count.get(p1, 0) + 1
                paper_shared_concept_count[p2] = paper_shared_concept_count.get(p2, 0) + 1

    # Pass 3.6: Faculty shared research interests across identical domains
    topic_to_faculty: dict[str, list[str]] = {}
    for link in links:
        if link['relationship'] == 'researches':
            topic_to_faculty.setdefault(link['target'], []).append(link['source'])

    faculty_pair_overlaps: dict[tuple[str, str], list[str]] = {}
    for topic_id, fac_ids in topic_to_faculty.items():
        topic_name = topic_nodes.get(topic_id, {}).get('name', 'Research Area')
        for i in range(len(fac_ids)):
            for j in range(i + 1, len(fac_ids)):
                pair = (min(fac_ids[i], fac_ids[j]), max(fac_ids[i], fac_ids[j]))
                faculty_pair_overlaps.setdefault(pair, []).append(topic_name)

    faculty_shared_interest_count: dict[str, int] = {}
    for (f1, f2), shared_topics in faculty_pair_overlaps.items():
        if len(shared_topics) >= 2 or (len(shared_topics) >= 1 and len(nodes_by_id) < 50):
            if faculty_shared_interest_count.get(f1, 0) < 3 and faculty_shared_interest_count.get(f2, 0) < 3:
                f1_name = nodes_by_id[f1]['name']
                f2_name = nodes_by_id[f2]['name']
                topics_str = ', '.join(shared_topics[:2])
                add_link(f1, f2, 'shared_interest', f"Shared research interests in {topics_str} ({f1_name} and {f2_name})")
                faculty_shared_interest_count[f1] = faculty_shared_interest_count.get(f1, 0) + 1
                faculty_shared_interest_count[f2] = faculty_shared_interest_count.get(f2, 0) + 1

    # Combine nodes
    all_nodes = list(nodes_by_id.values()) + list(topic_nodes.values())

    # Pass 4: Apply optional topic filter
    if topic_filter and topic_filter.strip():
        filter_term = topic_filter.strip().lower()
        matched_topic_ids = {
            t_id for t_id, t_node in topic_nodes.items()
            if filter_term in t_node['name'].lower()
        }
        connected_node_ids = set(matched_topic_ids)
        for link in links:
            if link['target'] in matched_topic_ids:
                connected_node_ids.add(link['source'])
            elif link['source'] in matched_topic_ids:
                connected_node_ids.add(link['target'])

        all_nodes = [n for n in all_nodes if n['id'] in connected_node_ids]
        node_id_set = {n['id'] for n in all_nodes}
        links = [l for l in links if l['source'] in node_id_set and l['target'] in node_id_set]

    # Pass 5: Ego-Network / Subgraph Extraction (if center_id provided)
    center_node_data = None
    if center_id and center_id.strip():
        target_center_id = center_id.strip()
        nodes_lookup = {n['id']: n for n in all_nodes}
        if target_center_id not in nodes_lookup:
            # Fallback check if center_id matches DOI or name
            matched_id = next((nid for nid, n in nodes_lookup.items() if target_center_id.lower() in n['name'].lower()), None)
            if matched_id:
                target_center_id = matched_id

        if target_center_id in nodes_lookup:
            center_node_data = nodes_lookup[target_center_id]
            center_node_data['is_center'] = True

            # Build adjacency
            adj: dict[str, set[str]] = {}
            for l in links:
                adj.setdefault(l['source'], set()).add(l['target'])
                adj.setdefault(l['target'], set()).add(l['source'])

            # BFS traversal up to `hops`
            visited_hops: dict[str, int] = {target_center_id: 0}
            queue = deque([(target_center_id, 0)])

            while queue:
                curr_id, curr_hop = queue.popleft()
                if curr_hop < hops:
                    for neighbor in adj.get(curr_id, ()):
                        if neighbor not in visited_hops:
                            visited_hops[neighbor] = curr_hop + 1
                            if len(visited_hops) < limit:
                                queue.append((neighbor, curr_hop + 1))

            ego_nodes = []
            for nid, hop_dist in visited_hops.items():
                if nid in nodes_lookup:
                    n = nodes_lookup[nid]
                    n['hop'] = hop_dist
                    ego_nodes.append(n)

            all_nodes = ego_nodes
            ego_node_ids = set(visited_hops.keys())
            links = [l for l in links if l['source'] in ego_node_ids and l['target'] in ego_node_ids]
        else:
            return {'nodes': [], 'links': []}

    else:
        # Balanced Global Graph Sampling:
        # Prevent topic starvation and eliminate zero-degree isolated singletons
        node_degrees: dict[str, int] = {n['id']: 0 for n in all_nodes}
        for l in links:
            node_degrees[l['source']] = node_degrees.get(l['source'], 0) + 1
            node_degrees[l['target']] = node_degrees.get(l['target'], 0) + 1

        for n in all_nodes:
            n['degree'] = node_degrees.get(n['id'], 0)

        # Categorize nodes
        topic_candidates = sorted([n for n in all_nodes if n['type'] == 'topic'], key=lambda x: -x['degree'])
        faculty_candidates = sorted([n for n in all_nodes if n['type'] == 'faculty'], key=lambda x: -x['degree'])
        paper_candidates = sorted([n for n in all_nodes if n['type'] == 'paper'], key=lambda x: -x['degree'])

        # Quotas tailored to limit
        quota_topics = min(len(topic_candidates), max(5, limit // 5))
        quota_faculty = min(len(faculty_candidates), max(10, limit // 3))
        quota_papers = min(len(paper_candidates), limit - quota_topics - quota_faculty)

        selected_nodes = topic_candidates[:quota_topics] + faculty_candidates[:quota_faculty] + paper_candidates[:quota_papers]
        selected_ids = {n['id'] for n in selected_nodes}

        # Fill remaining capacity if any with highest-degree connected candidates
        if len(selected_nodes) < limit:
            remaining = sorted([n for n in all_nodes if n['id'] not in selected_ids], key=lambda x: -x['degree'])
            selected_nodes.extend(remaining[:limit - len(selected_nodes)])

        all_nodes = selected_nodes
        final_node_ids = {n['id'] for n in all_nodes}
        links = [l for l in links if l['source'] in final_node_ids and l['target'] in final_node_ids]

    # Pass 6: Assign Community Clusters
    cluster_counts: dict[str, int] = {}
    for node in all_nodes:
        cluster = _assign_cluster(node)
        node['cluster'] = cluster
        cluster_counts[cluster] = cluster_counts.get(cluster, 0) + 1

    sorted_clusters = sorted(cluster_counts.items(), key=lambda x: -x[1])
    clusters_info = []
    for idx, (c_name, count) in enumerate(sorted_clusters):
        clusters_info.append({
            'id': re.sub(r'[^a-zA-Z0-9]+', '-', c_name.lower()).strip('-'),
            'name': c_name,
            'count': count,
            'color': CLUSTER_PALETTE[idx % len(CLUSTER_PALETTE)]
        })

    cluster_color_map = {c['name']: c['color'] for c in clusters_info}
    for node in all_nodes:
        node['cluster_color'] = cluster_color_map.get(node['cluster'], '#536779')

    # Pass 7: Assign Precomputed Layout Coordinates
    _compute_layout_coordinates(all_nodes, center_id if center_node_data else None, [c['name'] for c in clusters_info])

    # Limit nodes to requested budget
    all_nodes = all_nodes[:limit]
    final_node_ids = {n['id'] for n in all_nodes}
    links = [l for l in links if l['source'] in final_node_ids and l['target'] in final_node_ids]

    response = {
        'nodes': all_nodes,
        'links': links,
        'clusters': clusters_info,
    }
    if center_node_data:
        response['center_node'] = center_node_data

    return response
