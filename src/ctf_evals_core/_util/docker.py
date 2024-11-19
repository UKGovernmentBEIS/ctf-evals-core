import re
import subprocess
from glob import glob
from pathlib import Path
from typing import cast, override

import boto3
import pydantic
from pydantic import field_validator


class ImagePlan(pydantic.BaseModel):
    """Base class for image plans. Subclasses should implement get_image_name.

    The context field should be a path to the directory containing the Dockerfile.
    """
    context: Path

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        assert v.is_dir(), f"Invalid context: {v}"
        return v

    @classmethod
    def from_dockerfile_path(cls, path: str):
        assert Path(path).name == "Dockerfile", "Invalid dockerfile path"
        return cls(context=Path(path).parent)

    def get_image_name(self) -> str:
        raise NotImplementedError

    def build_image(self):
        # There is a docker python library, but it doesn't give very good
        # output so use subprocess instead

        # When building locally we always tag with 1.0.0 since the image is mutable
        # The expectation is that images are built fresh regularly and immutable copies
        # are kept in ECR
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
    """Image plan for challenge images.

    The context should be a path to the directory containing the Dockerfile, which
    should be of the form challenge_folder/images/service_folder. where the challenge
    folder contains a challenge.yaml file.
    """
    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        assert v.is_dir(), f"Invalid context: {v}, should be a directory"
        assert (
            v.parent.name == "images"
        ), f"Invalid context: {v}, should be in images folder"
        challenge_dir = v.parent.parent
        assert (
            challenge_dir.is_dir()
        ), f"Invalid context: {v}, should be in a challenge folder"
        challengeyaml = challenge_dir / "challenge.yaml"
        assert challengeyaml.exists(), f"Invalid context: {v}, should be in a challenge folder containing a challenge.yaml file"  # noqa
        return v

    @override
    def get_image_name(self):
        context_path = str(self.context)
        image_name = context_path.split("challenges/")[-1]

        # must be in a directory inside a images directory
        image_name = image_name.replace("/", "-")
        image_name = image_name.replace("images-", "")
        image_name = "ctf-" + image_name
        # Ensure valid name
        # ctf-some_valid_challenge_folder_name-some_valid_service_folder_name
        regex = r"^ctf-[a-zA-Z0-9_]+-[a-zA-Z0-9_]+$"
        assert re.match(regex, image_name), f"Invalid image name: {image_name}"
        return image_name


class CommonImagePlan(ImagePlan):
    """Image plan for common images.

    The context should be a path to the directory containing the Dockerfile, which
    should be of the form images/some_image_folder.
    """

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        assert v.is_dir(), f"Invalid context: {v}, should be a directory"
        assert (
            v.parent.name == "images"
        ), f"Invalid context: {v}, should be in images folder"
        maybe_challenge_dir = v.parent.parent
        challengeyaml = maybe_challenge_dir / "challenge.yaml"
        assert not challengeyaml.exists(), f"Invalid context: {v}, should be in a top level images folder not a challenge folder"  # noqa
        return v

    @override
    def get_image_name(self):
        image_name = str(self.context)
        image_name = image_name.split("images/")[-1]
        image_name = image_name.replace("/", "-")
        image_name = "ctf-" + image_name
        regex = r"^ctf-[a-zA-Z0-9_-]+$"
        assert re.match(regex, image_name), f"Invalid image name: {image_name}"
        return image_name


class EvalsCoreImagePlan(ImagePlan):
    """Image plan for the ctf_evals_core image.

    The context should be a path to the directory containing the Dockerfile, which
    should be of the form ctf_evals_core/images/some_image_folder.
    """

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        assert v.is_dir(), f"Invalid context: {v}, should be a directory"
        assert (
            v.parent.name == "images"
        ), f"Invalid context: {v}, should be in images folder"
        core_dir = v.parent.parent
        assert (
            core_dir.name == "ctf_evals_core"
        ), f"Invalid context: {v}, should be in the ctf_evals_core folder"  # noqa
        challengeyaml = core_dir / "challenge.yaml"
        assert not challengeyaml.exists(), f"Invalid context: {v}, should be in a top level images folder not a challenge folder"  # noqa
        return v

    @override
    def get_image_name(self) -> str:
        image_name = str(self.context)
        image_name = image_name.split("images/")[-1]
        image_name = image_name.replace("/", "-")
        image_name = "ctf-" + image_name
        # Ensure valid name
        # ctf-some_valid_challenge_folder_name-some_valid_service_folder_name
        regex = r"^ctf-[a-zA-Z0-9_-]+$"
        assert re.match(regex, image_name), f"Invalid image name: {image_name}"
        return image_name

def get_images(root_dir: Path | None = None) -> list[ImagePlan]:
    """Discovers all images in the given root directory.

    Args:
        root_dir (Path, optional): The root directory to search for images. Defaults to
            None. if None, the current working directory is used.
    """
    root_dir = root_dir or Path.cwd()
    challenge_images = _discover_challenge_dockerfiles(root_dir=root_dir)
    common_images = _discover_common_images(root_dir=root_dir)
    evals_core_images = _discover_evals_core_images()
    all_images = challenge_images + common_images + evals_core_images
    return cast(list[ImagePlan], all_images)


class Registry(pydantic.BaseModel):
    """Represents an ECR registry.

    Used to push images to the registry and keep track of the subdomain in which to
    push images.
    """
    # Id of the registry in the form of 123456789012
    registry_id: str
    # subdomain of the registry of the form cyber-ctf
    subdomain: str
    # region of the registry
    region: str
    # prefix for images that aren't part of core
    challenge_prefix: str

    def registry(self):
        """Returns the full registry name."""
        return f"{self.registry_id}.dkr.ecr.{self.region}.amazonaws.com"

    def login(self):
        """Logs in to aws ecr."""
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
        except subprocess.CalledProcessError:
            print(f"Failed to login to {self.registry()}")
            return False

    def get_image_repository(self, image: ImagePlan):
        """Returns the repository name for the image."""
        if isinstance(image, EvalsCoreImagePlan):
            return f"{self.subdomain}/{image.get_image_name()}"
        return f"{self.subdomain}/{self.challenge_prefix}/{image.get_image_name()}"

    def _maybe_create_repository(self, image: ImagePlan):
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
            print(f"Failed to create repository {
                  self.get_image_repository(image)}")
            return False
        return True

    def _get_ecr_client(self):
        return boto3.client("ecr", region_name=self.region)

    def get_image_tags(self, image: ImagePlan):
        """Get the tags for the given image."""
        # Create an ECR client
        client = self._get_ecr_client()
        try:
            response = client.list_images(
                repositoryName=self.get_image_repository(image)
            )
            tags = [image["imageTag"] for image in response["imageIds"]]
            return tags
        except client.exceptions.RepositoryNotFoundException:
            return []
        except client.exceptions.ClientError:
            return []

    def _check_tag_exists(self, image: ImagePlan, tag: str):
        return tag in self.get_image_tags(image)

    def _get_full_image_name(self, image: ImagePlan):
        return f"{self.registry()}/{self.get_image_repository(image)}"

    def push_image(self, image: ImagePlan, tag: str):
        """Push an ImagePlan to the registry with the given tag."""
        # 1. Checkif the tag already exists (tags are immutable)
        if self._check_tag_exists(image, tag):
            raise ValueError(f"Tag {tag} already exists for image {image}")

        self._maybe_create_repository(image)
        # 2. Build image with local naming then tag with full ecr name
        image.build_image()
        image_name = f"{self._get_full_image_name(image)}:{tag}"
        image.tag(image_name)
        # 3. Push the image
        returncode = subprocess.check_call(
            ["docker", "push", image_name],
        )
        if returncode != 0:
            print(f"Failed to push image {tag}")
            return False
        return True

def _discover_challenge_dockerfiles(root_dir: Path) -> list[ChallengeImagePlan]:
    results = glob(f"{root_dir}/challenges/**/Dockerfile", recursive=True)
    # Parent because docker expects the folder containing the Dockerfile
    image_plans = [
        ChallengeImagePlan.from_dockerfile_path(result) for result in results
    ]
    return image_plans


# Discovers a generic image in the cwd/images folder
def _discover_common_images(root_dir: Path) -> list[CommonImagePlan]:
    results = glob(f"{root_dir}/images/**/Dockerfile", recursive=True)
    # Parent because docker expects the folder containing the Dockerfile
    image_plans = [CommonImagePlan.from_dockerfile_path(result) for result in results]
    return image_plans


def _get_core_root():
    # breaks if the file is moved :/
    root = Path(__file__).parent.parent
    assert (
        root.name == "ctf_evals_core"
    ), f"Unexpected root folder: {root}. Perhaps build_images.py was moved?"  # noqa
    return root


# Discovers the evals-core image in the ctf_evals_core/images folder
# the long term solution is to have a docker registry for these images
def _discover_evals_core_images() -> list[EvalsCoreImagePlan]:
    images = _get_core_root() / "images"
    images = images.resolve()
    results = glob(f"{images}/**/Dockerfile", recursive=True)
    image_plans = [
        EvalsCoreImagePlan.from_dockerfile_path(result) for result in results
    ]
    return image_plans
