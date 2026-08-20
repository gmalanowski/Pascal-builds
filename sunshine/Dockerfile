FROM nvidia/cuda:12.6.3-devel-ubuntu22.04 AS build

ARG SUNSHINE_REF
ENV DEBIAN_FRONTEND=noninteractive \
    CFLAGS="-O2 -march=x86-64 -mtune=generic" \
    CXXFLAGS="-O2 -march=x86-64 -mtune=generic"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git software-properties-common \
    && add-apt-repository ppa:ubuntu-toolchain-r/test -y \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc-13 g++-13 \
    && rm -rf /var/lib/apt/lists/*

# CUDA 12.6 supports GCC up to version 13. Sunshine's current Ubuntu 22.04
# build tooling may select GCC 14, which nvcc 12.6 rejects. Force a supported
# host compiler explicitly for C, C++, and CUDA host compilation.
ENV CC=/usr/bin/gcc-13 \
    CXX=/usr/bin/g++-13 \
    CUDAHOSTCXX=/usr/bin/g++-13

WORKDIR /build
# Sunshine relies on a number of git submodules (moonlight-common-c,
# Simple-Web-Server, libdisplaydevice, build-deps, etc.). A plain clone leaves
# those directories empty, so always initialize the exact submodule revisions
# recorded by the selected upstream release.
RUN git clone https://github.com/LizardByte/Sunshine.git \
    && cd Sunshine \
    && git checkout --detach "${SUNSHINE_REF}" \
    && git submodule sync --recursive \
    && git submodule update --init --recursive

WORKDIR /build/Sunshine

# Install all non-CUDA dependencies using Sunshine's own build script.
# CUDA is already provided by the pinned NVIDIA devel base image, so we avoid
# the script downloading a newer toolkit while still enabling CUDA at configure time.
RUN chmod +x scripts/linux_build.sh \
    && ./scripts/linux_build.sh \
         --step=deps \
         --ubuntu-test-repo \
         --skip-cuda \
         --sudo-off

# Do NOT pass --skip-cuda from this point onward. The configure step will find
# nvcc 12.6 from the base image and build SUNSHINE_BUILD_CUDA/NvFBC support.
# Sunshine upstream includes compute capability 6.1 when CUDA < 13, which is
# required for Pascal GPUs such as the GTX 1050 Ti.
#
# Keep the diagnostic grep non-fatal without masking a failed configure step.
RUN set -e; \
    gcc-13 --version; \
    g++-13 --version; \
    nvcc --version; \
    export CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13 CUDAHOSTCXX=/usr/bin/g++-13; \
    ./scripts/linux_build.sh \
      --step=cmake \
      --publisher-name='Pascal Builds' \
      --publisher-website='https://github.com/gmalanowski/Pascal-builds' \
      --publisher-issue-url='https://github.com/gmalanowski/Pascal-builds/issues' \
      --sudo-off; \
    grep -E 'CMAKE_(C|CXX|CUDA)_COMPILER(:FILEPATH)?|CMAKE_CUDA_HOST_COMPILER|CMAKE_CUDA_COMPILER_VERSION|CMAKE_CUDA_ARCHITECTURES|SUNSHINE_ENABLE_CUDA' build/CMakeCache.txt || true; \
    ./scripts/linux_build.sh --step=validation --sudo-off; \
    ./scripts/linux_build.sh --step=build --sudo-off; \
    ./scripts/linux_build.sh --step=package --sudo-off

RUN test -s build/cpack_artifacts/Sunshine.deb \
    && dpkg-deb --info build/cpack_artifacts/Sunshine.deb >/dev/null

FROM scratch AS artifact
COPY --from=build /build/Sunshine/build/cpack_artifacts/Sunshine.deb /sunshine-ubuntu22-cuda12.6-pascal-x86_64.deb
