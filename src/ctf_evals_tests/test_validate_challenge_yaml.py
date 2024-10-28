import os
from glob import glob
from pathlib import Path

import pytest
import yaml


print("Hello, world!")
def _discover_challenge_task_modules() -> list[Path]:
    results = glob("challenges/**/challenge.yaml", recursive=True)
    results = [Path(result) for result in results]
    assert results, "Failed to discover any challenges for test"
    return results

def test_should_pass():
    assert True, "Should never hit this"

@pytest.mark.parametrize("task_module", _discover_challenge_task_modules())
def test_flag_and_flag_format_given_in_metadata(task_module: Path) -> None:
    challenge_data = yaml.load(open(task_module, "r"), Loader=yaml.FullLoader)
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
    assert len(prefix_and_flag) == 2, f"Flag is not in expected format for {task_module}"
    assert prefix_and_flag[1][-1] == "}", \
          f"Flag is not in expected format for {task_module}"

    # Check flag format hint is expected format
    prefix = flag.split("{")[0]
    expected_format = f"{prefix}" + "{" + "..." + "}"
    assert flag_format == expected_format, \
          f"Flag format does not match expected format for {task_module}"

@pytest.mark.parametrize("task_module", _discover_challenge_task_modules())
def test_files_exist_for_sandbox_copy(task_module: Path) -> None:
    parent_folder = task_module.parent
    assert task_module.is_file(), f"Failed to find task module {task_module}"
    data = yaml.load(open(task_module, "r"), Loader=yaml.FullLoader)
    assert data, f"Failed to parse task module {task_module}"

    # Collect files
    files = data.get("files", {})
    for variant in data.get("variant", []):
        files.update(variant.get("files", {}))

    # If no files are specified, skip the test
    if not files:
        pytest.skip("No files specified in task module")

    # Object should be key-value pairs where key is copy path and value is source path
    # Check source paths exist
    for source in files.values():
        file_path = parent_folder / source
        assert os.path.isfile(file_path), f"Failed to find source file {file_path}"

