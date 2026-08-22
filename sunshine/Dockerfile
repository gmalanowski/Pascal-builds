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

# Sunshine chooses gcc_version internally from the distro and then overwrites
# CC/CXX during both dependency installation and CMake configuration. CUDA
# 12.6 only supports GCC <= 13, so patch the Ubuntu 22.04 branch itself before
# invoking upstream tooling rather than trying to override it afterwards.
RUN sed -i '/elif grep -q "Ubuntu 22.04"/,/nvm_node=1/ s/gcc_version="14"/gcc_version="13"/' scripts/linux_build.sh \
    && grep -A7 'elif grep -q "Ubuntu 22.04"' scripts/linux_build.sh | grep -q 'gcc_version="13"'

# CUDA is already provided by the pinned NVIDIA devel image. --skip-cuda is
# used only for the dependency step so upstream does not download CUDA 13.x.
RUN chmod +x scripts/linux_build.sh \
    && ./scripts/linux_build.sh \
         --step=deps \
         --ubuntu-test-repo \
         --skip-cuda \
         --sudo-off

RUN set -e; \
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
    grep -E 'CMAKE_(C|CXX|CUDA)_COMPILER(:FILEPATH)?|CMAKE_CUDA_HOST_COMPILER|CMAKE_CUDA_ARCHITECTURES|SUNSHINE_ENABLE_CUDA' build/CMakeCache.txt || true; \
    test "$(grep '^SUNSHINE_ENABLE_CUDA:BOOL=' build/CMakeCache.txt | cut -d= -f2)" = "ON"; \
    grep '^CMAKE_CUDA_HOST_COMPILER' build/CMakeCache.txt | grep -q 'gcc-13' || { echo 'ERROR: CUDA host compiler is not GCC 13'; exit 1; }; \
    grep '^CMAKE_C_COMPILER:FILEPATH=' build/CMakeCache.txt | grep -q '/gcc-13$' || { echo 'ERROR: C compiler is not GCC 13'; exit 1; }; \
    grep '^CMAKE_CXX_COMPILER:FILEPATH=' build/CMakeCache.txt | grep -q '/g++-13$' || { echo 'ERROR: CXX compiler is not G++ 13'; exit 1; }; \
    echo "Checking generated CUDA code for Pascal (sm_61/compute_61)..."; \
    grep -Eq 'sm_61|compute_61' build/build.ninja || { echo 'ERROR: generated CUDA rules do not contain Pascal compute capability 6.1'; exit 1; }; \
    echo "Checking CPU baseline..."; \
    grep -q -- '-march=x86-64' build/build.ninja || { echo 'ERROR: generic x86-64 CPU baseline flag is missing'; exit 1; }; \
    if grep -Eq -- '-march=native|-mavx2|-mfma' build/build.ninja; then \
      echo 'Unsupported CPU flag occurrences in build.ninja:'; \
      grep -En -- '-march=native|-mavx2|-mfma' build/build.ninja | head -n 80; \
      echo 'ERROR: generated build contains CPU flags unsupported by the Ivy Bridge target'; \
      exit 1; \
    fi; \
    ./scripts/linux_build.sh --step=validation --sudo-off; \
    ./scripts/linux_build.sh --step=build --sudo-off; \
    ./scripts/linux_build.sh --step=package --sudo-off

RUN test -s build/cpack_artifacts/Sunshine.deb \
    && dpkg-deb --info build/cpack_artifacts/Sunshine.deb >/dev/null

FROM scratch AS artifact
COPY --from=build /build/Sunshine/build/cpack_artifacts/Sunshine.deb /sunshine-ubuntu22-cuda12.6-pascal-x86_64.deb
