import click

from app.constants.time_constants import TimeConstants
from app.services.auth_service import generate_jwt
from config import Config


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-w', '--wallet', default=None, show_default=True, type=str, help='Wallet address')
@click.option('-r', '--role', default=None, show_default=True, type=str, help='Role')
@click.option('-e', '--expire', default=None, show_default=True, type=int, help='Time to expire')
def generate_jwt_cli(wallet, role, expire):
    """Generate jwt for authorize api. """

    if (not wallet) and (not role):
        wallet = '0x'
        role = 'admin'
    elif not role:
        role = 'user'
    elif not wallet:
        wallet = '0x'

    if expire is None:
        expire = TimeConstants.DAYS_30

    token = generate_jwt(wallet.lower(), role, Config.SECRET, expire)
    print(token)
