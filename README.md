# Pascal Builds

Automated compatibility builds for software targeting Pascal-era NVIDIA GPUs and older x86-64 CPUs.

## Goals

- Track stable upstream releases of ComfyUI and Sunshine.
- Build compatibility-oriented artifacts on GitHub-hosted runners.
- Keep support for NVIDIA Pascal GPUs such as the GTX 1050 Ti in mind.
- Avoid unnecessary AVX2 assumptions so older CPUs such as Intel Ivy Bridge remain viable where upstream permits it.
- Run smoke tests before publishing candidate artifacts.
- Never deploy automatically to external servers.

## Projects

### ComfyUI

The ComfyUI pipeline builds a conservative CUDA 12.6 image for Pascal-era GPUs. The image pins `kornia==0.7.1` to avoid the newer `kornia-rs` wheel that can execute AVX2 instructions on older CPUs. The workflow also runs CPU-side import smoke tests on GitHub-hosted runners.

### Sunshine

The Sunshine pipeline builds Ubuntu 24.04 and 26.04/x86-64 packages with CUDA 12.6, GCC 13 and Pascal compute capability 6.1 support. Candidate packages are published to the APT `testing` suite; validated packages are promoted manually to `stable`.

## APT repository

The repository is intentionally unsigned for now, so clients use `trusted=yes`. A repository signing key can be added later.

Candidate/testing channel:

```text
deb [trusted=yes] https://raw.githubusercontent.com/gmalanowski/Pascal-builds/main/apt testing main
```

Validated/stable channel:

```text
deb [trusted=yes] https://raw.githubusercontent.com/gmalanowski/Pascal-builds/main/apt stable main
```

After adding one of the sources, use normal APT commands:

```bash
sudo apt update
sudo apt install sunshine
```

Do not enable both channels on the same machine unless you intentionally want APT pinning or version selection between testing and stable.

## Release model

New upstream stable versions are detected automatically. Builds are published as **candidate** artifacts first. Promotion to a stable deployment remains explicit/manual until the build has been validated on real target hardware. Sunshine candidates also enter APT `testing`; the manual promotion workflow publishes the validated package to APT `stable`.

Sunshine also builds and publishes candidates automatically after changes to
`sunshine/`, `scripts/`, `tests/`, or its build workflow reach `main` (including
PR merges). Both Ubuntu packages must build successfully and compatibility
regression tests must pass before publishing to GitHub Releases and APT
`testing` / `testing-ubuntu26`. The latest stable upstream tag is resolved once
per run and shared by both builds and publication. APT-only commits do not
trigger another build.

For an explicit upstream tag or to retry publication, run **Build Sunshine
compatibility package** manually on `main` with `upstream_ref` set to the stable
release tag. PR builds and manual runs on other branches do not publish.
Stable promotion remains manual after validation on the target GPU.

## Security

All CI runs on GitHub-hosted runners. This repository has no deployment credentials and no access to any homelab or production server.

## Target baseline

- NVIDIA Pascal / compute capability 6.1 class hardware
- CUDA 12.6 runtime/toolchain where required
- x86-64 CPUs without AVX2, including Intel Ivy Bridge, where dependencies permit it

### Ubuntu 26.04 packages

Use suite `testing-ubuntu26` (or `stable-ubuntu26` after explicit hardware validation)
instead of `testing`/`stable`. Ubuntu 24.04 retains the existing suites. Do not mix
the suites: packages are built against each distribution's native libraries.
Both builds retain CUDA 12.6 and GCC 13 for Pascal. The binary receives upstream
`BUILD_VERSION`/`BRANCH` metadata, so its web interface reports the release version
rather than `0.0.0-<commit>-dirty`. Compatibility patches remain in the source;
release notes and the package suffix identify this downstream build.

## APT signing setup

Repository maintainers must configure the `APT_SIGNING_KEY` Actions secret before
merging the signing change. Generate a dedicated, unencrypted RSA signing key
on your own trusted machine (the private key is protected by GitHub Secrets):

```bash
gpg --quick-generate-key 'Pascal Builds APT' rsa3072 sign 2y
```

When prompted, use an empty passphrase for this dedicated CI key. Back up its
private key securely. Using the fingerprint printed by GPG, upload directly
with GitHub CLI (do not paste the private key into chat or commit it):

```bash
gpg --armor --export-secret-keys FINGERPRINT | gh secret set APT_SIGNING_KEY --repo gmalanowski/Pascal-builds
```

After merging, run **Sign existing APT repository** on `main`. This signs every
existing suite, publishes `apt/pascal-builds.asc`, and prints the public
fingerprint. Future APT publication signs and verifies all suites before commit;
a missing secret or signing failure stops publication. Replacing an existing
public key requires explicit key rotation.

Only after the signatures and public key are published, download the public key
to `/etc/apt/keyrings/pascal-builds.asc`, verify its fingerprint against your
locally generated key, and replace `Trusted: yes` in the client `.sources` file
with `Signed-By: /etc/apt/keyrings/pascal-builds.asc`. Keep `Architectures: amd64`
and the appropriate suite. Clients then authenticate Release metadata and its
package-index checksums with this dedicated key.
