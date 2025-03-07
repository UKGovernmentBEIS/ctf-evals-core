import os
from glob import glob
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from ctf_evals_core._util.docker import get_images

CHALLENGE_YAML_SCHEMA = r"""
$schema: http://json-schema.org/draft-07/schema#
type: object
required:
  - name
  - flag
  - metadata
  - variants
properties:
  name:
    type: string
    description: Short name of the challenge
    pattern: ^[a-z0-9_]+$
  flag:
    type: string
    description: The flag that solves the challenge
    pattern: ^[^{}]+{[^{}]+}$
  files:
    type: object
    description: Files to be deployed with the challenge
  metadata:
    type: object
    required:
      - flag_format_hint
    properties:
      flag_format_hint:
        type: string
        description: Hint about the flag format
        pattern: ^[^{}]+{\.\.\.}$
  variants:
    type: object
    required:
      - minimal
    additionalProperties:
      type: object
      required:
        - prompt
      properties:
        prompt:
          type: string
          description: Variant prompt
        files:
          type: object
          description: Variant-specific files

"""


def _discover_challenge_task_modules() -> list[Path]:
    results = [
        Path(result) for result in glob("challenges/**/challenge.yaml", recursive=True)
    ]
    assert results, "Failed to discover any challenges for test"
    return results


def _load_yaml(file):
    try:
        yaml = YAML()
        with open(file, "r") as file:
            data = yaml.load(file)
        return data
    except Exception:
        return None


def _load_challenge_schema():
    return YAML().load(CHALLENGE_YAML_SCHEMA)


@pytest.mark.parametrize("task_module", _discover_challenge_task_modules(), ids=str)
def test_valid_challenge_yaml_schema(task_module: Path) -> None:
    challenge_data = _load_yaml(task_module)
    challenge_schema = _load_challenge_schema()
    assert challenge_data, f"Failed to parse task module {task_module}"

    try:
        validate(challenge_data, challenge_schema)
    except ValidationError as e:
        error_path = ".".join(str(p) for p in e.path) if e.path else "root"
        error_message = f"""
Validation error in "{task_module}":
Path: {error_path}
Error: {e.message}
"""
        raise pytest.fail.Exception(error_message) from None


@pytest.mark.parametrize("task_module", _discover_challenge_task_modules(), ids=str)
def test_challenge_name_matches_directory_name(task_module: Path) -> None:
    challenge_data = _load_yaml(task_module)
    name = challenge_data.get("name")

    assert (
        name == task_module.parent.name
    ), f'Challenge name "{name}" in {task_module} must match the directory name "{task_module.parent.name}"'


@pytest.mark.parametrize("task_module", _discover_challenge_task_modules(), ids=str)
def test_flag_and_flag_format_matches(task_module: Path) -> None:
    challenge_data = _load_yaml(task_module)
    flag = challenge_data.get("flag")
    flag_format = challenge_data.get("metadata").get("flag_format_hint")

    assert flag.split("{")[0] == flag_format.split("{")[0]


@pytest.mark.parametrize("task_module", _discover_challenge_task_modules(), ids=str)
def test_files_exist_for_sandbox_copy(task_module: Path) -> None:
    parent_folder = task_module.parent
    assert task_module.is_file(), f"Failed to find task module {task_module}"

    data = _load_yaml(task_module)

    # Collect files
    def collect_files(files_map: CommentedMap) -> dict:
        comments = files_map.ca.items
        files = {}
        for key, value in files_map.items():
            ignore = False
            file_comments = comments.get(key, [])
            for comment in file_comments:
                if comment is None:
                    continue
                if "pathcheck_ignore" in comment.value:
                    ignore = True
                    break
            if not ignore:
                files[key] = value
            else:
                print(f"Skipping file {key} due to pathcheck_ignore comment")
        return files

    files = collect_files(data.get("files", CommentedMap()))
    for variant in data.get("variants", {}).values():
        files.update(collect_files(variant.get("files", CommentedMap())))

    # If no files are specified, skip the test
    if not files:
        pytest.skip("No files specified in task module")

    # Object should be key-value pairs where key is copy path and value is source path
    # Check source paths exist
    for source in files.values():
        file_path = parent_folder / source
        assert os.path.isfile(
            file_path
        ), f"Failed to find source file {file_path}. Either the path is incorrect or you are missing a # pathcheck_ignore comment in the challenge.yaml file."  # noqa: E501


@pytest.mark.parametrize("task_module", _discover_challenge_task_modules(), ids=str)
def test_default_service_present(task_module: Path) -> None:
    compose_yaml = task_module.parent / "compose.yaml"
    data = _load_yaml(compose_yaml)
    if data is None:
        pytest.skip(f"Failed to parse compose yaml {compose_yaml}")
        return
    agent_image = data.get("services", {}).get("default", {}).get("image")
    assert agent_image, f"Failed to find default service in compose yaml {compose_yaml}. This necessary as it is the service agents run in"  # noqa: E501


@pytest.mark.parametrize("task_module", _discover_challenge_task_modules(), ids=str)
def test_valid_images(task_module: Path) -> None:
    available_images = set(
        [f"{image.get_image_name()}:1.0.0" for image in get_images()]
    )
    compose_yaml = task_module.parent / "compose.yaml"
    data = _load_yaml(compose_yaml)
    if not data:
        pytest.skip(f"Failed to parse compose yaml {compose_yaml}")
        return
    services = data.get("services", CommentedMap())
    for service in services.keys():
        service_comments = services[service].ca.items
        image = services[service].get("image")
        assert (
            image
        ), f"Failed to find image for service {service} in compose yaml {compose_yaml}"
        image_comments = service_comments.get("image", [])
        skip_check = False
        for comment in image_comments:
            if comment is None:
                continue
            if "imagecheck_ignore" in comment.value:
                skip_check = True
                break
        if skip_check:
            continue
        assert (
            image in available_images
        ), f"Image {image} in {compose_yaml} is not one generated by the build process either the name is incorrect or you are missing a # imagecheck_ignore comment in the compose.yaml file."  # noqa: E501
