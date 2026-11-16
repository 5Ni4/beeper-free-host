"""Start the official stable Beeper Server on a private, persistent container."""
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import tarfile
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def prepare_data():
    data = Path('/data')
    data.mkdir(exist_ok=True)
    if data.is_symlink():
        raise RuntimeError('/data must be a volume directory')
    if os.geteuid() == 0:
        os.chown(data, 10001, 10001)
        os.setgroups([])
        os.setgid(10001)
        os.setuid(10001)
    os.umask(0o077)
    data.chmod(0o700)
    os.environ.update({
        'HOME': str(data),
        'XDG_CACHE_HOME': str(data / 'cache'),
        'XDG_CONFIG_HOME': str(data / 'config'),
        'XDG_DATA_HOME': str(data / 'share'),
    })
    return data


def install(data):
    arch = {'x86_64': 'x64', 'aarch64': 'arm64'}.get(platform.machine())
    if not arch:
        raise RuntimeError('Only Linux x64 and arm64 are supported')
    release = json.loads(Path('/app/releases.json').read_text())[arch]
    url = release['url']
    if (urlsplit(url).hostname != 'beeper-desktop.download.beeper.com'
            or 'nightly' in url.lower() or not url.startswith('https://')):
        raise RuntimeError('An official stable server release is required')
    runtime = data / 'runtime'
    runtime.mkdir(exist_ok=True)
    executable = runtime / ('beeper-server-' + release['version'] + '-' + arch)
    stamp = executable.with_suffix('.sha512')
    if executable.exists() and stamp.exists():
        with executable.open('rb') as source:
            verified = hashlib.file_digest(source, 'sha512').hexdigest() == stamp.read_text().strip()
        if verified:
            return executable, release['version']
    with tempfile.TemporaryDirectory() as temp:
        archive = Path(temp) / 'server.tar.gz'
        digest = hashlib.sha512()
        with urlopen(Request(url, headers={'User-Agent': 'beeper-free-host/1'}), timeout=120) as response:
            if urlsplit(response.url).hostname != 'beeper-desktop.download.beeper.com':
                raise RuntimeError('Unexpected artifact redirect')
            with archive.open('wb') as dest:
                while chunk := response.read(1024 * 1024):
                    digest.update(chunk)
                    dest.write(chunk)
        if digest.digest() != base64.b64decode(release['sha512'], validate=True):
            raise RuntimeError('Official release checksum mismatch')
        with tarfile.open(archive, 'r:gz') as bundle:
            members = [x for x in bundle.getmembers() if x.isfile() and Path(x.name).name == 'beeper-server']
            if len(members) != 1:
                raise RuntimeError('Expected exactly one server executable')
            binary = bundle.extractfile(members[0])
            partial = executable.with_suffix('.partial')
            with partial.open('wb') as dest:
                while chunk := binary.read(1024 * 1024):
                    dest.write(chunk)
            partial.chmod(0o700)
            partial.replace(executable)
        with executable.open('rb') as source:
            stamp.write_text(hashlib.file_digest(source, 'sha512').hexdigest() + '\n')
    return executable, release['version']


def main():
    data = prepare_data()
    executable, version = install(data)
    profile = data / 'profile'
    profile.mkdir(exist_ok=True)
    logs = data / 'logs'
    logs.mkdir(exist_ok=True)
    log = logs / 'server.log'
    if log.exists() and log.stat().st_size > 1048576:
        log.replace(logs / 'previous.log')
    print('Starting official Beeper Server ' + version + ' on localhost:23374; profile persists in /data/profile', flush=True)
    # Runtime output stays in the private volume, not provider build/public logs.
    with log.open('ab', buffering=0) as output:
        os.dup2(output.fileno(), 1)
        os.dup2(output.fileno(), 2)
    os.execv(str(executable), [str(executable), '--host=127.0.0.1', '--port=23374', '--data-dir=' + str(profile)])


if __name__ == '__main__':
    main()
