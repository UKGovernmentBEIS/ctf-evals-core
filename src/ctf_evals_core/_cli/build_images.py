import click
from rich.console import Console
from rich.table import Table

from ctf_evals_core._util.docker import Registry, get_images


@click.group(invoke_without_command=True, help="Manage docker images, locally and on ECR")
@click.pass_context
def images(ctx: click.Context):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@click.command(name="build", help="Build all docker images")
def build_images():
    all_images = get_images()
    print(f"Building {len(all_images)} images...")
    for image in all_images:
        image.build_image()


@click.command(name="list", help="List all docker images, optionally with ECR details")
@click.option(
    "--challenge_prefix",
    envvar="CTF_EVALS_ECR_CHALLENGE_PREFIX",
    help="The path prefix to add to images specific to the current folder",
)
@click.option(
    "--subdomain",
    envvar="CTF_EVALS_ECR_SUBDOMAIN",
    help="The subdomain in the ECR host in which to place image repoistories",
)
@click.option(
    "--registry_id",
    envvar="CTF_EVALS_ECR_REGISTRY_ID",
    help="The ID of the registry in which to place image repositories",
)
@click.option(
    "--region",
    envvar="CTF_EVALS_ECR_REGION",
    help="The AWS region in which the ECR is located",
)
def list_images(challenge_prefix: str, subdomain: str, registry_id: str, region: str):
    all_images = get_images()
    print(f"Listing {len(all_images)} images...")
    print(challenge_prefix, subdomain, registry_id, region)
    import os
    print(os.environ.get("CTF_EVALS_ECR_CHALLENGE_PREFIX", None))

    table = Table()
    table.add_column("Image name")
    print_ecr_details = (
        challenge_prefix is not None
        and subdomain is not None
        and registry_id is not None
        and region is not None
    )
    if print_ecr_details:
        table.add_column("ECR name")
        table.add_column("Tags")
        registry = Registry(
            registry_id=registry_id,
            subdomain=subdomain,
            challenge_prefix=challenge_prefix,
            region=region,
        )
        registry.login()
        for image in all_images:
            table.add_row(
                image.get_image_name(),
                registry.get_image_repository(image),
                ", ".join(registry.get_image_tags(image)),
            )
    else:
        for image in all_images:
            table.add_row(image.get_image_name())

    console = Console()
    console.print(table)


@click.command(name="push", help="Push all docker images to ECR")
@click.option("--tag", required=True)
@click.option(
    "--challenge_prefix",
    required=True,
    envvar="CTF_EVALS_ECR_CHALLENGE_PREFIX",
    help="The path prefix to add to images specific to the current folder",
)
@click.option(
    "--subdomain",
    required=True,
    envvar="CTF_EVALS_ECR_SUBDOMAIN",
    help="The subdomain in the ECR host in which to place image repoistories",
)
@click.option(
    "--registry_id",
    required=True,
    envvar="CTF_EVALS_ECR_REGISTRY_ID",
    help="The ID of the registry in which to place image repositories",
)
@click.option(
    "--region",
    required=True,
    envvar="CTF_EVALS_ECR_REGION",
    help="The AWS region in which the ECR is located",
)
def push_images(
    tag: str, challenge_prefix: str, subdomain: str, registry_id: str, region: str
):
    registry = Registry(
        registry_id=registry_id,
        subdomain=subdomain,
        challenge_prefix=challenge_prefix,
        region=region,
    )
    registry.login()
    all_images = get_images()
    for image in all_images:
        try:
            registry.push_image(image, tag)
        except ValueError as e:
            print(f"Failed to push {registry.get_full_image_name(image)}")
            print(e)
            input("Press enter to continue or consider increasing the tag version")


@click.command(name="push_one", help="Push a single docker image to ECR")
@click.option("--tag", required=True)
@click.option("--image", required=True)
@click.option(
    "--challenge_prefix",
    required=True,
    envvar="CTF_EVALS_ECR_CHALLENGE_PREFIX",
    help="The path prefix to add to images specific to the current folder",
)
@click.option(
    "--subdomain",
    required=True,
    envvar="CTF_EVALS_ECR_SUBDOMAIN",
    help="The subdomain in the ECR host in which to place image repoistories",
)
@click.option(
    "--registry_id",
    required=True,
    envvar="CTF_EVALS_ECR_REGISTRY_ID",
    help="The ID of the registry in which to place image repositories",
)
@click.option(
    "--region",
    required=True,
    envvar="CTF_EVALS_ECR_REGION",
    help="The AWS region in which the ECR is located",
)
def push_image(
    tag: str,
    image: str,
    challenge_prefix: str,
    subdomain: str,
    registry_id: str,
    region: str,
):
    registry = Registry(
        registry_id=registry_id,
        subdomain=subdomain,
        challenge_prefix=challenge_prefix,
        region=region,
    )
    registry.login()
    all_images = get_images()
    matching_images = [i for i in all_images if image in i.get_image_name()]
    for image in matching_images:
        confirmed = input(f"Pushing {registry.get_full_image_name(image)} confirm y/n")
        if confirmed == "y":
            registry.push_image(image, tag)


@click.command(
    name="search",
    help="Search for images by substring in name, useful for checking docker compose is configured correctly", # noqa
)
@click.option("--image", required=True)
@click.option(
    "--challenge_prefix",
    required=True,
    envvar="CTF_EVALS_ECR_CHALLENGE_PREFIX",
    help="The path prefix to add to images specific to the current folder",
)
@click.option(
    "--subdomain",
    required=True,
    envvar="CTF_EVALS_ECR_SUBDOMAIN",
    help="The subdomain in the ECR host in which to place image repoistories",
)
@click.option(
    "--registry_id",
    required=True,
    envvar="CTF_EVALS_ECR_REGISTRY_ID",
    help="The ID of the registry in which to place image repositories",
)
@click.option(
    "--region",
    required=True,
    envvar="CTF_EVALS_ECR_REGION",
    help="The AWS region in which the ECR is located",
)
def search_images(
    image: str, challenge_prefix: str, subdomain: str, registry_id: str, region: str
):
    registry = Registry(
        registry_id=registry_id,
        subdomain=subdomain,
        challenge_prefix=challenge_prefix,
        region=region,
    )
    all_images = get_images()
    filtered = [i for i in all_images if image in i.get_image_name()]
    for image in filtered:
        print(registry.get_full_image_name(image))


images.add_command(build_images)
images.add_command(list_images)
images.add_command(push_images)
images.add_command(push_image)
images.add_command(search_images)
