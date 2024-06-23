ARG BASE_IMAGE_REPO=effectiverange/armhf-tools-base
ARG BASE_IMAGE_VER=latest

FROM ${BASE_IMAGE_REPO}:${BASE_IMAGE_VER}

ARG USERNAME

# [Optional] Uncomment this section to install additional packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && apt install -y sudo

# Create the user and get ownership of /opt/cross for package installation
RUN groupadd  --gid 1000 $USERNAME \
    && useradd -s /bin/bash --uid 1000 --gid 1000 -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME && chown -R $USERNAME:$USERNAME /opt/debs \
    && [ -f  /etc/schroot/chroot.d/buildroot ] && sed -ri "s/(users=.*)/\1,$USERNAME/g" /etc/schroot/chroot.d/buildroot || true

COPY --chown=$USERNAME:$USERNAME . /home/$USERNAME/test
# [Optional] Set the default user. Omit if you want to keep the default as root.
USER $USERNAME    

CMD ["/bin/bash"]

