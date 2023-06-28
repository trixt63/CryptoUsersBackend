import click

from cli.api.jwt import generate_jwt_cli
from cli.api.performance import api_performance


@click.group()
@click.version_option(version='1.6.3')
@click.pass_context
def cli(ctx):
    """Doesn't use, so pass"""
    pass


cli.add_command(generate_jwt_cli, "generate_jwt")
cli.add_command(api_performance, "performance")
