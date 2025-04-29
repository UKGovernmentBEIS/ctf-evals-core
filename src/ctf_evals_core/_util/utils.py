from typing import Any


def get_from_metadata[T](
    metadata: dict[str, Any] | None,
    key: str,
    default: T = None,  # type: ignore
) -> T | Any:
    # mypy wants default to be T | None because of no implicit optional but if so
    # people who call get_from_metadata with a default variable set get a value of
    # type T | None which is not correct
    """
    Get a value from metadata, with a default value if it doesn't exist.

    For a ctf task it will first look in the variant_metadata, then the
    challenge_metadata, then the metadata.

    Args:
        metadata: The metadata dictionary.
        key: The key to get.
        default: The default value to return if the key doesn't exist.
    """
    assert metadata is not None, "Inspect metadata should never be None"

    if "variant_metadata" in metadata and key in metadata["variant_metadata"]:
        result = metadata["variant_metadata"][key]
    elif "challenge_metadata" in metadata and key in metadata["challenge_metadata"]:
        result = metadata["challenge_metadata"][key]
    elif key in metadata:
        result = metadata[key]
    else:
        result = default
    return result
