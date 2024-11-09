ARG BASE_IMAGE_REPO=debian
ARG BASE_IMAGE_VER=bullseye-slim

FROM ${BASE_IMAGE_REPO}:${BASE_IMAGE_VER}

ARG BUILD_UID=499
ARG BUILD_GID=499
ARG KEEP_BUILD_ARTIFACTS=FALSE
ARG TARGET_DIR=NON_EXISTENT_FILE
ARG BUILD_ARCH=armhf

RUN apt update && apt install -y wget

# Checks if the 'crossbuilder' user exists. 
RUN if ! id crossbuilder 2>/dev/null;then \
    groupadd -g $BUILD_GID crossbuilder && \
    useradd -d /home/crossbuilder -m -g $BUILD_GID -u $BUILD_UID -s /bin/bash crossbuilder \
    ;fi
COPY --chown=crossbuilder:crossbuilder ./build_tools /home/crossbuilder/build_tools
COPY --chown=crossbuilder:crossbuilder ./scripts /home/crossbuilder/scripts
COPY --chown=crossbuilder:crossbuilder $TARGET_DIR /home/crossbuilder/target
RUN touch /home/crossbuilder/target.$(basename $TARGET_DIR)

# Non-interactive configuration of tzdata
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true
RUN { echo 'tzdata tzdata/Areas select Etc'; echo 'tzdata tzdata/Zones/Etc select UTC'; } | debconf-set-selections

RUN /bin/bash  -o pipefail -c " KEEP_BUILD_ARTIFACTS=$KEEP_BUILD_ARTIFACTS /home/crossbuilder/scripts/build_all $BUILD_ARCH 2>&1 | tee /tmp/build.log"

CMD ["/bin/bash"]