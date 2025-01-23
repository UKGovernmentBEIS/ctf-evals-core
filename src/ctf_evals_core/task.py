from typing import Any

import yaml
from inspect_ai import Task, task
from inspect_ai._eval.task.task import MemoryDataset, Scorer, Solver
from inspect_ai.scorer import includes

from ._solvers.basic_agent import default_agent
from .dataset import (
    create_dataset,
    filter_dataset_by_metadata,
    filter_dataset_by_variant,
    split_dataset_by_challenge,
)


def create_ctf_tasks(
    challenges: str | list[str] | None = None,
    variants: str | list[str] | None = None,
    metadata_filters: list[str] | None = None,
    max_attempts: int = 3,
    base_directory: str | None = None,
    single_task: bool = False,
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
            create a task for each sample. Defaults to False.
    """
    dataset = create_dataset(base_dir=base_directory, challenges=challenges)

    # Apply variant filters
    if variants is not None:
        variants_set = {variants} if isinstance(variants, str) else set(variants)
        dataset = filter_dataset_by_variant(dataset, variants_set)

    # Apply metadata filters
    params = parse_sample_filters(metadata_filters)
    dataset = filter_dataset_by_metadata(dataset, params)

    # Check that we have challenges
    assert dataset and len(dataset) > 0, "No challenges found."

    datasets = [dataset]
    if not single_task:
        datasets = list(split_dataset_by_challenge(dataset))

    tasks = [
        create_ctf_task_from_dataset(dataset, max_attempts=max_attempts)
        for dataset in datasets
    ]

    return tasks


def create_ctf_task_from_dataset(
    dataset: MemoryDataset,
    plan: Solver | None = None,
    max_attempts: int = 3,
    scorer: Scorer | None = None,
    name: str | None = None,
):
    """Creates a ctf task from a given dataset using our defaults.

    For use with custom dataset filtering
    """
    return Task(
        dataset=dataset,
        plan=plan or default_agent(max_attempts=max_attempts),
        scorer=scorer or includes(),
        name=name or dataset.name,
    )


@task
def ctf_task(
    challenges: str | list[str] | None = None,
    variants: str | list[str] | None = None,
    metadata_filters: list[str] | None = None,
    max_attempts: int = 3,
    base_directory: str | None = None,
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
    """
    tasks = create_ctf_tasks(
        challenges=challenges,
        variants=variants,
        metadata_filters=metadata_filters,
        max_attempts=max_attempts,
        base_directory=base_directory,
        single_task=True,
    )
    assert len(tasks) == 1, "Should get single task"
    return tasks[0]


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
