import re
import subprocess
from glob import glob
from pathlib import Path

import boto3
import pydantic


class ImagePlan(pydantic.BaseModel):
    context: Path

    def get_image_name(self) -> str:
        raise NotImplementedError

    def build_image(self):
        # There is a docker python library, but it doesn't give very good
        # output so use subprocess instead

        # When building locally we always tag with 1.0.0 since the image is mutable
        # The expectation is that images are built fresh regularly and immutable copies
        # are kept in ECR
        returncode = subprocess.check_call(
            [
                "docker",
                "build",
                "-t",
                f"{self.get_image_name()}:1.0.0",
                self.context,
            ]
        )
        if returncode != 0:
            print(f"Failed to build image {self.get_image_name()}:1.0.0")
            return False
        return True

    def tag(self, name: str):
        returncode = subprocess.check_call(
            ["docker", "tag", f"{self.get_image_name()}:1.0.0", name]
        )
        if returncode != 0:
            print(f"Failed to tag image {self.get_image_name()}:1.0.0")
            return False
        return True


class ChallengeImagePlan(ImagePlan):
    def get_image_name(self):
        context_path = str(self.context)
        image_name = context_path.replace("/", "-")
        image_name = image_name.replace("images-", "")
        image_name = image_name.replace("-Dockerfile", "")
        image_name = image_name.replace("challenges", "ctf")
        # Ensure valid name
        # ctf-some_valid_challenge_folder_name-some_valid_service_folder_name
        regex = r"^ctf-[a-zA-Z0-9_]+-[a-zA-Z0-9_]+$"
        assert re.match(regex, image_name), f"Invalid image name: {image_name}"
        return image_name


class CommonImagePlan(ImagePlan):
    # converts images/some_valid_image_folder_name/Dockerfile -> ctf-some_valid_image_folder_name
    def get_image_name(self):
        context_path = str(self.context)
        image_name = context_path.replace("/", "-")
        image_name = image_name.replace("images-", "ctf-")
        regex = r"^ctf-[a-zA-Z0-9_-]+$"
        assert re.match(regex, image_name), f"Invalid image name: {image_name}"
        return image_name


class EvalsCoreImagePlan(ImagePlan):
    # Converts .../ctf-evals-core/images/agent-> ctf-victim
    def get_image_name(self) -> str:
        image_name = str(self.context)
        image_name = image_name.split("ctf_evals_core/")[-1]
        image_name = image_name.replace("/", "-")
        image_name = image_name.replace("images-", "ctf-")
        # Ensure valid name
        # ctf-some_valid_challenge_folder_name-some_valid_service_folder_name
        regex = r"^ctf-[a-zA-Z0-9_-]+$"
        assert re.match(regex, image_name), f"Invalid image name: {image_name}"
        return image_name


# Discovers challenge image files in cwd/challenges, and uses a specific map from image
# path to image name
def _discover_challenge_dockerfiles() -> list[ChallengeImagePlan]:
    results = glob("challenges/**/Dockerfile", recursive=True)
    # Parent because docker expects the folder containing the Dockerfile
    results = [Path(result).parent for result in results]
    image_plans = [ChallengeImagePlan(context=result) for result in results]
    return image_plans


# Discovers a generic image in the cwd/images folder
def _discover_common_images() -> list[CommonImagePlan]:
    results = glob("images/**/Dockerfile", recursive=True)
    # Parent because docker expects the folder containing the Dockerfile
    results = [Path(result).parent for result in results]
    image_plans = [CommonImagePlan(context=result) for result in results]
    return image_plans


def _get_project_root():
    # breaks if the file is moved :/
    root = Path(__file__).parent.parent
    assert (
        root.name == "ctf_evals_core"
    ), f"Unexpected root folder: {root}. Perhaps build_images.py was moved?"  # noqa
    return root


# Discovers the evals-core image in the ctf_evals_core/images folder
# the long term solution is to have a docker registry for these images
def _discover_evals_core_images() -> list[EvalsCoreImagePlan]:
    images = _get_project_root() / "images"
    images = images.resolve()
    results = glob(f"{images}/**/Dockerfile", recursive=True)
    results = [Path(result).parent for result in results]
    image_plans = [EvalsCoreImagePlan(context=result) for result in results]
    return image_plans


def get_images() -> list[ImagePlan]:
    challenge_images = _discover_challenge_dockerfiles()
    common_images = _discover_common_images()
    evals_core_images = _discover_evals_core_images()
    all_images = challenge_images + common_images + evals_core_images
    return all_images


class Registry(pydantic.BaseModel):
    # Id of the registry in the form of 123456789012
    registry_id: str
    # subdomain of the registry of the form cyber-ctf
    subdomain: str
    # region of the registry
    region: str
    # prefix for images that aren't part of core
    challenge_prefix: str

    def registry(self):
        return f"{self.registry_id}.dkr.ecr.{self.region}.amazonaws.com"

    def login(self):
        ps = subprocess.Popen(
            ("aws", "ecr", "get-login-password", "--region", self.region),
            stdout=subprocess.PIPE,
        )
        try:
            _ = subprocess.check_output(
                (
                    "docker",
                    "login",
                    "--username",
                    "AWS",
                    "--password-stdin",
                    self.registry(),
                ),
                stdin=ps.stdout,
            )
            returncode = ps.wait()
            if returncode != 0:
                print(f"Failed to login to {self.registry()}")
                return False
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to login to {self.registry()}")
            return False
    def get_image_repository(self, image: ImagePlan):
        if isinstance(image, EvalsCoreImagePlan):
            return f"{self.subdomain}/{image.get_image_name()}"
        return f"{self.subdomain}/{self.challenge_prefix}/{image.get_image_name()}"

    def maybe_create_repository(self, image: ImagePlan):
        tags = self.get_image_tags(image)
        if len(tags) > 0:
            return
        returncode = subprocess.check_call(
            [
                "aws",
                "ecr",
                "create-repository",
                "--repository-name",
                self.get_image_repository(image),
                "--image-scanning-configuration",
                "scanOnPush=true",
                "--image-tag-mutability",
                "IMMUTABLE",
            ],
            stdout=subprocess.DEVNULL,
        )
        if returncode != 0:
            print(f"Failed to create repository {self.get_image_repository(image)}")
            return False
        return True

    def get_ecr_client(self):
        return boto3.client("ecr", region_name=self.region)

    def get_image_tags(self, image: ImagePlan):
        # Create an ECR client
        client = self.get_ecr_client()
        try:
            response = client.list_images(
                repositoryName=self.get_image_repository(image)
            )
            tags = [image["imageTag"] for image in response["imageIds"]]
            return tags
        except client.exceptions.RepositoryNotFoundException as e:
            return []
        except client.exceptions.ClientError as e:
            return []

    def check_tag_exists(self, image: ImagePlan, tag: str):
        return tag in self.get_image_tags(image)


    def get_full_image_name(self, image: ImagePlan):
        return f"{self.registry()}/{self.get_image_repository(image)}"

    def push_image(self, image: ImagePlan, tag: str):
        # 1. Checkif the tag already exists (tags are immutable)
        if self.check_tag_exists(image, tag):
            raise ValueError(f"Tag {tag} already exists for image {image}")

        self.maybe_create_repository(image)
        # 2. Build image with local naming then tag with full ecr name
        image.build_image()
        image_name = f"{self.get_full_image_name(image)}:{tag}"
        image.tag(image_name)
        # 3. Push the image
        returncode = subprocess.check_call(
            ["docker", "push", image_name],
        )
        if returncode != 0:
            print(f"Failed to push image {tag}")
            return False
        return True
