# ctf_evals_core
(currently in early development)

A inspect extension for running ctf evals.

The package provides:

- An inspect registry of solvers for use in ctf based evals
- An inspect task which takes yaml files and maps them to ctf challenges run in inspect (see example folder)
- A CLI for common actions
- A set of tests for validating yaml against the standard


# Usage

## Task running

Install the package and run `inspect eval ctf_evals_core/ctf_task` in any folder with the proper challenge structure (see examples)

If you provide a solution variant and solution.sh script as seen in the examples then running
`inspect eval ctf_evals_core/ctf_task --solver ctf_evals_core/qa -T variants=solution --model openai/gpt-4o` will run that variant with a special solver which runs only that script. Useful for verifying challenge set ups before running actual tests.

## Docker images

The CLI provides commands to manage docker images

`ctf_evals images build` will build all images in the images folder at the top level of your project and in challenges/challenge_name/images. Path is mapped to an image tag you may use in docker compose files. For example
`./images/generic_agent -> ctf-generic_agent:1.0.0`
`./challenges/ctf_01/images/victim -> ctf-ctf_01-victim:1.0.0`
We also include out own kali linux image which we use internally

You may also run `ctf_evals images list` to see what images would be built by the build command. The provided tests verify that challenge image tags are valid

## Tests

Adding the following to your pyproject.toml will ensure the tests from ctf_evals_tests are included.
```
[tool.pytest.ini_options]
addopts = "--pyargs ctf_evals_tests"
```

These tests:
- Verify files described in challenge.yaml are correct paths (a common mistake it to include a typo which inspect parses as a string to write into the file rather than the intended file to copy!). Ignore on a per file basis with `# pathcheck_ignore`
- Verify flags are correctly formatted
- Verify agent image matches our kali linux image
- Verify service images are outputs of the images build command. Ignore on a per image basis with `# imagecheck_ignore`


- README TODO
  - Document standard for challenge definitions
  - Document how to make use of solvers and inspect



