from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from ctf_evals_core._util.docker import (
    ChallengeImagePlan,
    CommonImagePlan,
    EvalsCoreImagePlan,
    ImagePlan,
    get_images,
)


# Image resolution
def test_list_images():
    test_tree = Path(__file__).parent / "test_tree"
    images = get_images(root_dir=test_tree.resolve())

    # Should produce 1 common image (agent)
    # 3 challenge images (challenge1, challenge2, challenge3)
    # 1 evals_core image (kali agent)
    assert len(images) == 5
    counter = Counter(list(map(lambda x: x.__class__.__name__, images)))
    assert counter["ChallengeImagePlan"] == 3
    assert counter["CommonImagePlan"] == 1
    assert counter["EvalsCoreImagePlan"] == 1


@pytest.mark.parametrize(
    "dockerfile_path, expected_name, image_type",
    [
        (
            "ctf_evals_core/images/agent-environment/Dockerfile",
            "ctf-agent-environment",
            EvalsCoreImagePlan,
        ),
        (
            "challenges/ctf_redbeard/images/victim/Dockerfile",
            "ctf-ctf_redbeard-victim",
            ChallengeImagePlan,
        ),
    ],
)
def test_image_name_generation(
    dockerfile_path: str, expected_name: str, image_type: ImagePlan, monkeypatch
):
    monkeypatch.setattr("pathlib.Path.is_dir", lambda _: True)
    monkeypatch.setattr("pathlib.Path.exists", lambda _: image_type == ChallengeImagePlan)
    plan = image_type.from_dockerfile_path(dockerfile_path)
    name = plan.get_image_name()
    assert name == expected_name, f"Expected {expected_name}, got {name}"


SHOULD_BE_IN_IMAGES_MESSAGE = "should be in images folder"
SHOULD_BE_IN_EVALS_CORE = "should be in the ctf_evals_core folder"
NOT_CHALLENFES_FOLDER = "not a challenge folder"


@pytest.mark.parametrize(
    "dockerfile_path, image_type, message",
    [
        # Dockerfiles should be in folders within their expected locations
        (
            "challenges/challenge1/images/Dockerfile",
            ChallengeImagePlan,
            SHOULD_BE_IN_IMAGES_MESSAGE,
        ),
        ("images/Dockerfile", CommonImagePlan, SHOULD_BE_IN_IMAGES_MESSAGE),
        ("images/Dockerfile", EvalsCoreImagePlan, SHOULD_BE_IN_IMAGES_MESSAGE),
        # ChallengeImagePlans can't be made from common image folders
        ("images/Dockerfile", ChallengeImagePlan, SHOULD_BE_IN_IMAGES_MESSAGE),
        # Common and Core images can't be made from challenge folders
        (
            "challenges/challenge1/images/victim/Dockerfile",
            CommonImagePlan,
            NOT_CHALLENFES_FOLDER,
        ),
        (
            "challenges/challenge1/images/victim/Dockerfile",
            EvalsCoreImagePlan,
            SHOULD_BE_IN_EVALS_CORE,
        ),
        # Dockerfiles in resources of a challenge will not be valid under any regime
        (
            "challenges/challenge1/resources/Dockerfile",
            ChallengeImagePlan,
            SHOULD_BE_IN_IMAGES_MESSAGE,
        ),
        (
            "challenges/challenge1/resources/Dockerfile",
            EvalsCoreImagePlan,
            SHOULD_BE_IN_IMAGES_MESSAGE,
        ),
        (
            "challenges/challenge1/resources/Dockerfile",
            CommonImagePlan,
            SHOULD_BE_IN_IMAGES_MESSAGE,
        ),
    ],
)
def test_invalid_image_names(dockerfile_path: str, image_type: ImagePlan, message: str, monkeypatch):
    """Invalid images should raise an AssertionError.

    We expect dockerfile paths for plans to be:
    EvalsCoreImagePlan: images/somefoldername/Dockerfile
    ChallengeImagePlan: challenges/somefoldername/images/someotherfoldername/Dockerfile
    CommonImagePlan: images/somefoldername/Dockerfile
    All non matching names should raise an AssertionError.
    """
    monkeypatch.setattr("pathlib.Path.is_dir", lambda _: True)
    monkeypatch.setattr("pathlib.Path.exists", lambda _: True)
    with pytest.raises(ValidationError, match=message):
        plan = image_type.from_dockerfile_path(dockerfile_path)
        _ = plan.get_image_name()
