# Provide a script to run common tasks needed to run ctf_evals
import click
from dotenv import load_dotenv

from .build_images import images

load_dotenv(".env")


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(images)


def main():
    cli()
