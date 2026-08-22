#!/usr/bin/env bash
set -euo pipefail

suite="${1:?usage: update-apt-repo.sh <testing|stable> <package.deb>}"
pkg="${2:?usage: update-apt-repo.sh <testing|stable> <package.deb>}"

case "$suite" in
  testing|stable) ;;
  *) echo "Unsupported suite: $suite" >&2; exit 2 ;;
esac

test -s "$pkg"

name="$(dpkg-deb -f "$pkg" Package)"
version="$(dpkg-deb -f "$pkg" Version)"
arch="$(dpkg-deb -f "$pkg" Architecture)"

if [ "$name" != "sunshine" ]; then
  echo "Refusing to publish unexpected package: $name" >&2
  exit 1
fi
if [ "$arch" != "amd64" ]; then
  echo "Refusing to publish unexpected architecture: $arch" >&2
  exit 1
fi

root="apt"
pool_dir="$root/pool/$suite/main/s/$name"
index_dir="$root/dists/$suite/main/binary-$arch"
mkdir -p "$pool_dir" "$index_dir"

dest="$pool_dir/${name}_${version}_${arch}.deb"
cp "$pkg" "$dest"

(
  cd "$root"
  dpkg-scanpackages --arch "$arch" --multiversion "pool/$suite/main" /dev/null \
    > "dists/$suite/main/binary-$arch/Packages"
  gzip -9c "dists/$suite/main/binary-$arch/Packages" \
    > "dists/$suite/main/binary-$arch/Packages.gz"
)

release="$root/dists/$suite/Release"
{
  echo "Origin: Pascal Builds"
  echo "Label: Pascal Builds"
  echo "Suite: $suite"
  echo "Codename: $suite"
  echo "Architectures: $arch"
  echo "Components: main"
  echo "Description: Pascal compatibility builds"
  echo "Date: $(date -Ru)"

  for algo in MD5Sum SHA1 SHA256; do
    echo "$algo:"
    case "$algo" in
      MD5Sum) hash_cmd=md5sum ;;
      SHA1)   hash_cmd=sha1sum ;;
      SHA256) hash_cmd=sha256sum ;;
    esac
    for rel in "main/binary-$arch/Packages" "main/binary-$arch/Packages.gz"; do
      file="$root/dists/$suite/$rel"
      hash="$($hash_cmd "$file" | awk '{print $1}')"
      size="$(stat -c '%s' "$file")"
      printf ' %s %16s %s\n' "$hash" "$size" "$rel"
    done
  done
} > "$release"

echo "Published $name $version ($arch) to APT suite $suite"
