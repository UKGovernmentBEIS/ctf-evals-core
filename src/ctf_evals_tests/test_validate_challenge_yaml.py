import os
from pathlib import Path

import pytest
from ruamel.yaml.comments import CommentedMap

from .utils import comment_contains, discover_challenge_task_modules, load_yaml


@pytest.mark.parametrize("task_module", discover_challenge_task_modules())
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
    ), f"Flag format hint is not in expected format for {task_module}"  # noqa
    assert flag.startswith(
        split[0]
    ), f"Start of flag does not match format hint for {task_module}"  # noqa
    if len(split) == 2:
        assert flag.endswith(
            split[1]
        ), f"End of flag does not match format hint for {task_module}"  # noqa


@pytest.mark.parametrize("task_module", discover_challenge_task_modules())
def test_files_exist_for_sandbox_copy(task_module: Path) -> None:
    parent_folder = task_module.parent
    assert task_module.is_file(), f"Failed to find task module {task_module}"

    data = load_yaml(task_module)

    assert data, f"Failed to parse task module {task_module}"

    # Collect files
    def collect_files(files_map: CommentedMap) -> dict[str, str]:
        comments = files_map.ca.items
        files = {}
        for key, value in files_map.items():
            file_comments = comments.get(key, [])
            if not comment_contains("pathcheck_ignore", file_comments):
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
