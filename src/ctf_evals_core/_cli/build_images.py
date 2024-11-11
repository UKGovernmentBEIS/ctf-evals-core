import click
from rich.console import Console
from rich.table import Table

from ctf_evals_core._util.docker import get_images, Registry


@click.group(invoke_without_command=True)
def images():
    pass


@click.command(name="build")
def build_images():
    all_images = get_images()
    print(f"Building {len(all_images)} images...")
    for image in all_images:
        image.build_image()


@click.command(name="list")
@click.option("--subdomain", required=False)
@click.option("--registry_id", required=False)
@click.option("--region", required=False)
def list_images(subdomain: str, registry_id: str, region: str):
    all_images = get_images()

    table = Table()
    table.add_column("Image name")
    print_ecr_details = (
        subdomain is not None and registry_id is not None and region is not None
    )
    if print_ecr_details:
        table.add_column("ECR name")
        table.add_column("Tags")
        registry = Registry(
            registry_id=registry_id,
            challenge_prefix=subdomain,
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


@click.command(name="push")
@click.option("--tag", required=True)
@click.option("--subdomain", required=True)
@click.option("--registry_id", required=True)
@click.option("--region", required=True)
def push_images(tag: str, subdomain: str, registry_id: str, region: str):
    registry = Registry(
        registry_id=registry_id,
        challenge_prefix=subdomain,
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


@click.command(name="push_one")
@click.option("--tag", required=True)
@click.option("--image", required=True)
@click.option("--subdomain", required=True)
@click.option("--registry_id", required=True)
@click.option("--region", required=True)
def push_image(tag: str, image: str, subdomain: str, registry_id: str, region: str):
    registry = Registry(
        registry_id=registry_id,
        challenge_prefix=subdomain,
        region=region,
    )
    registry.login()
    all_images = get_images()
    matching_images = [i for i in all_images if image in i.get_image_name()]
    for image in matching_images:
        confirmed = input(f"Pushing {registry.get_full_image_name(image)} confirm y/n")
        if confirmed == "y":
            registry.push_image(image, tag)


@click.command(name="search")
@click.option("--image", required=True)
@click.option("--subdomain", required=True)
@click.option("--registry_id", required=True)
@click.option("--region", required=True)
def search_images(image: str, subdomain: str, registry_id: str, region: str):
    registry = Registry(
        registry_id=registry_id,
        challenge_prefix=subdomain,
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
