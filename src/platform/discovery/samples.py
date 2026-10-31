"""Tiny synthetic corpus shipped with the application, not real faculty records.

Every title and origin identifies the sample. No public person, publication,
contact address, institution or source URL is fabricated.
"""


def _sample(key: str, kind: str, title: str, text: str) -> dict:
    return {
        'external_id': f'synthetic:sensor-corpus-v1:{key}',
        'title': f'Synthetic {kind}: {title}',
        'text': text,
        'origin': 'Synthetic sensor corpus v1; no public URL or real faculty identity',
        'version': 'synthetic-v1',
        'kind': kind,
        'evidence_kind': 'synthetic',
        'is_public': True,
        'proposal_id': None,
    }


SAMPLE_RECORDS = (
    _sample('greenhouse-sampling', 'paper', 'Greenhouse sensor measurement schedule',
            'Synthetic sample study: In a greenhouse experiment, a temperature sensor recorded one reading '
            'every ten minutes for seven days. The trial evaluated data collection reliability. '
            'It did not measure crop yields or establish an energy-saving benefit.'),
    _sample('greenhouse-collaborator', 'researcher', 'Greenhouse sensor systems collaborator',
            'Synthetic researcher profile: This example collaborator studies temperature sensor reliability '
            'and greenhouse measurement schedules. Example skills include sensor calibration and missing-data '
            'checks. This profile represents no real person, laboratory or institution.'),
    _sample('water-quality-sampling', 'paper', 'Water quality sensor comparison',
            'Synthetic sample study: A water quality sensor collected hourly turbidity measurements for three '
            'days. A second instrument provided comparison readings at noon. The example describes a sampling '
            'protocol and reports no measured accuracy improvement.'),
    _sample('water-quality-collaborator', 'researcher', 'Water quality measurement collaborator',
            'Synthetic researcher profile: This example collaborator works on water quality monitoring, '
            'turbidity measurement and sensor comparison protocols. This profile represents no real person, '
            'laboratory or institution, and has no contact details.'),
    _sample('battery-monitoring', 'paper', 'Battery monitoring logger trial',
            'Synthetic sample study: A battery monitoring logger recorded voltage and current once per minute '
            'during a two-hour bench trial. The protocol used a fixed test load. The sample does not establish '
            'battery lifetime, deployment safety or a reduction in energy use.'),
    _sample('energy-collaborator', 'researcher', 'Battery and energy measurement collaborator',
            'Synthetic researcher profile: This example collaborator studies battery monitoring, current '
            'measurement and energy logging protocols. This profile represents no real person, laboratory '
            'or institution. No qualifications or availability are claimed for a real researcher.'),
)
