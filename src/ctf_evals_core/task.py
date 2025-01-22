from typing import Any

import yaml
from inspect_ai import Task, task
from inspect_ai.scorer import includes

from ._solvers.basic_agent import default_agent
from .dataset import (
    create_dataset,
    filter_dataset_by_metadata,
    filter_dataset_by_variant,
)


def create_ctf(
    challenges: str | list[str] | None = None,
    variants: str | list[str] | None = None,
    metadata_filters: list[str] | None = None,
    max_attempts: int = 3,
    base_directory: str | None = None,
    single_task: bool = True,
) -> list[Task]:
    """Create a task for CTF challenges.

    Args:
        challenges (str | list[str] | None): The path to the challenge directory or a
          list of challenge directories to load. Relative paths are resolved relative to
          the base directory. If None, all challenges are loaded.
        variants (str | list[str] | None): The variant or list of variants to include
          (e.g. "easy" or "easy,hard"). If None, all variants are included.
        metadata_filters (list[str] | None): A list of metadata filters to apply to the
            challenges.
        max_attempts (int): The maximum number of submission attempts before
          terminating. This argument is ignored if `agent` is provided.
        max_messages (int): The maximum number of messages in the conversation.
        base_directory (str | None): The default challenge directory to use to discover
            challenges. If None, the current working directory / "challenges" is used.
        single_task (bool): If True, create a single task for all samples. If False,
            create a task for each sample. Defaults to True.
    """
    dataset = create_dataset(base_dir=base_directory, challenges=challenges, single_task=single_task)

    # Apply variant filters
    if variants is not None:
        variants_set = {variants} if isinstance(variants, str) else set(variants)
        dataset = filter_dataset_by_variant(dataset, variants_set)

    # Apply metadata filters
    params = parse_sample_filters(metadata_filters)
    dataset = filter_dataset_by_metadata(dataset, params)

    # Check that we have challenges
    assert dataset and len(dataset) > 0, "No challenges found."
    return Task(
        dataset=dataset,
        plan=default_agent(max_attempts=max_attempts),
        scorer=includes(),
    )


@task
def ctf_task(
    challenges: str | list[str] | None = None,
    variants: str | list[str] | None = None,
    metadata_filters: list[str] | None = None,
    max_attempts: int = 3,
    base_directory: str | None = None,
    single_task: bool = True,
) -> Task:
    """Create a task for CTF challenges.

    Args:
        challenges (str | list[str] | None): The path to the challenge directory or a
          list of challenge directories to load. Relative paths are resolved relative to
          the base directory. If None, all challenges are loaded.
        variants (str | list[str] | None): The variant or list of variants to include
          (e.g. "easy" or "easy,hard"). If None, all variants are included.
        metadata_filters (list[str] | None): A list of metadata filters to apply to the
            challenges.
        max_attempts (int): The maximum number of submission attempts before
          terminating. This argument is ignored if `agent` is provided.
        max_messages (int): The maximum number of messages in the conversation.
        base_directory (str | None): The default challenge directory to use to discover
            challenges. If None, the current working directory / "challenges" is used.
        single_task (bool): If True, create a single task for all samples. If False,
            create a task for each sample. Defaults to True.
    """
    return create_ctf(challenges=challenges, variants=variants, metadata_filters=metadata_filters, max_attempts=max_attempts, base_directory=base_directory, single_task=single_task)


def parse_sample_filters(args: str | tuple[str] | list[str] | None) -> dict[str, Any]:
    """
    Parse the sample filters from the command line arguments.

    Should parse a list of key=value pairs into a dictionary. The input is expected
    to come from an inspect task argument so be of the form
    -T metadata_filters=type=flag,prod=True

    Args:
        args (tuple[str] | list[str] | None): The command line arguments.

    Returns:
        dict[str, Any]: The sample filters

    Example:
        >>> parse_sample_filters("type=flag")
        {'type': 'flag'}
        >>> parse_sample_filters(["type=flag", "prod=True"])
        {'type': 'flag', 'variant': True}
    """
    filters: dict[str, Any] = dict()
    if args is None:
        return filters
    if isinstance(args, str):
        args = [args]
    for arg in args:
        parts = arg.split("=")
        assert len(parts) == 2
        if len(parts) > 1:
            key = parts[0].replace("-", "_")
            value = yaml.safe_load("=".join(parts[1:]))
            if isinstance(value, str):
                value = value.split(",")
                value = value if len(value) > 1 else value[0]
            filters[key] = value
    return filters
