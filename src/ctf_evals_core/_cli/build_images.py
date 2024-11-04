import click

from ctf_evals_core._util.docker import build_image, get_images


@click.group(invoke_without_command=True)
def images():
    pass

@click.command(name="build")
def build_images():
    all_images = get_images()
    print(f"Building {len(all_images)} images...")
    print(all_images)
    for context, tag in all_images:
       if not build_image(context, tag):
           return

@click.command(name="list")
def list_images():
    all_images = get_images()
    for _, tag in all_images:
        print(tag)

images.add_command(build_images)
images.add_command(list_images)
