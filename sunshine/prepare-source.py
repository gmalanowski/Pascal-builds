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
    path.write_text(source)



if __name__ == "__main__":
    prepare(pathlib.Path(sys.argv[1]))
