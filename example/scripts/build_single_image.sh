path_to_dockerfile_dir=$1

# Converts challenges/challengename/images/victim/Dockerfile -> ctf-challengename-victim:1.0.0
image_name=$(echo $path_to_dockerfile_dir | sed "s/\//-/g; s/images-//g; s/-Dockerfile//g; s/challenges/ctf/; s/$/:1.0.0/")

# Build the image

echo "Building image $image_name from $path_to_dockerfile_dir"
docker build -t $image_name $path_to_dockerfile_dir


