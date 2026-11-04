"""Seed 10 realistic academic users, 3 collaborative teams, proposals, and tracking records."""
import os
import sys
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from pwdlib import PasswordHash
from sqlalchemy import select
from src.platform.database import Database
from src.platform.database.models import User, Team, Membership, Proposal, ProposalSource, Source
from src.platform.database.pursuits import Opportunity, Pursuit, PursuitHistory
from src.platform.database.shortlists import TeamShortlistEntry

password_hasher = PasswordHash.recommended()
DEFAULT_PASSWORD_HASH = password_hasher.hash('Password123!')

USERS_DATA = [
    {
        'id': '11111111-1111-4111-8111-111111111111',
        'email': 'elena.rostova@rit.edu',
        'name': 'Dr. Elena Rostova',
        'affiliation': 'Professor of Computer Science, Robotics & Control'
    },
    {
        'id': '22222222-2222-4222-8222-222222222222',
        'email': 'marcus.vance@rit.edu',
        'name': 'Dr. Marcus Vance',
        'affiliation': 'Associate Professor, Embedded Systems & Sensors'
    },
    {
        'id': '33333333-3333-4333-8333-333333333333',
        'email': 'aria.chen@rit.edu',
        'name': 'Dr. Aria Chen',
        'affiliation': 'Postdoctoral Fellow, Distributed Swarm Intelligence'
    },
    {
        'id': '44444444-4444-4444-8444-444444444444',
        'email': 'devon.miller@rit.edu',
        'name': 'Devon Miller',
        'affiliation': 'Graduate Research Assistant, Robotics Testbed'
    },
    {
        'id': '55555555-5555-4555-8555-555555555555',
        'email': 'sophia.almansoor@rit.edu',
        'name': 'Dr. Sophia Al-Mansoor',
        'affiliation': 'Professor, Biomedical Computing & Health Informatics'
    },
    {
        'id': '66666666-6666-4666-8666-666666666666',
        'email': 'rajesh.patel@rit.edu',
        'name': 'Dr. Rajesh K. Patel',
        'affiliation': 'Associate Professor of Imaging Science'
    },
    {
        'id': '77777777-7777-4777-8777-777777777777',
        'email': 'claire.beauchamp@rit.edu',
        'name': 'Claire Beauchamp',
        'affiliation': 'Clinical Research Protocol Coordinator'
    },
    {
        'id': '88888888-8888-4888-8888-888888888888',
        'email': 'tariq.thorne@rit.edu',
        'name': 'Dr. Tariq Thorne',
        'affiliation': 'Associate Professor, Cybersecurity & Cryptographic Protocols'
    },
    {
        'id': '99999999-9999-4999-8999-999999999999',
        'email': 'maya.lin@rit.edu',
        'name': 'Dr. Maya Lin',
        'affiliation': 'Assistant Professor, Trustworthy Machine Learning & Fairness'
    },
    {
        'id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        'email': 'lucas.sterling@rit.edu',
        'name': 'Lucas Sterling',
        'affiliation': 'Doctoral Candidate in Theoretical CS'
    }
]


def seed_database():
    db_password = os.getenv('TBR_DB_PASSWORD')
    db_host = os.getenv('TBR_DB_HOST', 'db')
    db_name = os.getenv('TBR_DB_NAME', 'tbr')
    db_user = os.getenv('TBR_DB_USER', 'tbr')
    db_port = os.getenv('TBR_DB_PORT', '5432')

    db_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    print(f'Connecting to PostgreSQL: {db_host}:{db_port}/{db_name}...')
    database = Database(db_url)

    with database.session_factory() as session:
        # 1. Upsert 10 Users
        user_objects = {}
        for u in USERS_DATA:
            existing = session.scalar(select(User).where(User.email == u['email']))
            if existing:
                existing.name = u['name']
                existing.password_hash = DEFAULT_PASSWORD_HASH
                user_objects[u['email']] = existing
            else:
                user = User(
                    id=u['id'],
                    email=u['email'],
                    name=u['name'],
                    password_hash=DEFAULT_PASSWORD_HASH,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(user)
                user_objects[u['email']] = user
        session.commit()
        print(f'Successfully ensured {len(user_objects)} users in database.')

        # Fetch sample public sources to attach to proposals
        public_sources = session.scalars(select(Source).where(Source.is_public == True).limit(10)).all()
        source_ids = [s.id for s in public_sources]
        print(f'Using {len(source_ids)} real public sources for attachment.')

        # 2. Team 1: Autonomous & Cyber-Physical Systems Lab
        t1_id = 'bbbbbbbb-1111-4bbb-8bbb-111111111111'
        team1 = session.get(Team, t1_id)
        if not team1:
            team1 = Team(id=t1_id, name='Autonomous & Cyber-Physical Systems Lab')
            session.add(team1)
            session.flush()

        memberships_t1 = [
            (user_objects['elena.rostova@rit.edu'].id, 'owner'),
            (user_objects['marcus.vance@rit.edu'].id, 'editor'),
            (user_objects['aria.chen@rit.edu'].id, 'editor'),
            (user_objects['devon.miller@rit.edu'].id, 'viewer'),
        ]
        for uid, role in memberships_t1:
            m = session.scalar(select(Membership).where(Membership.team_id == team1.id, Membership.user_id == uid))
            if not m:
                session.add(Membership(team_id=team1.id, user_id=uid, role=role))

        # Opportunity for Team 1
        opp1 = session.scalar(select(Opportunity).where(Opportunity.team_id == team1.id, Opportunity.title.like('%NSF 24-500%')))
        if not opp1:
            opp1 = Opportunity(
                team_id=team1.id,
                title='NSF 24-500: CISE Core Programs (IIS, CCF, CNS)',
                source_url='https://new.nsf.gov/funding/opportunities/computer-information-science-engineering-core',
                deadline=datetime.now(timezone.utc) + timedelta(days=45),
                deadline_timezone='America/New_York',
                notes='Medium project solicitation ($1.2M total). Requires cross-disciplinary validation and real-world sensing deployment.',
                eligibility='eligible'
            )
            session.add(opp1)
            session.flush()

        # Proposal 1
        p1_sources = source_ids[:3] if len(source_ids) >= 3 else source_ids
        p1_id = 'cccccccc-1111-4ccc-8ccc-111111111111'
        p1 = session.get(Proposal, p1_id)
        p1_content = """# Resilient Multi-Robot Perception and Swarm Coordination for Disaster Response

## 1. Project Overview & Intellectual Merit
Disaster response environments—including post-seismic collapsed structures, subterranean search operations, and wildfire perimeters—exhibit severe communication degradation, occlusion, and dynamic environmental hazards. Autonomous multi-robot swarms provide a scalable paradigm for rapid spatial mapping, victim localization, and thermal anomaly detection without exposing human first responders to hazardous conditions.

## 2. Theoretical Architecture & Sensor Fusion
Our framework couples distributed state estimation with graph-based semantic Simultaneous Localization and Mapping (SLAM). Each agent in the robotic swarm runs a lightweight peer-to-peer visual-inertial odometry estimator.

### Key Innovations:
- **Byzantine-Fault-Tolerant Consensus**: Outlier sensor readings caused by hardware failures or adversarial jamming are filtered through local peer agreement protocols.
- **Sub-Gigahertz Mesh Telemetry**: When broadband RF communication is completely severed, agents fall back to low-bandwidth packet broadcast.

## 3. Specific Aims
- **Specific Aim 1 (Foundations & Modeling)**: Formalize distributed visual-inertial state estimation bounds under non-Gaussian noise.
- **Specific Aim 2 (Hardware-in-the-Loop Testbed)**: Deploy a fleet of 6 agile quadrupeds and 4 UAVs equipped with radiometric thermal sensors.
- **Specific Aim 3 (Field Validation & Translation)**: Conduct end-to-end multi-agent search drills in collaboration with the Monroe County Urban Search and Rescue team.

## 4. Broader Impacts
The resulting software framework will be open-sourced under the MIT License for academic and emergency services use. The initiative directly funds 3 doctoral candidates and 4 undergraduate researchers from underrepresented groups in computing.
"""
        if not p1:
            p1 = Proposal(
                id=p1_id,
                team_id=team1.id,
                title='Resilient Multi-Robot Perception and Swarm Coordination for Disaster Response',
                content=p1_content,
                revision=3,
                selected_source_ids=p1_sources
            )
            session.add(p1)
            session.flush()
            for sid in p1_sources:
                session.add(ProposalSource(proposal_id=p1.id, source_id=sid))

            # Pursuit tracking for P1
            pursuit1 = Pursuit(
                proposal_id=p1.id,
                opportunity_id=opp1.id,
                state='collaborating'
            )
            session.add(pursuit1)
            session.flush()
            session.add(PursuitHistory(
                pursuit_id=pursuit1.id,
                from_state='draft',
                to_state='shortlisted',
                user_id=user_objects['elena.rostova@rit.edu'].id
            ))
            session.add(PursuitHistory(
                pursuit_id=pursuit1.id,
                from_state='shortlisted',
                to_state='collaborating',
                user_id=user_objects['elena.rostova@rit.edu'].id
            ))

        # 3. Team 2: Biomedical Intelligence & Health Informatics
        t2_id = 'bbbbbbbb-2222-4bbb-8bbb-222222222222'
        team2 = session.get(Team, t2_id)
        if not team2:
            team2 = Team(id=t2_id, name='Biomedical Intelligence & Health Informatics Lab')
            session.add(team2)
            session.flush()

        memberships_t2 = [
            (user_objects['sophia.almansoor@rit.edu'].id, 'owner'),
            (user_objects['rajesh.patel@rit.edu'].id, 'editor'),
            (user_objects['claire.beauchamp@rit.edu'].id, 'viewer'),
        ]
        for uid, role in memberships_t2:
            m = session.scalar(select(Membership).where(Membership.team_id == team2.id, Membership.user_id == uid))
            if not m:
                session.add(Membership(team_id=team2.id, user_id=uid, role=role))

        opp2 = session.scalar(select(Opportunity).where(Opportunity.team_id == team2.id, Opportunity.title.like('%NIH%')))
        if not opp2:
            opp2 = Opportunity(
                team_id=team2.id,
                title='NIH R01: Exploratory Biomedical Data Repositories & Diagnostics (PA-20-185)',
                source_url='https://grants.nih.gov/grants/guide/pa-files/PA-20-185.html',
                deadline=datetime.now(timezone.utc) + timedelta(days=60),
                deadline_timezone='America/New_York',
                notes='Standard R01 submission window. Clinical trial optional, focus on multi-site privacy compliance.',
                eligibility='eligible'
            )
            session.add(opp2)
            session.flush()

        p2_id = 'cccccccc-2222-4ccc-8ccc-222222222222'
        p2 = session.get(Proposal, p2_id)
        p2_content = """# Privacy-Preserving Federated Diagnostics for Clinical Neurological Biomarkers

## 1. Abstract & Clinical Significance
Early identification of neurodegenerative pathologies—such as Alzheimer's disease and frontotemporal lobar degeneration—relies on high-field structural and functional Magnetic Resonance Imaging (MRI). However, cross-institutional data pooling is severely constrained by HIPAA regulations and patient privacy safeguards.

## 2. Research Strategy & Federated Framework
We introduce a decentralized differential-privacy federated learning architecture. Hospital clinical nodes compute encrypted model gradient updates on local neuroimaging clusters without transmitting raw scan volumes.
"""
        if not p2:
            p2 = Proposal(
                id=p2_id,
                team_id=team2.id,
                title='Privacy-Preserving Federated Diagnostics for Clinical Neurological Biomarkers',
                content=p2_content,
                revision=2,
                selected_source_ids=source_ids[3:6] if len(source_ids) >= 6 else []
            )
            session.add(p2)
            session.flush()
            for sid in (source_ids[3:6] if len(source_ids) >= 6 else []):
                session.add(ProposalSource(proposal_id=p2.id, source_id=sid))

            pursuit2 = Pursuit(
                proposal_id=p2.id,
                opportunity_id=opp2.id,
                state='submitted'
            )
            session.add(pursuit2)
            session.flush()
            session.add(PursuitHistory(
                pursuit_id=pursuit2.id,
                from_state='collaborating',
                to_state='submitted',
                user_id=user_objects['sophia.almansoor@rit.edu'].id
            ))

        # 4. Team 3: Trustworthy AI & Cryptographic Systems Group
        t3_id = 'bbbbbbbb-3333-4bbb-8bbb-333333333333'
        team3 = session.get(Team, t3_id)
        if not team3:
            team3 = Team(id=t3_id, name='Trustworthy AI & Cryptographic Systems Group')
            session.add(team3)
            session.flush()

        memberships_t3 = [
            (user_objects['tariq.thorne@rit.edu'].id, 'owner'),
            (user_objects['maya.lin@rit.edu'].id, 'editor'),
            (user_objects['lucas.sterling@rit.edu'].id, 'editor'),
        ]
        for uid, role in memberships_t3:
            m = session.scalar(select(Membership).where(Membership.team_id == team3.id, Membership.user_id == uid))
            if not m:
                session.add(Membership(team_id=team3.id, user_id=uid, role=role))

        opp3 = session.scalar(select(Opportunity).where(Opportunity.team_id == team3.id, Opportunity.title.like('%SaTC%')))
        if not opp3:
            opp3 = Opportunity(
                team_id=team3.id,
                title='NSF 24-504: Secure and Trustworthy Cyberspace (SaTC)',
                source_url='https://new.nsf.gov/funding/opportunities/secure-trustworthy-cyberspace-satc',
                deadline=datetime.now(timezone.utc) + timedelta(days=30),
                deadline_timezone='America/New_York',
                notes='Core SaTC solicitation. Focus on cryptographic verification and zero-knowledge neural network inference.',
                eligibility='eligible'
            )
            session.add(opp3)
            session.flush()

        p3_id = 'cccccccc-3333-4ccc-8ccc-333333333333'
        p3 = session.get(Proposal, p3_id)
        p3_content = """# Adversarial Robustness and Verifiable Zero-Knowledge Bounds in Large Multimodal Models

## 1. Problem Statement
Foundation models and Large Multimodal Models (LMMs) are increasingly integrated into high-assurance decision support systems. However, vulnerability to imperceptible adversarial perturbations and prompt-injection attacks presents severe reliability risks.

## 2. Research Plan & Zero-Knowledge Verification
This project designs succinct non-interactive arguments of knowledge (zk-SNARKs) tailored for quantized transformer layer activations.
"""
        if not p3:
            p3 = Proposal(
                id=p3_id,
                team_id=team3.id,
                title='Adversarial Robustness and Verifiable Zero-Knowledge Bounds in Large Multimodal Models',
                content=p3_content,
                revision=1,
                selected_source_ids=source_ids[6:9] if len(source_ids) >= 9 else []
            )
            session.add(p3)
            session.flush()
            for sid in (source_ids[6:9] if len(source_ids) >= 9 else []):
                session.add(ProposalSource(proposal_id=p3.id, source_id=sid))

            pursuit3 = Pursuit(
                proposal_id=p3.id,
                opportunity_id=opp3.id,
                state='shortlisted'
            )
            session.add(pursuit3)

        # 5. Seed some curated faculty shortlist entries
        shortlist_candidates = [
            (team1.id, user_objects['elena.rostova@rit.edu'].id, 'Matthew Wright', 'Expertise in adversarial machine learning and sensor verification.'),
            (team1.id, user_objects['elena.rostova@rit.edu'].id, 'Bo Yuan', 'Malware and computational intelligence on edge devices.'),
            (team2.id, user_objects['sophia.almansoor@rit.edu'].id, 'Cecilia Alm', 'Linguistic and multimodal sensing with human-centered AI.'),
            (team3.id, user_objects['tariq.thorne@rit.edu'].id, 'Travis Desell', 'Evolutionary neural architectures and high-performance distributed datasets.')
        ]
        for tid, uid, name_query, note in shortlist_candidates:
            # find source by title
            src = session.scalar(select(Source).where(Source.title.like(f'%{name_query}%')))
            if src:
                existing_entry = session.scalar(select(TeamShortlistEntry).where(TeamShortlistEntry.team_id == tid, TeamShortlistEntry.source_id == src.id))
                if not existing_entry:
                    session.add(TeamShortlistEntry(
                        team_id=tid,
                        source_id=src.id,
                        created_by=uid,
                        note=note
                    ))

        session.commit()
        print('All 10 users, 3 teams, proposals, pursuits, and shortlists seeded successfully!')


if __name__ == '__main__':
    seed_database()
