from pathlib import Path

import pytest

from ctf_evals_core._util.docker import (
    _convert_challenge_image_path_to_image_name,
    _convert_common_image_path_to_image_name,
    _convert_core_image_path_to_image_name,
    _discover_evals_core_images,
    _get_project_root,
)

VALID_EVALS_CORE_IMAGES = [
    "ctf-agent-environment:1.0.0",
]


def test_project_root():
    assert _get_project_root().name == "ctf-evals-core"


def test_dockefiles():
    images = _discover_evals_core_images()
    assert len(images) == 1
    tags = [tag for _, tag in images]
    assert tags == VALID_EVALS_CORE_IMAGES


@pytest.mark.parametrize(
    "path,expected",
    [
        (".venv/some/stuff/ctf-evals-core/images/agent", "ctf-agent:1.0.0"),
        ("challenges/example/images/victim", "ctf-example-victim:1.0.0"),
        ("images/example", "ctf-example:1.0.0"),
        ("images/example-example", "ctf-example-example:1.0.0"),
    ],
)
def test_name_conversion(path, expected):
    if "challenges" in path:
        assert _convert_challenge_image_path_to_image_name(Path(path)) == expected
    elif "ctf-evals-core" in path:
        assert _convert_core_image_path_to_image_name(Path(path)) == expected
    else:
        assert _convert_common_image_path_to_image_name(Path(path)) == expected
