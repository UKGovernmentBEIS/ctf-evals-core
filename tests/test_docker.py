from pathlib import Path
from typing import Counter

import mock
import pytest
from pydantic import ValidationError

from ctf_evals_core._util.docker import (
    ChallengeImagePlan,
    CommonImagePlan,
    EvalsCoreImagePlan,
    get_images,
)


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
def test_image_name_generation(dockerfile_path, expected_name, image_type):
    with mock.patch("pathlib.Path.is_dir", return_value=True):
        with mock.patch(
            "pathlib.Path.exists", return_value=image_type == ChallengeImagePlan
        ):
            plan = image_type.from_dockerfile_path(Path(dockerfile_path))
            name = plan.get_image_name()
            assert name == expected_name, f"Expected {expected_name}, got {name}"


@pytest.mark.parametrize(
    "dockerfile_path, image_type",
    [
        # Dockerfiles should be in folders within their expected locations
        ("challenges/challenge1/images/Dockerfile", ChallengeImagePlan),
        ("images/Dockerfile", CommonImagePlan),
        ("images/Dockerfile", EvalsCoreImagePlan),
        # ChallengeImagePlans can't be made from common image folders
        ("images/Dockerfile", ChallengeImagePlan),
        # Common and Core images can't be made from challenge folders
        ("challenges/challenge1/images/victim/Dockerfile", CommonImagePlan),
        ("challenges/challenge1/images/vicim/Dockerfile", EvalsCoreImagePlan),
        # Dockerfiles in resources of a challenge will not be valid under any regime
        ("challenges/challenge1/resources/Dockerfile", ChallengeImagePlan),
        ("challenges/challenge1/resources/Dockerfile", EvalsCoreImagePlan),
        ("challenges/challenge1/resources/Dockerfile", CommonImagePlan),
    ],
)
def test_invalid_image_names(dockerfile_path, image_type):
    """Invalid images should raise an AssertionError.

    We expect dockerfile paths for plans to be:
    EvalsCoreImagePlan: images/somefoldername/Dockerfile
    ChallengeImagePlan: challenges/somefoldername/images/someotherfoldername/Dockerfile
    CommonImagePlan: images/somefoldername/Dockerfile
    All non matching names should raise an AssertionError.
    """
    with pytest.raises(ValidationError):
        with mock.patch("pathlib.Path.is_dir", return_value=True):
            with mock.patch("pathlib.Path.exists", return_value=True):
                plan = image_type.from_dockerfile_path(Path(dockerfile_path))
                plan.get_image_name()
