import subprocess

from inspect_ai import eval
from inspect_ctf import ctf

# Create a task for the CTF challenge(s)
# all = ctf(".")
examples_1 = ctf("cybench", challenges="challenge_name", metadata="prof", variants="maximal")
examples_2 = ctf("gray_swan", challenges="challenge_name", metadata="prod", variants="maximal")
# task = ctf()
# print(task.dataset.samples)

eval_set(examples_1, examples_2)

# subprocess.run(["inspect", "eval", str(task), "--model", "openai/gpt-4o"])
eval(task, model="openai/gpt-4o", epochs=2)





# log file per challenge
create_ctf(single_task=False)





build_images()


cybench = ctf("cybench", challenges="challenge_name", metadata="prof", variants="maximal", single_task=True)
OR
inspect eval inspect_ctf/ctf --model openai/gpt-4o -T root_dir=cybench


create_eval_set(cybench, gray_swan)

