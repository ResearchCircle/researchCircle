"""Build local application images without pushing or starting the shared stack."""

import argparse
import json
import subprocess
from pathlib import Path

from .runtime import ROOT


def build_command(component: str, tag: str, api_requirements: str | None) -> list[str]:
    if component not in ('api', 'web'):
        raise ValueError('Image component must be api or web.')
    command = ['docker', 'build', '-f', str(ROOT / f'deployment/{component}.Dockerfile'), '-t', tag]
    if component == 'api':
        if not api_requirements or Path(api_requirements).is_absolute():
            raise ValueError('Supply a checkout-relative API requirements file.')
        path = (ROOT / api_requirements).resolve()
        try:
            relative = path.relative_to(ROOT)
        except ValueError:
            raise ValueError('API requirements must stay inside the checkout.') from None
        allowed = bool(relative.parts) and (relative.parts[0] in ('deployment', 'services', 'src')
                                           or relative.parts[:2] == ('packages', 'contracts'))
        if not allowed or path.suffix not in ('.txt', '.in', '.lock') or not path.is_file():
            raise ValueError('Supply a requirements file in the API build context, outside source data and secrets.')
        command.extend(['--build-arg', f'TBR_API_REQUIREMENTS={relative.as_posix()}'])
    command.append(str(ROOT))
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--component', choices=['api', 'web', 'all'], default='all')
    parser.add_argument('--api-tag', default='tbr-v2-api:development')
    parser.add_argument('--web-tag', default='tbr-v2-web:development')
    parser.add_argument('--api-requirements', default='services/api/requirements.txt')
    parser.add_argument('--print-only', action='store_true')
    args = parser.parse_args()
    try:
        components = ('api', 'web') if args.component == 'all' else (args.component,)
        commands = [build_command(component, args.api_tag if component == 'api' else args.web_tag,
                                  args.api_requirements if component == 'api' else None) for component in components]
        if args.print_only:
            print(json.dumps({'commands': commands, 'scope': 'Local images only; no deployment or acceptance claim.'}))
            return 0
        for command in commands:
            subprocess.run(command, check=True)
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        message = str(error) if isinstance(error, ValueError) else 'Local image build failed; inspect the build output.'
        print(json.dumps({'status': 'build_failed', 'message': message}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
