"""Exercise signing and tamper detection with a disposable, non-production key."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AptSigningTests(unittest.TestCase):
    def test_signatures_and_failure_paths(self):
        with tempfile.TemporaryDirectory(prefix='apt-sign-', dir='/tmp') as directory:
            root = Path(directory)
            home = root / 'key'
            home.mkdir(mode=0o700)
            env = dict(os.environ, GNUPGHOME=str(home))
            subprocess.run(['gpg', '--batch', '--pinentry-mode', 'loopback', '--passphrase', '', '--quick-generate-key', 'CI disposable key', 'rsa2048', 'sign', '1d'], env=env, check=True, capture_output=True)
            try:
                key = subprocess.check_output(['gpg', '--batch', '--armor', '--export-secret-keys'], env=env, text=True)
                env['APT_SIGNING_KEY'] = key
                release = root / 'apt/dists/testing/Release'
                release.parent.mkdir(parents=True)
                release.write_text('Suite: testing\n')
                command = ['bash', str(ROOT / 'scripts/sign-apt-repo.sh')]
                subprocess.run(command, cwd=root, env=env, check=True, capture_output=True)
                public = root / 'public.gpg'
                public.write_bytes(subprocess.check_output(['gpg', '--dearmor'], input=(root / 'apt/pascal-builds.asc').read_bytes()))
                for signature, data in [('InRelease', []), ('Release.gpg', [str(release)])]:
                    subprocess.run(['gpgv', '--keyring', str(public), str(release.parent / signature), *data], check=True, capture_output=True)
                release.write_text('Suite: modified\n')
                self.assertNotEqual(subprocess.run(['gpgv', '--keyring', str(public), str(release)+'.gpg', str(release)], capture_output=True).returncode, 0)
                env.pop('APT_SIGNING_KEY')
                self.assertNotEqual(subprocess.run(command, cwd=root, env=env, capture_output=True).returncode, 0)
                # Reject a different trust anchor rather than silently rotating it.
                env['APT_SIGNING_KEY'] = key
                (root / 'apt/pascal-builds.asc').write_text('different key\n')
                self.assertNotEqual(subprocess.run(command, cwd=root, env=env, capture_output=True).returncode, 0)
            finally:
                subprocess.run(['gpgconf', '--kill', 'gpg-agent'], env=env, capture_output=True)
