#!/usr/bin/env bash
set -euo pipefail
# The private key is supplied only by a GitHub Actions secret, never a tracked file.
: "${APT_SIGNING_KEY:?Configure the APT_SIGNING_KEY repository secret first}"
: "${APT_SIGNING_PASSPHRASE:?Configure the APT_SIGNING_PASSPHRASE repository secret first}"
root="${1:-apt}"
work="$(mktemp -d)"
trap 'gpgconf --kill gpg-agent >/dev/null 2>&1 || true; rm -rf "$work"' EXIT
umask 077
printf '%s' "$APT_SIGNING_PASSPHRASE" > "$work/passphrase"
unset APT_SIGNING_PASSPHRASE
export GNUPGHOME="$work/gnupg"
mkdir -m 700 "$GNUPGHOME"
printf '%s\n' "$APT_SIGNING_KEY" | gpg --batch --quiet --import
unset APT_SIGNING_KEY
mapfile -t keys < <(gpg --batch --with-colons --list-secret-keys | awk -F: '$1=="sec" {want=1; next} want && $1=="fpr" {print $10; want=0}')
[ "${#keys[@]}" -eq 1 ] || { echo 'Expected exactly one signing identity' >&2; exit 1; }
key="${keys[0]}"
gpg --batch --armor --export "$key" > "$work/public.asc"
# Rotation must be explicit: do not silently replace an existing client trust anchor.
if [ -f "$root/pascal-builds.asc" ]; then
  cmp "$root/pascal-builds.asc" "$work/public.asc" || { echo 'Signing key differs from published key; explicit rotation required' >&2; exit 1; }
fi
cp "$work/public.asc" "$root/pascal-builds.asc"
gpg --batch --export "$key" > "$work/public.gpg"
found=false
for release in "$root"/dists/*/Release; do
  [ -f "$release" ] || continue
  found=true
  gpg --batch --yes --pinentry-mode loopback --passphrase-file "$work/passphrase" --local-user "$key" --digest-algo SHA256 --clearsign --output "${release%Release}InRelease" "$release"
  gpg --batch --yes --pinentry-mode loopback --passphrase-file "$work/passphrase" --local-user "$key" --digest-algo SHA256 --armor --detach-sign --output "$release.gpg" "$release"
  gpgv --keyring "$work/public.gpg" "${release%Release}InRelease"
  gpgv --keyring "$work/public.gpg" "$release.gpg" "$release"
done
[ "$found" = true ] || { echo 'No APT Release files found' >&2; exit 1; }
echo "APT signed and verified with fingerprint $key"
