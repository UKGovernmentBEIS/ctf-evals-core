# ctf_evals_core
(currently in early development)

A inspect extension for running ctf evals.

The package provides:

- An inspect registry of solvers for use in ctf based evals
- An inspect task which takes yaml files and maps them to ctf challenges run in inspect (see example folder)
- A CLI for common actions
- A set of tests for validating yaml against the standard


# Usage

## Setup

Create folder with the following structure
```
my_ctf_challenge_directory/
    images/
    challenges/
        challenge1/
            challenge.yaml
            compose.yaml
            resources/
            images/
                victim/
                    Dockerfile
                    startup.sh
        challenge2/
        challenge3/
    pyproject.yaml
```

Install ctf_evals_core. We recommend using a virtual environment and dependency management library like poetry

```
poetry install git+https://github.com/UKGovernmentBEIS/ctf-evals-core.git
```

## Task running

Run `inspect eval ctf_evals_core/ctf_task` at the top level of your project.

Inspect allows you to pass parameters to your tasks with the -T flag. ctf_task has the following parameters
- base_directory: The default challenge directory to use to discover challenges. If None, the current working directory / "challenges" is used.
    You should only need to use this if your structure is more complicated than the example provided
- challenges: The path to the challenge directory or a list of challenge directories to load. Relative paths are resolved relative to the base directory. If None, all challenges are loaded.
- variants: The variant or list of variants to include (e.g. "easy" or "easy,hard"). If None, all variants are included.
- metadata_filters: A list of metadata filters to apply to the challenges. e.g `metadata_filters=split=prod,category=web_exploitation` metadata can be set in challene.yaml per variant or per challenge (variant overrides challenge)
- max_attempts: The maximum number of submission attempts before terminating. This argument is used by our default agent and is ignored if the solver argument in inspect is set

We provide a solver called qa which simply tries to run a file called solution.sh in the sandbox. A good default for quality assurance is to provide one special variant called solution which copies a solution.sh file (and any other necessary files) that reliably and automatically solves the challenge. Then you may run those variants with the qa solver like follows 
```
inspect eval ctf_evals_core/ctf_task --solver ctf_evals_core/qa -T variants=solution --model openai/gpt-4o
``` 
if the score on the task is not 1.0 you may want to investigate

## Docker images

The CLI provides commands to manage docker images

`ctf_evals images build` will build all images in the images folder at the top level of your project and in challenges/challenge_name/images. Path is mapped to an image tag you may use in docker compose files. For example
`./images/generic_agent -> ctf-generic_agent:1.0.0`
`./challenges/ctf_01/images/victim -> ctf-ctf_01-victim:1.0.0`
We also include out own kali linux image which we use internally it will be mapped to:
`ctf-agent-environment:1.0.0`


`ctf_evals images push` will push images to an ECR registry given the provided arguments/environment variables

You may also run `ctf_evals images list` to see what images would be built by the build command. If you provide arguments specifying your ECR registry it will show how images will be pushed to ECR

## Tests

Adding the following to your pyproject.toml will ensure the tests from ctf_evals_tests are included.
```
[tool.pytest.ini_options]
addopts = "--pyargs ctf_evals_tests"
```

These tests:
- Verify files described in challenge.yaml are correct paths (a common mistake it to include a typo which inspect parses as a string to write into the file rather than the intended file to copy!). Ignore on a per file basis with `# pathcheck_ignore`
- Verify that docker images listed in compose.yaml would all be discovered by the cli images build command
- Verify flags are correctly formatted
- Verify agent image matches our kali linux image


# Advanced

## Configuring sandbox environments

Inspect provides a default docker sandbox provider and ctf_evals will use docker by default looking for a docker compose file next to your challenge.yaml file for each challenge. If you have an alternative sandbox provider you would like to use you may set the following environment varables

- CTF_SANDBOX_PROVIDER the name of the provider as given to inspect. For example to use the (podman example)[https://inspect.ai-safety-institute.org.uk/extensions.html#sec-sandbox-environment-extensions] from the inspect docs you would use "podman"
- CTF_SANDBOX_SPEC_FILE the name of the configuration file for the environment relative to each challenge.yaml files. For docker this is implicitly `compose.yaml` for the podman example this would be `config.yaml`
