#!/usr/bin/env python3
"""Apply compiler/CUDA compatibility changes with explicit upstream anchors."""
import pathlib
import sys


def prepare(root):
    path = root / "scripts/linux_build.sh"
    source = path.read_text()
    anchor = 'architecture=$(uname -m)'
    if source.count(anchor) != 1:
        raise ValueError("Upstream distro-detection anchor changed")
    source = source.replace(anchor, 'gcc_version="13"\ncuda_system_package=0\n' + anchor)
    # Validate metadata offline: a remote screenshot outage must not block a
    # package build. Keep both validators and desktop-file validation enabled.
    source = source.replace('appstreamcli validate "', 'appstreamcli validate --no-net "')
    source = source.replace('appstream-util validate "', 'appstream-util validate --nonet "')
    path.write_text(source)

    # GCC 13 lacks C++23 ranges::to. This expression is only used to format
    # a diagnostic string; preserve the exact separator behavior, including
    # empty display names, without changing capture/encoding code.
    kms = root / "src/platform/linux/kmsgrab.cpp"
    if kms.exists():
        text = kms.read_text()
        expression = "(display_names | std::views::join_with(' ') | std::ranges::to<std::string>())"
        replacement = """([&]() {
      std::string joined;
      bool first = true;
      for (const auto &name : display_names) {
        if (!first) {
          joined += ' ';
        }
        joined += name;
        first = false;
      }
      return joined;
    }())"""
        if 'std::ranges::to' in text and text.count(expression) != 1:
            raise ValueError("Upstream KMS ranges expression changed")
        kms.write_text(text.replace(expression, replacement))



if __name__ == "__main__":
    prepare(pathlib.Path(sys.argv[1]))
