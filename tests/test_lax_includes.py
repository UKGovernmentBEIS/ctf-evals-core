from inspect_ai.model import ModelOutput
import pytest
from inspect_ai.scorer import Target
from inspect_ai.solver import TaskState

from ctf_evals_core._scorers.lax_includes import lax_includes


def make_dummy_task_state(submission, flag_format_hint):
    """Make task state which lax_includes expects."""
    return TaskState(
        model="openai/o1",
        sample_id="",
        input="",
        epoch=1,
        messages=[],
        output=ModelOutput.from_content("dummy", submission),
        metadata={"flag_format_hint": flag_format_hint},
    )


async def score_lax_includes(input, target, flag_format_hint):
    state = make_dummy_task_state(input, flag_format_hint)
    scorer = lax_includes()
    score = await scorer(state, Target(target))
    return score


@pytest.mark.parametrize(
    "answer,target,flag_format,score,message",
    [
        (
            "ctf{flag}",
            "ctf{flag}",
            "ctf{...}",
            "C",
            "Equal flag and submission should pass",
        ),
        ("flag", "ctf{flag}", "ctf{...}", "C", "Stripped flag should pass"),
        (
            "preamble text flag",
            "ctf{flag}",
            "ctf{...}",
            "C",
            "Reasoning + stripped flag should pass",
        ),
        (
            "preamble text ctf{flag}",
            "ctf{flag}",
            "ctf{...}",
            "C",
            "Reasoning + flag should pass",
        ),
        (
            "lag",
            "ctf{flag}",
            "ctf{...}",
            "I",
            "Subset of flag should fail",
        ),
        (
            "f   lag",
            "ctf{flag}",
            "ctf{...}",
            "I",
            "Fuzzy match should fail",
        ),
        (
            "(flag)",
            "ctf{(flag)}",
            "ctf{...}",
            "C",
            "Regex should strip only outer flag formatting",
        ),
    ],
)
@pytest.mark.asyncio
async def test_lax_includes(answer, target, flag_format, score, message):
    scored = await score_lax_includes(answer, target, flag_format)
    print(scored)
    assert scored.text == score, message
