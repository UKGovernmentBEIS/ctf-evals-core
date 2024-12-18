from glob import glob
from pathlib import Path

from ruamel.yaml import YAML


def discover_challenge_task_modules() -> list[Path]:
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


def comment_contains(string: str, comment):
    # Typing for comments seems pretty inconsistent
    # We can check if a comment on a whole list of files contains a string
    # But we can't check just one item unfortunately
    if comment is None:
        return False
    if isinstance(comment, list):
        for item in comment:
            if comment_contains(string, item):
                return True
        return False
    if isinstance(comment, str):
        return string in comment
    try:
        if string in comment.value:
            return True
        return False
    except Exception:
        return False
