"""Transactional immutable public snapshots. The caller owns commit/rollback."""
import unicodedata
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.models import Source
from ..database.public_records import PublicRecord
from .import_public import import_records


def import_public_records(session: Session, records) -> dict:
    prepared = {}
    for record in records:
        record = dict(record)
        text = record.get('text')
        if not isinstance(text, str):
            raise ValueError('Public source text must be a string.')
        record['text'] = unicodedata.normalize('NFC', text.replace('\r\n', '\n').replace('\r', '\n'))
        record.setdefault('version', 'snapshot')
        row = import_records([record])[0]
        key = f"{row['kind']}:{record['external_id'].strip()}"
        if len(key) > 1000:
            raise ValueError('Public external identity exceeds 1000 characters.')
        if key in prepared and prepared[key][0] != row:
            raise ValueError('Conflicting versions for one public identity in this batch.')
        prepared[key] = row, record.get('metadata', {})
    counts = dict(inserted=0, unchanged=0, retired=0)
    with session.begin_nested():
        for key, (row, metadata) in prepared.items():
            source_id = str(uuid5(NAMESPACE_URL, f"urn:researchcircle:public-snapshot:{key}:{row['content_hash']}"))
            current = session.scalar(select(PublicRecord).where(PublicRecord.external_id == key, PublicRecord.is_current.is_(True)).with_for_update())
            if current is not None and current.source_id == source_id:
                counts['unchanged'] += 1
                continue
            if current is not None:
                current.is_current = False
                session.flush()
                counts['retired'] += 1
            source = session.get(Source, source_id)
            if source is None:
                source = Source(id=source_id, version='sha256:' + row['content_hash'], content_hash=row['content_hash'],
                                title=row['title'], origin=row['origin'], text=row['text'], is_public=True, proposal_id=None)
                session.add(source)
                session.flush()
                counts['inserted'] += 1
            elif (not source.is_public or source.proposal_id is not None or source.text != row['text']
                  or source.content_hash != row['content_hash']):
                raise ValueError('Immutable public snapshot conflicts with existing source data.')
            previous = session.get(PublicRecord, source_id)
            if previous is None:
                session.add(PublicRecord(source_id=source_id, external_id=key, kind=row['kind'],
                                         evidence_kind=row['evidence_kind'], is_current=True, metadata_json=metadata))
            else:
                previous.is_current = True
            session.flush()
    return counts
