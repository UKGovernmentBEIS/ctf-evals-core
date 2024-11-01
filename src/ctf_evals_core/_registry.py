# from .solve import qa_solver # noqa imported to expose to inspect
from inspect_ai.model import ModelOutput
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox


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
