"""Read configuration without creating directories or contacting services."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from src.platform.models.provider import LocalModelProvider, OllamaModelProvider


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RuntimeConfig:
    profile: str
    provider: str
    model_base_url: str | None
    model_id: str | None
    source_dir: Path
    work_dir: Path

    @classmethod
    def from_env(cls, env: Mapping[str, str]):
        profile = env.get('TBR_PROFILE', 'development')
        provider = env.get('TBR_MODEL_PROVIDER', 'fixture')
        if profile not in ('development', 'demo') or provider not in ('fixture', 'local', 'ollama'):
            raise ValueError('Use development/demo profile and an explicit fixture/local/ollama provider.')
        if profile == 'demo' and (provider != 'local' or env.get('TBR_DEV_IDENTITY', '').lower() not in ('', '0', 'false')):
            raise ValueError('Shared demo requires the local provider and disables development identity.')
        url, model = env.get('TBR_MODEL_BASE_URL'), env.get('TBR_MODEL_ID')
        if provider == 'local':
            LocalModelProvider(url, model)
        elif provider == 'ollama':
            OllamaModelProvider(url, model)
        source = Path(env.get('TBR_DATA_SOURCE', str(ROOT / 'data'))).expanduser().resolve()
        work = Path(env.get('TBR_DATA_WORK', '/tmp/tbr-v2-work')).expanduser().resolve()
        if source == work or source in work.parents or work in source.parents:
            raise ValueError('Source snapshot and runtime work directory must be separate, non-nested paths.')
        return cls(profile, provider, url, model, source, work)


def integration_gaps(root: Path, env: Mapping[str, str]) -> list[str]:
    """Structural prerequisites only; their presence does not prove acceptance."""
    gaps = []
    for relative, message in [
        ('src/platform/discovery', 'T1 source/retrieval implementation is absent.'),
        ('src/platform/database', 'T2 application database implementation is absent.'),
        ('src/platform/workflow', 'T2 proposal/job services are absent.'),
        ('services/api/routes', 'T2 v2 routes are absent.'),
        ('frontend/src/lib/api.ts', 'T3 v2 API client is absent; browser integration is pending.'),
    ]:
        if not (root / relative).exists():
            gaps.append(message)
    module = env.get('TBR_WORKER_MODULE', 'services.worker.generate')
    if not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', module):
        gaps.append('T2 worker entrypoint TBR_WORKER_MODULE is not configured.')
    else:
        path = root.joinpath(*module.split('.'))
        if not path.with_suffix('.py').is_file() and not (path / '__main__.py').is_file():
            gaps.append('Configured T2 worker entrypoint does not exist.')
    return gaps
