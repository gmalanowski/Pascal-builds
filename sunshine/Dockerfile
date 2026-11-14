ARG UBUNTU_VERSION=24.04
FROM nvidia/cuda:12.6.3-devel-ubuntu24.04 AS cuda
FROM ubuntu:${UBUNTU_VERSION} AS build
ARG UBUNTU_VERSION
COPY --from=cuda /usr/local/cuda-12.6 /usr/local/cuda-12.6
RUN ln -s cuda-12.6 /usr/local/cuda
ENV PATH=/usr/local/cuda/bin:${PATH} \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64

ARG SUNSHINE_REF
ENV DEBIAN_FRONTEND=noninteractive \
    CFLAGS="-O2 -march=x86-64 -mtune=generic" \
    CXXFLAGS="-O2 -march=x86-64 -mtune=generic"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git python3 patch software-properties-common \
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

# Override the selected compiler after distro detection, not a distro-specific
# text fragment: upstream now uses a case statement for Ubuntu versions.
COPY sunshine/prepare-source.py /tmp/prepare-source.py
RUN python3 /tmp/prepare-source.py /build/Sunshine \
    && if [ "$UBUNTU_VERSION" = 26.04 ]; then \
         patch -p2 --directory=/usr/local/cuda \
           < packaging/linux/patches/x86_64/cuda-12-math_functions.patch; \
       fi

# Boost.Log automatically adds a dedicated dump_avx2.cpp implementation when
# the build host supports AVX2. GitHub runners do, but the Ivy Bridge target
# does not. Pre-seed Boost's configure-test result before dependencies are
# added so the AVX2 translation unit is not built into the package at all.
RUN sed -i '/include(${CMAKE_MODULE_PATH}\/dependencies\/common.cmake)/i set(BOOST_LOG_COMPILER_HAS_AVX2 FALSE CACHE BOOL "Disable Boost.Log AVX2 for Ivy Bridge compatibility" FORCE)' CMakeLists.txt \
    && grep -B1 -A1 'dependencies/common.cmake' CMakeLists.txt | grep -q 'BOOST_LOG_COMPILER_HAS_AVX2 FALSE'

# GCC 13 emits a known false-positive array-bounds warning in libstdc++ while
# compiling Sunshine's Linux graphics tests. Upstream enables -Werror through
# SUNSHINE_COMPILE_OPTIONS, which is appended after environment CXXFLAGS, so
# disabling the error via CXXFLAGS is ineffective. Add the narrow exception
# directly after upstream's -Werror so only this warning remains non-fatal.
RUN sed -i '/list(APPEND SUNSHINE_COMPILE_OPTIONS -Werror)/a\    list(APPEND SUNSHINE_COMPILE_OPTIONS -Wno-error=array-bounds)' cmake/compile_definitions/common.cmake \
    && grep -A1 'SUNSHINE_COMPILE_OPTIONS -Werror' cmake/compile_definitions/common.cmake | grep -q 'Wno-error=array-bounds'

# CUDA is already provided by the pinned NVIDIA devel image. --skip-cuda is
# used only for the dependency step so upstream does not download CUDA 13.x.
RUN chmod +x scripts/linux_build.sh \
    && ./scripts/linux_build.sh \
         --step=deps \
         --ubuntu-test-repo \
         --skip-cuda \
         --sudo-off

RUN set -e; \
    export BRANCH=master BUILD_VERSION="${SUNSHINE_REF}"; \
    export COMMIT="$(git rev-parse HEAD)" TAG="${SUNSHINE_REF}"; \
    echo "Host toolchain:"; \
    gcc-13 --version | head -n1; \
    g++-13 --version | head -n1; \
    nvcc --version; \
    ./scripts/linux_build.sh \
      --step=cmake \
      --publisher-name='Pascal Builds' \
      --publisher-website='https://github.com/gmalanowski/Pascal-builds' \
      --publisher-issue-url='https://github.com/gmalanowski/Pascal-builds/issues' \
      --sudo-off; \
    echo "CMake compiler/CUDA summary:"; \
    grep -E 'CMAKE_(C|CXX|CUDA)_COMPILER(:FILEPATH)?|CMAKE_CUDA_HOST_COMPILER|CMAKE_CUDA_ARCHITECTURES|SUNSHINE_ENABLE_CUDA|BOOST_LOG_COMPILER_HAS_AVX2' build/CMakeCache.txt || true; \
    test "$(grep '^SUNSHINE_ENABLE_CUDA:BOOL=' build/CMakeCache.txt | cut -d= -f2)" = "ON"; \
    grep '^CMAKE_CUDA_HOST_COMPILER' build/CMakeCache.txt | grep -q 'gcc-13' || { echo 'ERROR: CUDA host compiler is not GCC 13'; exit 1; }; \
    grep '^CMAKE_C_COMPILER:FILEPATH=' build/CMakeCache.txt | grep -q '/gcc-13$' || { echo 'ERROR: C compiler is not GCC 13'; exit 1; }; \
    grep '^CMAKE_CXX_COMPILER:FILEPATH=' build/CMakeCache.txt | grep -q '/g++-13$' || { echo 'ERROR: CXX compiler is not G++ 13'; exit 1; }; \
    grep '^BOOST_LOG_COMPILER_HAS_AVX2:BOOL=FALSE' build/CMakeCache.txt || { echo 'ERROR: Boost.Log AVX2 was not disabled'; exit 1; }; \
    echo "Checking generated CUDA code for Pascal (sm_61/compute_61)..."; \
    grep -Eq 'sm_61|compute_61' build/build.ninja || { echo 'ERROR: generated CUDA rules do not contain Pascal compute capability 6.1'; exit 1; }; \
    echo "Checking CPU baseline..."; \
    grep -q -- '-march=x86-64' build/build.ninja || { echo 'ERROR: generic x86-64 CPU baseline flag is missing'; exit 1; }; \
    if grep -Eq -- '-march=native|-mavx2|-mfma' build/build.ninja; then \
      echo 'Unsupported CPU flag occurrences in build.ninja:'; \
      grep -En -- '-march=native|-mavx2|-mfma' build/build.ninja | head -n 80; \
      echo 'Context around the first unsupported flag:'; \
      first_line="$(grep -En -- '-march=native|-mavx2|-mfma' build/build.ninja | head -n1 | cut -d: -f1)"; \
      start=$((first_line > 12 ? first_line - 12 : 1)); \
      end=$((first_line + 12)); \
      sed -n "${start},${end}p" build/build.ninja; \
      echo 'Matching compile_commands.json entries:'; \
      grep -n -B2 -A6 -E -- '-march=native|-mavx2|-mfma' build/compile_commands.json | head -n 120 || true; \
      echo 'ERROR: generated build contains CPU flags unsupported by the Ivy Bridge target'; \
      exit 1; \
    fi; \
    grep -q -- '-Wno-error=array-bounds' build/build.ninja || { echo 'ERROR: GCC 13 array-bounds exception was not propagated to generated compile rules'; exit 1; }; \
    ./scripts/linux_build.sh --step=validation --sudo-off; \
    ./scripts/linux_build.sh --step=build --sudo-off; \
    ./scripts/linux_build.sh --step=package --sudo-off

# CPack names release builds sunshine_<version>_amd64.deb, while older
# builds used Sunshine.deb. Export exactly one verified package under a
# stable artifact name rather than relying on either upstream filename.
RUN set -e; \
    set -- build/cpack_artifacts/*.deb; \
    test "$#" -eq 1; \
    test -s "$1"; \
    dpkg-deb --info "$1" >/dev/null; \
    cp "$1" /build/Sunshine.deb

FROM scratch AS artifact
COPY --from=build /build/Sunshine.deb /Sunshine.deb
