import os
from glob import glob
from pathlib import Path

import pytest
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from ctf_evals_core._util.docker import get_images


def _discover_challenge_task_modules() -> list[Path]:
    results = [
        Path(result) for result in glob("challenges/**/challenge.yaml", recursive=True)
    ]
    assert results, "Failed to discover any challenges for test"
    return results


def load_yaml(file):
    # Load YAML file using ruamel.yaml
    try:
        yaml = YAML()
        with open(file, "r") as file:
            data = yaml.load(file)
        return data
    except Exception:
        return None


@pytest.mark.parametrize("task_module", _discover_challenge_task_modules())
def test_flag_and_flag_format_given_in_metadata(task_module: Path) -> None:
    challenge_data = load_yaml(task_module)
    assert challenge_data, f"Failed to parse task module {task_module}"

    # Find flag
    flag = challenge_data.get("flag")
    assert flag, f"Failed to find flag in task module {task_module}"

    # Check flag_format_hint exists
    metadata = challenge_data.get("metadata")
    assert metadata, f"Failed to find metadata for challenge {task_module}"
    flag_format = metadata.get("flag_format_hint")
    assert flag_format, f"Failed to find flag_format_hint in metadata for {task_module}"

    # Check flag is expected format
    split = flag_format.split("...")
    assert (
        len(split) <= 2
    ), f"Flag format hint is not in expected format for {task_module}"
    assert flag.startswith(
        split[0]
    ), f"Start of flag does not match format hint for {task_module}"
    if len(split) == 2:
        assert flag.endswith(
            split[1]
        ), f"End of flag does not match format hint for {task_module}"


@pytest.mark.parametrize("task_module", _discover_challenge_task_modules())
def test_files_exist_for_sandbox_copy(task_module: Path) -> None:
    parent_folder = task_module.parent
    assert task_module.is_file(), f"Failed to find task module {task_module}"

    data = load_yaml(task_module)

    assert data, f"Failed to parse task module {task_module}"

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


DOCKER_AGENT_IMAGE = "ctf-agent-environment:1.0.0"


@pytest.mark.parametrize("task_module", _discover_challenge_task_modules())
def test_correct_agent_image(task_module: Path) -> None:
    compose_yaml = task_module.parent / "compose.yaml"
    data = load_yaml(compose_yaml)
    if data is None:
        pytest.skip(f"Failed to parse compose yaml {compose_yaml}")
        return
    agent_image = data.get("services", {}).get("default", {}).get("image")
    assert agent_image, f"Failed to find agent image in compose yaml {compose_yaml}"
    assert (
        agent_image == DOCKER_AGENT_IMAGE
    ), f"Agent image is not {DOCKER_AGENT_IMAGE} in compose yaml {compose_yaml}"


@pytest.mark.parametrize("task_module", _discover_challenge_task_modules())
def test_valid_images(task_module: Path) -> None:
    available_images = set(
        [f"{image.get_image_name()}:1.0.0" for image in get_images()]
    )
    compose_yaml = task_module.parent / "compose.yaml"
    data = load_yaml(compose_yaml)
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
        ), f"Image {image} in {compose_yaml} is not one generated by the build process"
