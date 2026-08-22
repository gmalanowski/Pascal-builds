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

ENV CC=/usr/bin/gcc-13 \
    CXX=/usr/bin/g++-13 \
    CUDAHOSTCXX=/usr/bin/g++-13

WORKDIR /build
RUN git clone https://github.com/LizardByte/Sunshine.git \
    && cd Sunshine \
    && git checkout --detach "${SUNSHINE_REF}" \
    && git submodule sync --recursive \
    && git submodule update --init --recursive

WORKDIR /build/Sunshine

# Install non-CUDA dependencies with upstream tooling. The script may switch
# compiler alternatives to its preferred GCC version, so restore GCC 13 after
# this step for CUDA 12.6 compatibility.
RUN chmod +x scripts/linux_build.sh \
    && ./scripts/linux_build.sh \
         --step=deps \
         --ubuntu-test-repo \
         --skip-cuda \
         --sudo-off \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 130 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 130 \
    && update-alternatives --set gcc /usr/bin/gcc-13 \
    && update-alternatives --set g++ /usr/bin/g++-13

# The selected Sunshine release hard-codes its preferred host compiler into
# the generated CMake arguments. Patch only that CUDA host-compiler argument so
# nvcc 12.6 never gets gcc-14. C/C++ compiler selection is also pinned through
# CC/CXX and update-alternatives above.
RUN sed -i 's/CMAKE_CUDA_HOST_COMPILER=gcc-14/CMAKE_CUDA_HOST_COMPILER=gcc-13/g' scripts/linux_build.sh

RUN set -e; \
    echo "Host toolchain:"; \
    gcc --version | head -n1; \
    g++ --version | head -n1; \
    nvcc --version; \
    export CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13 CUDAHOSTCXX=/usr/bin/g++-13; \
    ./scripts/linux_build.sh \
      --step=cmake \
      --publisher-name='Pascal Builds' \
      --publisher-website='https://github.com/gmalanowski/Pascal-builds' \
      --publisher-issue-url='https://github.com/gmalanowski/Pascal-builds/issues' \
      --sudo-off; \
    echo "CMake compiler/CUDA summary:"; \
    grep -E 'CMAKE_(C|CXX|CUDA)_COMPILER(:FILEPATH)?|CMAKE_CUDA_HOST_COMPILER|CMAKE_CUDA_ARCHITECTURES|SUNSHINE_ENABLE_CUDA' build/CMakeCache.txt || true; \
    test "$(grep '^SUNSHINE_ENABLE_CUDA:BOOL=' build/CMakeCache.txt | cut -d= -f2)" = "ON"; \
    ! grep -q 'CMAKE_CUDA_HOST_COMPILER.*gcc-14' build/CMakeCache.txt; \
    ! grep -q 'CMAKE_C_COMPILER:FILEPATH=/usr/bin/gcc-14' build/CMakeCache.txt; \
    ! grep -q 'CMAKE_CXX_COMPILER:FILEPATH=/usr/bin/g++-14' build/CMakeCache.txt; \
    echo "Checking generated CUDA code for Pascal (sm_61/compute_61)..."; \
    grep -Eq 'sm_61|compute_61' build/build.ninja; \
    ./scripts/linux_build.sh --step=validation --sudo-off; \
    ./scripts/linux_build.sh --step=build --sudo-off; \
    ./scripts/linux_build.sh --step=package --sudo-off

RUN test -s build/cpack_artifacts/Sunshine.deb \
    && dpkg-deb --info build/cpack_artifacts/Sunshine.deb >/dev/null

FROM scratch AS artifact
COPY --from=build /build/Sunshine/build/cpack_artifacts/Sunshine.deb /sunshine-ubuntu22-cuda12.6-pascal-x86_64.deb
