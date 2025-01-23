from ctf_evals_core.task import create_ctf_tasks
from inspect_ai import eval_set

challenges = ""
variants = ["solution", "minimal"]
metadata_filters = None
# metadata_filters=["filter_var=True"] # should only get the hello world task
single_task = False

tasks = create_ctf_tasks(
    challenges=challenges,
    variants=variants,
    single_task=single_task,
    metadata_filters=metadata_filters,
)
eval_set(tasks, log_dir="logs", model="openai/gpt-4o", max_tasks=5)
