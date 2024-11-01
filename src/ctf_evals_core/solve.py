from inspect_ai import Task
from inspect_ai.model import ModelOutput
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox

from .task import make_ctf_task


def make_solver_task(
    challenges: str | list[str] | None = None,
    max_attempts: int = 3,
    max_messages: int = 15,
    default_challenge_dir: str | None = None,
) -> Task:
    task = make_ctf_task(
            challenges=challenges,
            variants="solution",
            agent=qa_solver(),
            max_attempts=max_attempts,
            max_messages=max_messages,
            default_challenge_dir=default_challenge_dir,
        )
    return task


@solver("qa_solver")
def qa_solver() -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        exec_result = await sandbox().exec(["chmod", "+x", "solution.sh"])
        exec_result = await sandbox().exec(["bash", "solution.sh"])
        if exec_result.returncode != 0:
            state.output = ModelOutput.from_content(
                "error",
                f"""Failed to execute the solution.
                stdout:{exec_result.stdout}
                stderr{exec_result.stderr}""",
            )
            state.messages.append(state.output.message)
            return state
        state.output = ModelOutput.from_content("dummy", exec_result.stdout)
        formatted_message = ModelOutput.from_content(
            "dummy", f"```\n{exec_result.stdout}\n```"
        ).message
        print(exec_result.stdout)
        state.messages.append(formatted_message)
        return state

    return solve
