from inspect_ai.model import ModelOutput
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox


@solver("qa")
def qa_solver(print_solution_output=True) -> Solver:
    """A solver for doing QA on challenges.

    This solver expects a solution.sh script in the challenge directory.
    It executes it and scores it's output
    """

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        solution_location = state.metadata.get("variant_metadata", {}).get(
            "solution_location", None
        )
        if solution_location is None:  # use relative path
            exec_result = await sandbox().exec(
                ["bash", "-c", "chmod +x *.sh && ./solution.sh"]
            )
        else:
            exec_result = await sandbox().exec(
                [
                    "bash",
                    "-c",
                    f"chmod +x {solution_location}/*.sh && {solution_location}/solution.sh",  # noqa E501
                ]
            )
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
            "dummy", f"```\n{exec_result.stdout}\n{exec_result.stderr}\n```"
        ).message
        if print_solution_output:
            print(formatted_message.content)
        state.messages.append(formatted_message)
        return state

    return solve
