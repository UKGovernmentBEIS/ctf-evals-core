# Pin to specific version in order to keep evals consistent
# Use the command below to target a new release
# docker pull kalilinux/kali-last-release
# docker inspect -f '{{json .RepoDigests}}' kalilinux/kali-last-release | jq -r '.[0]'
FROM kalilinux/kali-last-release@sha256:92935ba0b1053dc765e627edb65d1981341b662ccaea99271f5ab40e387483a1


# Fix Kali key signing issue
RUN echo "Acquire::AllowInsecureRepositories \"true\";" > /etc/apt/apt.conf.d/99allow-insecure

# Avoid prompts during package installation.
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --allow-unauthenticated \
    curl

RUN curl https://archive.kali.org/archive-keyring.gpg -o /usr/share/keyrings/kali-archive-keyring.gpg

RUN rm /etc/apt/apt.conf.d/99allow-insecure
# Done fixing Kali issue


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

#GHIDRA Tool Support
RUN apt-get update && apt-get install -y default-jdk
# Install ghidra.
WORKDIR /usr/src/ghidra
ARG GHIDRA_ZIP=ghidra_11.0_PUBLIC_20231222.zip
ARG GHIDRA_HOME=/usr/src/ghidra/ghidra_11.0_PUBLIC
RUN wget https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.0_build/${GHIDRA_ZIP} && \
    unzip ${GHIDRA_ZIP} && \
    rm ${GHIDRA_ZIP}
# Read + execute permissions for all users.
RUN chmod -R 755 ${GHIDRA_HOME}
ENV GHIDRA_SCRIPTS /opt/scripts
ENV GHIDRA_HEADLESS "${GHIDRA_HOME}/support/analyzeHeadless"

# Copy scripts.
COPY scripts/DecompileToJson.java ${GHIDRA_SCRIPTS}/DecompileToJson.java
COPY scripts/DisassembleToJson.java ${GHIDRA_SCRIPTS}/DisassembleToJson.java
COPY scripts/run-ghidra.py ${GHIDRA_SCRIPTS}/run-ghidra.py
RUN chmod +x ${GHIDRA_SCRIPTS}/run-ghidra.py
#DONE Ghidra Tool Support

WORKDIR /root/

# Default command: sleep for 24 hours.
CMD [ "sleep", "86400" ]
