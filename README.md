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

The Sunshine pipeline tracks stable releases and builds Linux packages from source using upstream build tooling where possible. It is intentionally kept independent from any deployment target.

## Release model

New upstream stable versions are detected automatically. Builds are published as **candidate** artifacts first. Promotion to a stable deployment remains explicit/manual until the build has been validated on real target hardware.

## Security

All CI runs on GitHub-hosted runners. This repository has no deployment credentials and no access to any homelab or production server.

## Target baseline

- NVIDIA Pascal / compute capability 6.1 class hardware
- CUDA 12.6 runtime for ComfyUI
- x86-64 CPUs without AVX2, including Intel Ivy Bridge, where dependencies permit it
