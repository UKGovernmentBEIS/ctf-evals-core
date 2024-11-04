import os
from glob import glob
from pathlib import Path

import pytest
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


def _discover_challenge_task_modules() -> list[Path]:
    results = glob("challenges/**/challenge.yaml", recursive=True)
    results = [Path(result) for result in results]
    assert results, "Failed to discover any challenges for test"
    return results


def load_yaml(file):
    # Load YAML file using ruamel.yaml
    try:
        yaml = YAML()
        with open(file, "r") as file:
            data = yaml.load(file)
        return data
    except Exception as e:
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
    prefix_and_flag = flag.split("{")
    assert (
        len(prefix_and_flag) == 2
    ), f"Flag is not in expected format for {task_module}"
    assert (
        prefix_and_flag[1][-1] == "}"
    ), f"Flag is not in expected format for {task_module}"

    # Check flag format hint is expected format
    prefix = flag.split("{")[0]
    expected_format = f"{prefix}" + "{" + "..." + "}"
    assert (
        flag_format == expected_format
    ), f"Flag format does not match expected format for {task_module}"


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
HELM_AGENT_IMAGE = "257469545531.dkr.ecr.eu-west-2.amazonaws.com/superintendent/cyber-ctf/agent-environment:1.1.0"  # noqa: E501


@pytest.mark.parametrize("task_module", _discover_challenge_task_modules())
def test_correct_agent_image(task_module: Path) -> None:
    compose_yaml = task_module.parent / "compose.yaml"
    data = load_yaml(compose_yaml)
    assert data, f"Failed to parse compose yaml {compose_yaml}"
    agent_image = data.get("services", {}).get("default", {}).get("image")
    assert agent_image, f"Failed to find agent image in compose yaml {compose_yaml}"
    assert (
        agent_image == DOCKER_AGENT_IMAGE
    ), f"Agent image is not {DOCKER_AGENT_IMAGE} in compose yaml {compose_yaml}"


    helm_chart = task_module.parent / "helm-values.yaml"
    data = load_yaml(helm_chart)
    if not data:
        pytest.skip(f"Failed to parse helm chart {helm_chart}")
    agent_image = data.get("services", {}).get("default", {}).get("image")
    assert agent_image, f"Failed to find agent image in helm chart {helm_chart}"
    assert (
        agent_image == HELM_AGENT_IMAGE
    ), f"Agent image is not {HELM_AGENT_IMAGE} in helm chart {helm_chart}"


