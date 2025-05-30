# Pin to specific version in order to keep evals consistent
# Use the command below to target a new release
# docker pull kalilinux/kali-last-release
# docker inspect -f '{{json .RepoDigests}}' kalilinux/kali-last-release | jq -r '.[0]'
FROM kalilinux/kali-last-release@sha256:99d99f1c1349a5e1fa8f862875ad204ffc009599e2a6c4ed617d16f6d5bae241

# Avoid prompts during package installation.
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y \
    kali-linux-headless \
    fdisk \
    foremost \
    gcc-aarch64-linux-gnu \
    gdb \
    gobuster \
    iputils-ping \
    libc6-dev-arm64-cross \ 
    netbase \
    openssh-client \
    outguess \
    python-is-python3 \
    python3 \
    python3-pip \
    python3-opencv \
    python3-pil \
    python3-venv \
    qemu-user \
    sleuthkit \
    sshpass \
    steghide \
    tcpflow \
    unzip \
    wireshark \
    && rm -rf /var/lib/apt/lists/*

# Note: stegoveritas isn't available as a system package, so we'll need to use pip for just that one
RUN pip3 install --no-cache-dir --break-system-packages stegoveritas

# Fix an issue with nmap (see https://github.com/AI-Safety-Institute/ws-cyber/issues/364)
# Should remove this once Kali linux fixes this bug: https://bugs.kali.org/view.php?id=9085
RUN setcap cap_net_raw,cap_net_bind_service+eip /usr/lib/nmap/nmap

WORKDIR /root/

# Default command: sleep for 24 hours.
CMD [ "sleep", "86400" ]
