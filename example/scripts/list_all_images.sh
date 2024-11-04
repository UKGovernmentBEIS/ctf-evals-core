find challenges -name "Dockerfile" | sed "s/\//-/g; s/images-//g; s/-Dockerfile//g; s/challenges/ctf/g; s/$/:1.0.0/g"
