import os
from pathlib import Path
from typing import Any, Callable, Generator

import yaml
from inspect_ai.dataset import Dataset, MemoryDataset, Sample
from inspect_ai.util import SandboxEnvironmentType

from .model import ChallengeInfo

CHALLENGE_INFO_FILENAME = "challenge.yaml"


def create_dataset(
    base_dir: str | None, challenges: str | list[str] | None = None
) -> Dataset:
    """
    Create a dataset from a directory of challenges.

    Args:
        base_dir (str | None): The path to the directory containing the
            challenges to load. If None, the path "challenges" is used relative to cwd.
        challenges: (str | list[str] | None): An optional list of subdirectories within
            the challenges directory to load. If None, all challenges are loaded
    """
    if base_dir is None:
        challenges_path = Path.cwd() / "challenges"
    else:
        challenges_path = Path(base_dir)

    def _make_absolute(path: str) -> Path:
        return challenges_path / path

    def get_challenge_dir_paths() -> list[Path]:
        # If no challenges are specified, use the default challenge directory.
        if challenges is None:
            return [challenges_path]
        if isinstance(challenges, str):
            return [_make_absolute(challenges)]
        return [_make_absolute(x) for x in challenges]

    challenge_dir_paths = get_challenge_dir_paths()
    challenge_dirs = list(_find_challenge_dirs_recursive(challenge_dir_paths))
    return MemoryDataset(samples=list(_create_samples(challenge_dirs)))


def filter_dataset_by_variant(dataset: Dataset, variants: set[str]) -> Dataset:
    """
    Filter a dataset to just samples with a specific variant.

    Args:
        dataset (Dataset): The dataset to filter.
        variants (set[str]): A set of variant names to filter the dataset by. Only
          samples with a variant name contained in this set are included.
    """
    return dataset.filter(
        # Check that metadata is not None to satisfy mypy.
        lambda x: x.metadata is not None and x.metadata["variant"] in variants
    )


def filter_dataset_by_metadata(dataset: Dataset, filters: dict[str, Any]) -> Dataset:
    """
    Filter a dataset to just samples which match the given metadata filters.

    Keys in the filters are used to check variant metadata then challenge metadata
    then task metadata.

    Args:
        dataset (Dataset): The dataset to filter.
        filters (dict[str, Any]): A dictionary of metadata filters to apply to the
            dataset. Only samples with metadata matching the filters are included.
    """

    def get_key_from_metadata(metadata, key) -> Any:
        # Prefer variant metadata over challenge metadata over typical metadata.
        variant_metadata = metadata.get("variant_metadata", {})
        challenge_metadata = metadata.get("challenge_metadata", {})
        value = variant_metadata.get(
            key, challenge_metadata.get(key, metadata.get(key, None))
        )
        return value

    def sample_predicate(sample: Sample) -> bool:
        # All filters must be satisfied
        return all(
            get_key_from_metadata(sample.metadata, key) == value
            for key, value in filters.items()
        )

    return dataset.filter(sample_predicate)


def _find_challenge_dirs_recursive(
    challenges_dirs: list[Path],
) -> Generator[Path, None, None]:
    for challenge_dir in challenges_dirs:
        if not challenge_dir.exists():
            raise NotADirectoryError(f"Could not find: '{challenge_dir}'")
        for file in challenge_dir.rglob(CHALLENGE_INFO_FILENAME):
            yield file.parent


def _create_samples(challenge_dirs: list[Path]) -> Generator[Sample, None, None]:
    sandbox_from_dir = _make_sandbox_resolver()
    for challenge_dir in challenge_dirs:
        challenge_info = _load_challenge_info(challenge_dir)
        challenge_files = _make_paths_absolute(challenge_info.files, challenge_dir)
        sandbox = sandbox_from_dir(challenge_dir)
        if sandbox is None:
            continue

        # Create a sample for each variant of the challenge.
        for variant_name, variant in challenge_info.variants.items():
            variant_files = _make_paths_absolute(variant.files, challenge_dir)
            # Will be None if spec file can't be found
            yield Sample(
                id=f"{challenge_info.name}-{variant_name}",
                input=variant.prompt,
                target=challenge_info.flag,
                files=challenge_files | variant_files,
                metadata={
                    "variant": variant_name,
                    "challenge": challenge_info.name,
                    "challenge_metadata": challenge_info.metadata,
                    "variant_metadata": variant.metadata,
                },
                sandbox=sandbox,
            )


def _load_challenge_info(challenge: Path) -> ChallengeInfo:
    # Each challenge directory must have a CHALLENGE_INFO_FILENAME file.
    yaml_path = challenge / CHALLENGE_INFO_FILENAME
    try:
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Could not find {CHALLENGE_INFO_FILENAME} in '{challenge}'."
        )
    return ChallengeInfo(**data)


def _make_paths_absolute(files: dict[str, str], base_path: Path) -> dict[str, str]:
    return {key: _make_path_absolute(value, base_path) for key, value in files.items()}


SANDBOX_SPEC_VAR = "CTF_SANDBOX_SPEC_FILE"
SANDBOX_PROVIDER_VAR = "CTF_SANDBOX_PROVIDER"


def _make_sandbox_resolver() -> Callable[[Path], SandboxEnvironmentType | None]:
    if (
        SANDBOX_PROVIDER_VAR not in os.environ
        or os.environ[SANDBOX_PROVIDER_VAR] == "docker"
    ):
        print("Using docker sandbox")
        return lambda challenge_dir: (
            "docker",
            _make_path_absolute("compose.yaml", challenge_dir),
        )
    sandbox = os.environ[SANDBOX_PROVIDER_VAR]
    if SANDBOX_SPEC_VAR not in os.environ:
        print(f"Using {sandbox} sandbox with no spec file")
        return lambda challenge_dir: sandbox

    spec_file = os.environ[SANDBOX_SPEC_VAR]
    print(f"Using {sandbox} sandbox with spec file {spec_file}")

    def make_alt_sandbox_spec(challenge_dir) -> SandboxEnvironmentType | None:
        path = _make_path_absolute(spec_file, Path(challenge_dir))
        if not Path(path).is_file():
            print(f"No sandbox spec file found for challenge directory {challenge_dir}")
            return None
        return (sandbox, path)

    return make_alt_sandbox_spec


def _make_path_absolute(path_or_content: str, base_path: Path) -> str:
    if Path(path_or_content).is_absolute():
        return path_or_content
    path = base_path / path_or_content
    if path.is_file():
        return str(path.resolve())
    return path_or_content
