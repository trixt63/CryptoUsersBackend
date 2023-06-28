import click

from config import Config
from tests.performance.api_latency import api_latency


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-b', '--base-url', default=Config.API_HOST, show_default=True, type=str, help='API base url')
def api_performance(base_url):
    api_latency(base_url)
