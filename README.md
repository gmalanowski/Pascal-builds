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
