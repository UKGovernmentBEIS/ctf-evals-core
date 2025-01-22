from ctf_evals_core.task import create_ctf_tasks
from inspect_ai import eval_set

challenges = ""
variants = "solution"
single_task = False

tasks = create_ctf_tasks(
    challenges=challenges, variants=variants, single_task=single_task
)
eval_set(tasks, log_dir="logs", model="openai/gpt-4o", max_tasks=5)
