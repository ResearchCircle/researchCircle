"""Seed 10 realistic student researchers, 3 collaborative student teams, proposals, and tracking records."""
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

STUDENT_USERS_DATA = [
    {
        'id': '11111111-1111-4111-8111-111111111111',
        'email': 'aarav.sharma@rit.edu',
        'name': 'Aarav Sharma',
        'affiliation': 'Ph.D. Candidate in Computer Science (Swarm Robotics & SLAM)'
    },
    {
        'id': '22222222-2222-4222-8222-222222222222',
        'email': 'chloe.dubois@rit.edu',
        'name': 'Chloe Dubois',
        'affiliation': 'M.S. Student in Microelectronic Engineering (Edge AI Hardware)'
    },
    {
        'id': '33333333-3333-4333-8333-333333333333',
        'email': 'maya.patel@rit.edu',
        'name': 'Maya Patel',
        'affiliation': 'Ph.D. Candidate in Information Sciences (Human-Swarm Interaction)'
    },
    {
        'id': '44444444-4444-4444-8444-444444444444',
        'email': 'liam.oconnor@rit.edu',
        'name': 'Liam O\'Connor',
        'affiliation': 'Senior Undergraduate Researcher in Software Engineering'
    },
    {
        'id': '55555555-5555-4555-8555-555555555555',
        'email': 'david.zhang@rit.edu',
        'name': 'Zhenyu (David) Zhang',
        'affiliation': 'Ph.D. Candidate in Imaging Science (Federated Medical AI)'
    },
    {
        'id': '66666666-6666-4666-8666-666666666666',
        'email': 'fatima.zahra@rit.edu',
        'name': 'Fatima Zahra',
        'affiliation': 'M.S. Student in Biomedical Engineering (Neural Biosensors)'
    },
    {
        'id': '77777777-7777-4777-8777-777777777777',
        'email': 'gabriel.santos@rit.edu',
        'name': 'Gabriel Santos',
        'affiliation': 'Graduate Research Assistant in Health Informatics'
    },
    {
        'id': '88888888-8888-4888-8888-888888888888',
        'email': 'ananya.iyer@rit.edu',
        'name': 'Ananya Iyer',
        'affiliation': 'Ph.D. Candidate in Computing Security (Zero-Knowledge Proofs)'
    },
    {
        'id': '99999999-9999-4999-8999-999999999999',
        'email': 'ethan.vance@rit.edu',
        'name': 'Ethan Vance',
        'affiliation': 'M.S. Student in Artificial Intelligence (Adversarial Robustness)'
    },
    {
        'id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        'email': 'samantha.reed@rit.edu',
        'name': 'Samantha Reed',
        'affiliation': 'Graduate Research Fellow, Global Cybersecurity Institute'
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
        # 1. Upsert 10 Student Users
        user_objects = {}
        for u in STUDENT_USERS_DATA:
            existing = session.get(User, u['id'])
            if existing:
                existing.email = u['email']
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
        print(f'Successfully ensured {len(user_objects)} student users in database.')

        # Fetch sample public sources to attach to proposals
        public_sources = session.scalars(select(Source).where(Source.is_public == True).limit(10)).all()
        source_ids = [s.id for s in public_sources]
        print(f'Using {len(source_ids)} real public sources for attachment.')

        # ---------------------------------------------------------------------
        # 2. Team 1: TigerSwarm Autonomous Robotics Lab
        # ---------------------------------------------------------------------
        t1_id = 'bbbbbbbb-1111-4bbb-8bbb-111111111111'
        team1 = session.get(Team, t1_id)
        if not team1:
            team1 = Team(id=t1_id, name='TigerSwarm Autonomous Robotics Lab')
            session.add(team1)
            session.flush()
        else:
            team1.name = 'TigerSwarm Autonomous Robotics Lab'

        memberships_t1 = [
            (user_objects['aarav.sharma@rit.edu'].id, 'owner'),
            (user_objects['chloe.dubois@rit.edu'].id, 'editor'),
            (user_objects['maya.patel@rit.edu'].id, 'editor'),
            (user_objects['liam.oconnor@rit.edu'].id, 'viewer'),
        ]
        for uid, role in memberships_t1:
            m = session.scalar(select(Membership).where(Membership.team_id == t1_id, Membership.user_id == uid))
            if not m:
                session.add(Membership(id=str(uuid4()), team_id=t1_id, user_id=uid, role=role))
            else:
                m.role = role

        # Proposal 1
        p1_id = 'cccccccc-1111-4ccc-8ccc-111111111111'
        prop1 = session.get(Proposal, p1_id)
        p1_title = 'Adaptive Multi-Robot Swarm Telemetry and Decentralized Perception for Urban Disaster Search-and-Rescue'
        p1_content = """# Project Description

## 1. Overview and Objectives
Urban search-and-rescue (USAR) operations present catastrophic communication degradation, physical occlusions, and dynamic hazards where centralized robotic control fails catastrophically. The **TigerSwarm Autonomous Systems Lab** proposes a decentralized multi-robot coordination architecture integrating distributed Simultaneous Localization and Mapping (SLAM), low-power edge neuromorphic vision processing, and adaptive peer-to-peer mesh networking.

Our primary hypothesis is that heterogeneous autonomous swarms utilizing localized topological state estimation achieve 4.2x faster survivor localization in GPS-denied collapsed structures compared to state-of-the-art centralized frontier exploration.

## 2. Intellectual Merit
This research advances cyber-physical systems across three core technical thrusts:
1. **Decentralized Spatial Perception under Communication Choke-points**: Formulating asynchronous factor graphs that preserve spatial convergence even when agent dropouts exceed 60%.
2. **Neuromorphic Edge Computing**: Incorporating sub-milliwatt event-based optical sensors for micro-UAV obstacle negotiation in smoke-obscured corridors.
3. **Resilient Task Allocation**: Designing game-theoretic consensus protocols that prevent redundant zone coverage and dynamically prioritize victim triage telemetry.

## 3. Work Plan & Specific Aims
- **Aim 1 (Months 1–12)**: Characterize decentralized consensus convergence over lossy 802.11ah mesh networks using the RIT Robotics Testbed.
- **Aim 2 (Months 13–24)**: Prototype embedded neuromorphic sensor fusion payloads aboard quadrotor-ground rover heterogeneous teams.
- **Aim 3 (Months 25–36)**: Conduct full-scale field validation in simulated disaster training facilities with local emergency responders.

## 4. Broader Impacts
The resulting software framework will be released as an open-source ROS 2 package. The project directly trains undergraduate and graduate students at Rochester Institute of Technology, engaging minority student researchers through RIT's Women in Computing (WiC) and NSBE chapters.
"""
        if not prop1:
            prop1 = Proposal(
                id=p1_id,
                team_id=t1_id,
                title=p1_title,
                content=p1_content,
                revision=3,
                created_at=datetime.now(timezone.utc) - timedelta(days=20),
                updated_at=datetime.now(timezone.utc) - timedelta(hours=2)
            )
            session.add(prop1)
        else:
            prop1.title = p1_title
            prop1.content = p1_content
            prop1.revision = 3

        # Attach real sources to Proposal 1
        for sid in source_ids[:4]:
            ps = session.scalar(select(ProposalSource).where(ProposalSource.proposal_id == p1_id, ProposalSource.source_id == sid))
            if not ps:
                session.add(ProposalSource(proposal_id=p1_id, source_id=sid))

        # Opportunity & Pursuit for Team 1 (NSF CISE Core)
        opp1_id = 'dddddddd-1111-4ddd-8ddd-111111111111'
        opp1 = session.get(Opportunity, opp1_id)
        if not opp1:
            opp1 = Opportunity(
                id=opp1_id,
                team_id=t1_id,
                title='NSF 24-500: CISE Core Programs (IIS, CCF, CNS)',
                source_url='https://new.nsf.gov/funding/opportunities/computer-information-science-engineering-core',
                deadline=datetime.now(timezone.utc) + timedelta(days=45),
                notes='CISE Core Programs open submission window for Small and Medium multi-agent systems and cyber-physical resilience.',
                eligibility='eligible'
            )
            session.add(opp1)

        pursuit1 = session.scalar(select(Pursuit).where(Pursuit.proposal_id == p1_id))
        if not pursuit1:
            pursuit1 = Pursuit(
                id=str(uuid4()),
                proposal_id=p1_id,
                opportunity_id=opp1_id,
                state='collaborating',
                created_at=datetime.now(timezone.utc) - timedelta(days=15),
                updated_at=datetime.now(timezone.utc) - timedelta(hours=1)
            )
            session.add(pursuit1)
        else:
            pursuit1.state = 'collaborating'

        # ---------------------------------------------------------------------
        # 3. Team 2: NeuroHealth Federated AI Student Guild
        # ---------------------------------------------------------------------
        t2_id = 'bbbbbbbb-2222-4bbb-8bbb-222222222222'
        team2 = session.get(Team, t2_id)
        if not team2:
            team2 = Team(id=t2_id, name='NeuroHealth Federated AI Student Guild')
            session.add(team2)
            session.flush()
        else:
            team2.name = 'NeuroHealth Federated AI Student Guild'

        memberships_t2 = [
            (user_objects['david.zhang@rit.edu'].id, 'owner'),
            (user_objects['fatima.zahra@rit.edu'].id, 'editor'),
            (user_objects['gabriel.santos@rit.edu'].id, 'viewer'),
        ]
        for uid, role in memberships_t2:
            m = session.scalar(select(Membership).where(Membership.team_id == t2_id, Membership.user_id == uid))
            if not m:
                session.add(Membership(id=str(uuid4()), team_id=t2_id, user_id=uid, role=role))
            else:
                m.role = role

        # Proposal 2
        p2_id = 'cccccccc-2222-4ccc-8ccc-222222222222'
        prop2 = session.get(Proposal, p2_id)
        p2_title = 'Privacy-Preserving Federated Tomography and Multi-Modal Biomarker Discovery for Neurodegenerative Disorders'
        p2_content = """# Specific Aims

## Significance & Clinical Need
Early diagnosis of neurodegenerative pathologies such as Alzheimer's disease (AD) and frontotemporal dementia (FTD) requires longitudinal multimodal volumetric neuroimaging paired with physiological biomarkers. However, strict patient privacy regulations (HIPAA, GDPR) prevent cross-institutional pooling of raw MRI and PET scans.

The **NeuroHealth Federated AI Initiative** investigates federated differential privacy paradigms that enable multi-center model training without raw medical image aggregation.

## Specific Aim 1: Federated Structural MRI Tensor Decomposition
Develop decentralized, privacy-budgeted tensor factorization across multi-site neuroimaging cohorts (ADNI, OASIS), guaranteeing (ε, δ)-differential privacy bounds while retaining high structural biomarker fidelity.

## Specific Aim 2: Cross-Modal Alignment of Biofluid Microfluidic Signatures
Integrate plasma p-tau217 and neurofilament light chain (NfL) time-series data with cortical thickness maps using physics-informed neural ODEs.

## Specific Aim 3: Empirical Validation & Clinical Generalizability Assessment
Evaluate cross-scanner generalizability on heterogeneous 1.5T and 3.0T MRI acquisitions without domain adaptation leakage.
"""
        if not prop2:
            prop2 = Proposal(
                id=p2_id,
                team_id=t2_id,
                title=p2_title,
                content=p2_content,
                revision=2,
                created_at=datetime.now(timezone.utc) - timedelta(days=35),
                updated_at=datetime.now(timezone.utc) - timedelta(days=2)
            )
            session.add(prop2)
        else:
            prop2.title = p2_title
            prop2.content = p2_content
            prop2.revision = 2

        # Attach real sources to Proposal 2
        for sid in source_ids[4:7]:
            ps = session.scalar(select(ProposalSource).where(ProposalSource.proposal_id == p2_id, ProposalSource.source_id == sid))
            if not ps:
                session.add(ProposalSource(proposal_id=p2_id, source_id=sid))

        # Opportunity & Pursuit for Team 2 (NIH R01)
        opp2_id = 'dddddddd-2222-4ddd-8ddd-222222222222'
        opp2 = session.get(Opportunity, opp2_id)
        if not opp2:
            opp2 = Opportunity(
                id=opp2_id,
                team_id=t2_id,
                title='NIH PA-20-185: Research Project Grant (Parent R01)',
                source_url='https://grants.nih.gov/grants/guide/pa-files/PA-20-185.html',
                deadline=datetime.now(timezone.utc) + timedelta(days=90),
                notes='Parent R01 supporting fundamental biomedical research in neurological computational diagnostics and imaging biomarkers.',
                eligibility='eligible'
            )
            session.add(opp2)

        pursuit2 = session.scalar(select(Pursuit).where(Pursuit.proposal_id == p2_id))
        if not pursuit2:
            pursuit2 = Pursuit(
                id=str(uuid4()),
                proposal_id=p2_id,
                opportunity_id=opp2_id,
                state='submitted',
                created_at=datetime.now(timezone.utc) - timedelta(days=25),
                updated_at=datetime.now(timezone.utc) - timedelta(days=1)
            )
            session.add(pursuit2)
        else:
            pursuit2.state = 'submitted'

        # ---------------------------------------------------------------------
        # 4. Team 3: Verifiable AI & Cryptographic Computing Guild
        # ---------------------------------------------------------------------
        t3_id = 'bbbbbbbb-3333-4bbb-8bbb-333333333333'
        team3 = session.get(Team, t3_id)
        if not team3:
            team3 = Team(id=t3_id, name='Verifiable AI & Cryptographic Computing Guild')
            session.add(team3)
            session.flush()
        else:
            team3.name = 'Verifiable AI & Cryptographic Computing Guild'

        memberships_t3 = [
            (user_objects['ananya.iyer@rit.edu'].id, 'owner'),
            (user_objects['ethan.vance@rit.edu'].id, 'editor'),
            (user_objects['samantha.reed@rit.edu'].id, 'editor'),
        ]
        for uid, role in memberships_t3:
            m = session.scalar(select(Membership).where(Membership.team_id == t3_id, Membership.user_id == uid))
            if not m:
                session.add(Membership(id=str(uuid4()), team_id=t3_id, user_id=uid, role=role))
            else:
                m.role = role

        # Proposal 3
        p3_id = 'cccccccc-3333-4ccc-8ccc-333333333333'
        prop3 = session.get(Proposal, p3_id)
        p3_title = 'Zero-Knowledge Verifiable Bounds and Adversarial Certification for Foundation Models'
        p3_content = """# Executive Research Plan

## Technical Challenge & Overview
Foundation model deployments increasingly govern critical infrastructure, autonomous navigation, and medical decision support. However, model outputs remain vulnerable to adversarial perturbations, and verifying execution integrity on third-party cloud accelerators compromises either model weights or query privacy.

The **Trustworthy AI & Cryptographic Systems Group** formulates verifiable zero-knowledge arguments (zk-SNARKs) tailored for high-dimensional matrix transformations and non-linear activation layers.

## Key Research Objectives
1. **Succinct Proofs for Transformer Layers**: Establishing polynomial commitment schemes with logarithmic verification complexity over multi-head attention blocks.
2. **Adversarial Perturbation Bounds**: Formalizing certifiable l-infinity radius certificates through interval bound propagation with zero-knowledge proof of correctness.
3. **Decentralized Model Watermarking**: Embedding cryptographically unforgeable signatures into diffusion and transformer weights verifiable without leaking intellectual property.
"""
        if not prop3:
            prop3 = Proposal(
                id=p3_id,
                team_id=t3_id,
                title=p3_title,
                content=p3_content,
                revision=1,
                created_at=datetime.now(timezone.utc) - timedelta(days=12),
                updated_at=datetime.now(timezone.utc) - timedelta(hours=5)
            )
            session.add(prop3)
        else:
            prop3.title = p3_title
            prop3.content = p3_content
            prop3.revision = 1

        # Attach real sources to Proposal 3
        for sid in source_ids[7:10]:
            ps = session.scalar(select(ProposalSource).where(ProposalSource.proposal_id == p3_id, ProposalSource.source_id == sid))
            if not ps:
                session.add(ProposalSource(proposal_id=p3_id, source_id=sid))

        # Opportunity & Pursuit for Team 3 (NSF SaTC)
        opp3_id = 'dddddddd-3333-4ddd-8ddd-333333333333'
        opp3 = session.get(Opportunity, opp3_id)
        if not opp3:
            opp3 = Opportunity(
                id=opp3_id,
                team_id=t3_id,
                title='NSF 24-504: Secure and Trustworthy Cyberspace (SaTC)',
                source_url='https://new.nsf.gov/funding/opportunities/secure-trustworthy-cyberspace-satc',
                deadline=datetime.now(timezone.utc) + timedelta(days=30),
                notes='Supports fundamental cybersecurity, verifiable computation, and cryptographic machine learning privacy.',
                eligibility='eligible'
            )
            session.add(opp3)

        pursuit3 = session.scalar(select(Pursuit).where(Pursuit.proposal_id == p3_id))
        if not pursuit3:
            pursuit3 = Pursuit(
                id=str(uuid4()),
                proposal_id=p3_id,
                opportunity_id=opp3_id,
                state='shortlisted',
                created_at=datetime.now(timezone.utc) - timedelta(days=10),
                updated_at=datetime.now(timezone.utc) - timedelta(hours=4)
            )
            session.add(pursuit3)
        else:
            pursuit3.state = 'shortlisted'

        # Seed Faculty Shortlist for Teams
        shortlists = [
            (t1_id, source_ids[0], 'Dr. Matthew Wright (Cybersecurity & Swarm Telemetry) - Priority PI collaborator for NSF CISE Core.'),
            (t1_id, source_ids[1], 'Dr. Bo Yuan (Computer Science) - Recommended for deep neural SLAM and edge optimization.'),
            (t2_id, source_ids[4], 'Dr. Cecilia Alm (Computational Linguistics & Multimodal Diagnostics) - Potential Co-PI for clinical text alignment.'),
            (t3_id, source_ids[7], 'Dr. Travis Desell (Distributed Systems & Verifiable Computing) - Contacted for cluster compute benchmarking.'),
        ]
        owner_by_team = {
            t1_id: user_objects['aarav.sharma@rit.edu'].id,
            t2_id: user_objects['david.zhang@rit.edu'].id,
            t3_id: user_objects['ananya.iyer@rit.edu'].id,
        }
        for tid, sid, note in shortlists:
            existing_sl = session.scalar(select(TeamShortlistEntry).where(TeamShortlistEntry.team_id == tid, TeamShortlistEntry.source_id == sid))
            if not existing_sl:
                session.add(TeamShortlistEntry(id=str(uuid4()), team_id=tid, source_id=sid, created_by=owner_by_team[tid], note=note))

        session.commit()
        print('Successfully committed all 10 students, 3 research teams, proposals, pursuits, and shortlists!')


if __name__ == '__main__':
    seed_database()
