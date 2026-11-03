"""Knowledge graph query service grounded strictly in immutable public records.

Builds researcher, paper, and topic nodes and their relationships (authorship,
co-authorship, and research topics) from verified public sources.
Enforces that private proposal-scoped sources are strictly excluded.
"""

from __future__ import annotations

import re
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.platform.database.models import Source
from src.platform.database.public_records import PublicRecord


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
    """Extract explicit research topics or interests from record metadata or facts."""
    topics: list[str] = []
    # 1. Structured interests from profile metadata
    raw_interests = metadata.get('interests') or metadata.get('research_interests') or []
    if isinstance(raw_interests, list):
        for interest in raw_interests:
            if isinstance(interest, str) and interest.strip():
                topics.append(interest.strip())
            elif isinstance(interest, dict) and 'name' in interest:
                topics.append(str(interest['name']).strip())

    # 2. Extract key topical phrases from synthetic or bibliographic facts
    if not topics and ('sensor' in text.lower() or 'sensor' in title.lower()):
        if 'greenhouse' in text.lower():
            topics.append('Greenhouse Sensors')
        if 'water' in text.lower() or 'turbidity' in text.lower():
            topics.append('Water Quality Monitoring')
        if 'battery' in text.lower() or 'energy' in text.lower():
            topics.append('Energy & Battery Systems')
    return list(dict.fromkeys(topics))


def get_public_graph(
    session: Session,
    limit: int = 150,
    topic_filter: str | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Return public graph nodes and edges for visualization and discovery.

    Only sources with is_public=True and proposal_id=None are eligible.
    Private proposal data is never queried or returned.
    """
    stmt = (
        select(Source, PublicRecord)
        .join(PublicRecord, Source.id == PublicRecord.source_id)
        .where(
            Source.is_public == True,  # noqa: E712
            Source.proposal_id.is_(None),
            PublicRecord.is_current == True  # noqa: E712
        )
        .order_by(Source.title)
        .limit(limit)
    )

    rows = session.execute(stmt).all()
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
        # Also map DOI if present
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

        # Track listed authors for papers
        if record.kind == 'paper':
            if meta.get('authors') and isinstance(meta['authors'], list):
                paper_authors_map[source.id] = [str(a) for a in meta['authors']]

        # Extract topics and link to topic nodes
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
    for source, record in rows:
        meta = record.metadata_json if isinstance(record.metadata_json, dict) else {}
        # Author linked to paper via paper_external_id in metadata
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

    return {'nodes': all_nodes, 'links': links}
