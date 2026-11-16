"""Inspect runtime metadata only; never authenticate or read chat messages."""
import json
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.request import urlopen


def read(path):
    try:
        with urlopen('http://127.0.0.1:23374' + path, timeout=3) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        return exc.code, {}


def main():
    status, info = read('/v1/info')
    server = info.get('server', {})
    if '--isolated-test' not in sys.argv:
        return 0 if status == 200 and server.get('status') == 'running' else 1
    state_status, setup = read('/v1/app/setup')
    account_status, _ = read('/v1/accounts')
    mcp_status, _ = read('/v0/mcp')
    profile = Path('/data/profile')
    files = [p for p in profile.rglob('*') if p.is_file()]
    result = {
        'server_running': status == 200 and server.get('status') == 'running',
        'version': info.get('app', {}).get('version'),
        'hostname': server.get('hostname'),
        'remote_access': server.get('remote_access'),
        'setup_http_status': state_status,
        'setup_state': setup.get('state'),
        'accounts_without_credentials': account_status,
        'mcp_without_credentials': mcp_status,
        'profile_files': len(files),
        'profile_bytes': sum(p.stat().st_size for p in files),
    }
    result['passed'] = (result['server_running'] and result['hostname'] == '127.0.0.1'
                        and result['setup_state'] == 'needs-login'
                        and account_status == 401 and mcp_status == 401
                        and len(files) > 0)
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
