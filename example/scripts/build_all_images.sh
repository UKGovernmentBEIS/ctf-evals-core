find challenges -name "Dockerfile" | sed "s/.Dockerfile$//" | xargs -n 1 ./scripts/build_single_image.sh
docker build -t ctf-agent-environment:1.0.0 images/agent-execution-environment
docker build -t ctf-ghidra-environment:1.0.0 images/ghidra-execution-environment
