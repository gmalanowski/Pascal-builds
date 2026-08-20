FROM ubuntu:22.04 AS build

ARG SUNSHINE_REF
ENV DEBIAN_FRONTEND=noninteractive \
    CFLAGS="-O2 -march=x86-64 -mtune=generic" \
    CXXFLAGS="-O2 -march=x86-64 -mtune=generic"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone --filter=blob:none https://github.com/LizardByte/Sunshine.git \
    && cd Sunshine \
    && git checkout --detach "${SUNSHINE_REF}"

WORKDIR /build/Sunshine
RUN chmod +x scripts/linux_build.sh \
    && ./scripts/linux_build.sh \
         --step=deps \
         --ubuntu-test-repo \
         --skip-cuda \
         --sudo-off

RUN ./scripts/linux_build.sh \
      --step=cmake \
      --skip-cuda \
      --publisher-name='Pascal Builds' \
      --publisher-website='https://github.com/gmalanowski/Pascal-builds' \
      --publisher-issue-url='https://github.com/gmalanowski/Pascal-builds/issues' \
      --sudo-off \
    && ./scripts/linux_build.sh --step=validation --skip-cuda --sudo-off \
    && ./scripts/linux_build.sh --step=build --skip-cuda --sudo-off \
    && ./scripts/linux_build.sh --step=package --skip-cuda --sudo-off

RUN test -s build/cpack_artifacts/Sunshine.deb \
    && dpkg-deb --info build/cpack_artifacts/Sunshine.deb >/dev/null

FROM scratch AS artifact
COPY --from=build /build/Sunshine/build/cpack_artifacts/Sunshine.deb /sunshine-ubuntu22-x86_64.deb
