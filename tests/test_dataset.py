from collections import Counter
from pathlib import Path

import mock

from ctf_evals_core.dataset import (
    SANDBOX_PROVIDER_VAR,
    SANDBOX_SPEC_VAR,
    _make_sandbox_resolver,
    create_dataset,
    filter_dataset_by_metadata,
    filter_dataset_by_variant,
)


def test_create_dataset():
    dataset = create_dataset(base_dir="tests/test_tree")
    assert len(dataset) == 4
    assert set([x.id for x in dataset]) == set(
        [
            "hello-world-minimal",
            "hello-world-solution",
            "hello-world2-minimal",
            "hello-world2-solution",
        ]
    )


def test_filter_by_variant():
    dataset = create_dataset(base_dir="tests/test_tree")
    filtered = filter_dataset_by_variant(dataset, {"minimal"})
    assert len(filtered) == 2
    filtered = filter_dataset_by_variant(dataset, set())
    assert len(filtered) == 0


meta = {
    "hello-world": {
        "variant_metadata": {
            "minimal": {"a": 1},
            "solution": {},
        },
        "challenge_metadata": {"a": 2},
    },
    "hello-world2": {
        "variant_metadata": {
            "minimal": {"a": 1},
            "solution": {},
        },
        "challenge_metadata": {"b": 3},
    },
}


def test_filter_by_metadata():
    dataset = create_dataset(base_dir="tests/test_tree")
    # We could write the metadata in the dataset but it makes it harder to
    # parse tests so we'll just add it here.
    # It also lets us parameterize this test later if we want to.
    for sample in dataset:
        assert sample.metadata is not None
        challenge_name = sample.metadata.get("challenge", None)
        variant_name = sample.metadata.get("variant", None)
        sample.metadata["challenge_metadata"] = meta[challenge_name][
            "challenge_metadata"
        ]
        sample.metadata["variant_metadata"] = meta[challenge_name]["variant_metadata"][
            variant_name
        ]
    # Sample metadata overrides challenge metadata so we should see 2 samples
    filtered = filter_dataset_by_metadata(dataset, {"a": 1})
    assert len(filtered) == 2
    # since a is set for 3 / 4 variants. We should see 1 with it not set
    filtered = filter_dataset_by_metadata(dataset, {"a": None})
    assert len(filtered) == 1
    # b is set for challenge so we should see 2 sample
    filtered = filter_dataset_by_metadata(dataset, {"b": 3})
    assert len(filtered) == 2
    # C is never set so we should see 0 samples
    filtered = filter_dataset_by_metadata(dataset, {"c": 4})
    assert len(filtered) == 0
    # C is never set so we should see 4 samples
    filtered = filter_dataset_by_metadata(dataset, {"c": None})
    assert len(filtered) == 4


def test_make_sandbox_spec(monkeypatch):
    # Mock __main__._make_path_absolute to return the same path
    def mock_make_path_absolute(path, base_path: Path):
        print("hit")
        return base_path / path

    monkeypatch.setattr(
        "ctf_evals_core.dataset._make_path_absolute", mock_make_path_absolute
    )

    monkeypatch.setattr(
        "pathlib.Path.is_file", lambda x: True
    )

    # Test docker sandbox provider is default
    resolver = _make_sandbox_resolver()
    spec = resolver(Path("tests/test_tree/1"))
    assert spec is not None
    assert spec[0] == "docker"
    assert str(spec[1]) == "tests/test_tree/1/compose.yaml"

    # test docker provider is set infers compose.yaml
    monkeypatch.setenv(SANDBOX_PROVIDER_VAR, "docker")
    resolver = _make_sandbox_resolver()
    spec = resolver(Path("tests/test_tree/1"))
    assert spec is not None

    # Test atypical sandbox provider
    monkeypatch.setenv(SANDBOX_PROVIDER_VAR, "dummy")

    # No spec file should return single string
    resolver = _make_sandbox_resolver()
    spec = resolver(Path("tests/test_tree/1"))
    assert spec is not None
    assert spec == "dummy"



    monkeypatch.setenv(SANDBOX_SPEC_VAR, "dummy.yaml")
    resolver = _make_sandbox_resolver()

    spec = resolver(Path("tests/test_tree/1"))
    assert spec is not None
    assert spec[0] == "dummy", "Sandbox provider should be dummy"
    assert str(spec[1]) == "tests/test_tree/1/dummy.yaml", "Spec file should be dummy.yaml"

    # If spec file can't be found resolver should return None
    monkeypatch.setattr("pathlib.Path.is_file", lambda x: False)
    assert (
        resolver(Path("tests/test_tree/1")) is None
    ), "If spec file can't be found sandbox resolver should return None"
