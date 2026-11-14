import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_source', ROOT / 'sunshine/prepare-source.py')
prepare_source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_source)


class CompatibilityTests(unittest.TestCase):
    def test_compiler_override_after_distro_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            script = root / 'scripts/linux_build.sh'
            script.write_text('gcc_version="14"\ncuda_system_package=1\narchitecture=$(uname -m)\nprintf "%s %s" "$gcc_version" "$cuda_system_package"\n')
            prepare_source.prepare(root)
            result = subprocess.check_output(['bash', str(script)], text=True)
            self.assertEqual(result, '13 0')

    def test_upstream_anchor_drift_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            (root / 'scripts/linux_build.sh').write_text('changed upstream script\n')
            with self.assertRaisesRegex(ValueError, 'anchor changed'):
                prepare_source.prepare(root)

    def test_metadata_validation_keeps_checks_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            script = root / 'scripts/linux_build.sh'
            script.write_text('architecture=$(uname -m)\nappstreamcli validate "metadata.xml"\nappstream-util validate "metadata.xml"\ndesktop-file-validate "app.desktop"\n')
            prepare_source.prepare(root)
            source = script.read_text()
            self.assertIn('appstreamcli validate --no-net "metadata.xml"', source)
            self.assertIn('appstream-util validate --nonet "metadata.xml"', source)
            self.assertIn('desktop-file-validate "app.desktop"', source)

    def test_kms_join_preserves_output_without_cpp23_ranges(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            (root / 'scripts/linux_build.sh').write_text('architecture=$(uname -m)\n')
            kms = root / 'src/platform/linux/kmsgrab.cpp'
            kms.parent.mkdir(parents=True)
            expression = "(display_names | std::views::join_with(' ') | std::ranges::to<std::string>())"
            kms.write_text('#include <string>\n#include <vector>\n#include <cassert>\nstd::string join(const std::vector<std::string>& display_names) { return ' + expression + '; }\nint main() { assert(join({}) == ""); assert(join({""}) == ""); assert(join({"", ""}) == " "); assert(join({"A", "B"}) == "A B"); assert(join({"A", "", "C"}) == "A  C"); }\n')
            prepare_source.prepare(root)
            self.assertNotIn('std::ranges::to', kms.read_text())
            binary = root / 'join-test'
            subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', str(kms), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

    def test_distribution_apt_suites_remain_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control = root / 'package/DEBIAN'
            control.mkdir(parents=True)
            (control / 'control').write_text('Package: sunshine\nVersion: 2026.914.233613+pascal3\nArchitecture: amd64\nMaintainer: Test <test@example.com>\nDescription: Test fixture\n')
            package = root / 'test.deb'
            subprocess.run(['dpkg-deb', '--build', str(control.parent), str(package)], check=True, capture_output=True)
            for suite in ('testing', 'stable', 'testing-ubuntu26', 'stable-ubuntu26'):
                subprocess.run(['bash', str(ROOT / 'scripts/update-apt-repo.sh'), suite, str(package)], cwd=root, check=True, capture_output=True)
                index = (root / 'apt/dists' / suite / 'main/binary-amd64/Packages').read_text()
                self.assertIn(f'Filename: pool/{suite}/', index)


if __name__ == '__main__':
    unittest.main()
