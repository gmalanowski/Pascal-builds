#!/usr/bin/env python3
import json
import sys
import urllib.request


def latest(owner_repo: str) -> dict:
    url = f"https://api.github.com/repos/{owner_repo}/releases/latest"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "pascal-builds"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: latest-release.py OWNER/REPO", file=sys.stderr)
        return 2
    data = latest(sys.argv[1])
    print(json.dumps({
        "tag_name": data.get("tag_name"),
        "name": data.get("name"),
        "prerelease": data.get("prerelease", False),
        "draft": data.get("draft", False),
        "html_url": data.get("html_url"),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
