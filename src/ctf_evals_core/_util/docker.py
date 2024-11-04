import re
import subprocess
from glob import glob
from pathlib import Path


# Converts challenges/challengename/images/victim-> ctf-challengename-victim:1.0.0
def _convert_challenge_image_path_to_image_name(context_path: Path) -> str:
    context_path = str(context_path)
    image_name = context_path.replace("/", "-")
    image_name = image_name.replace("images-", "")
    image_name = image_name.replace("-Dockerfile", "")
    image_name = image_name.replace("challenges", "ctf")
    image_name = f"{image_name}:1.0.0"
    # Ensure valid name
    # ctf-some_valid_challenge_folder_name-some_valid_service_folder_name:1.0.0
    regex = r"^ctf-[a-zA-Z0-9_]+-[a-zA-Z0-9_]+:1.0.0$"
    assert re.match(regex, image_name), f"Invalid image name: {image_name}"
    return image_name

# Discovers challenge image files in cwd/challenges, and uses a specific map from image
# path to image name
def _discover_challenge_dockerfiles() -> list[tuple[Path, str]]:
    results = glob("challenges/**/Dockerfile", recursive=True)
    # Parent because docker expects the folder containing the Dockerfile
    results = [Path(result).parent for result in results]
    pairs = [
        (result, _convert_challenge_image_path_to_image_name(result))
        for result in results
    ]
    return pairs

# Converts images/agent-> ctf-victim:1.0.0
def _convert_common_image_path_to_image_name(context_path: Path) -> str:
    context_path = str(context_path)
    image_name = context_path.replace("/", "-")
    image_name = image_name.replace("images-", "ctf-")
    image_name = f"{image_name}:1.0.0"
    # Ensure valid name
    # ctf-some_valid_challenge_folder_name-some_valid_service_folder_name:1.0.0
    regex = r"^ctf-[a-zA-Z0-9_-]+:1.0.0$"
    assert re.match(regex, image_name), f"Invalid image name: {image_name}"
    return image_name

# Discovers a generic image in the cwd/images folder
def _discover_common_images() -> list[tuple[Path, str]]:
    results = glob("images/**/Dockerfile", recursive=True)
    # Parent because docker expects the folder containing the Dockerfile
    results = [Path(result).parent for result in results]
    pairs = [
        (result, _convert_common_image_path_to_image_name(result))
        for result in results
    ]
    return pairs

def _get_project_root():
    # breaks if the file is moved :/
    root = Path(__file__).parent.parent
    assert (
        root.name == "ctf_evals_core"
    ), f"Unexpected root folder: {root}. Perhaps build_images.py was moved?"  # noqa
    return root

# Converts .../ctf-evals-core/images/agent-> ctf-victim:1.0.0
def _convert_core_image_path_to_image_name(context_path: Path) -> str:
    image_name = str(context_path)
    image_name = image_name.split("ctf_evals_core/")[-1]
    image_name = image_name.replace("/", "-")
    image_name = image_name.replace("images-", "ctf-")
    image_name = f"{image_name}:1.0.0"
    # Ensure valid name
    # ctf-some_valid_challenge_folder_name-some_valid_service_folder_name:1.0.0
    regex = r"^ctf-[a-zA-Z0-9_-]+:1.0.0$"
    assert re.match(regex, image_name), f"Invalid image name: {image_name}"
    return image_name

# Discovers the evals-core image in the ctf_evals_core/images folder
# the long term solution is to have a docker registry for these images
def _discover_evals_core_images() -> list[tuple[Path, str]]:

    images = _get_project_root() / "images"
    images = images.resolve()
    results = glob(f"{images}/**/Dockerfile", recursive=True)
    results = [Path(result).parent for result in results]
    pairs = [
        (result, _convert_core_image_path_to_image_name(result))
        for result in results
    ]
    return pairs


def get_images() -> list[tuple[Path, str]]:
    challenge_images = _discover_challenge_dockerfiles()
    common_images = _discover_common_images()
    evals_core_images = _discover_evals_core_images()

    all_images = challenge_images + common_images + evals_core_images
    return all_images


def build_image(context: Path, tag: str):
    # There is a docker python library, but it doesn't give very good
    # output so use subprocess instead
    returncode = subprocess.check_call(["docker", "build", "-t", tag, context])
    if returncode != 0:
        print(f"Failed to build image {tag}")
        return False
    return True
