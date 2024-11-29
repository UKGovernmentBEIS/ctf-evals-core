# Pin to specific version in order to keep evals consistent
# Use the command below to target a new release
# docker pull kalilinux/kali-last-release
# docker inspect -f '{{json .RepoDigests}}' kalilinux/kali-last-release | jq -r '.[0]'
FROM kalilinux/kali-last-release@sha256:92935ba0b1053dc765e627edb65d1981341b662ccaea99271f5ab40e387483a1

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

WORKDIR /root/

# Default command: sleep for 24 hours.
CMD [ "sleep", "86400" ]
