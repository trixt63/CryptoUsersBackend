import requests
from pycoingecko import CoinGeckoAPI

from app.constants.network_constants import ChainsAnkr
from app.decorators.time_exe import sync_log_time_exe, TimeExeTag
from app.utils.logger_utils import get_logger

logger = get_logger("Market service")


class MarketService:
    def __init__(self):
        self.coingecko = CoinGeckoAPI()
        self.coingecko.request_timeout = 30

        self.currency = 'usd'

    def get_all_coin_ids(self):
        coins_list = self.coingecko.get_coins_list()
        all_coin_ids = [coin.get('id') for coin in coins_list]
        return all_coin_ids

    def get_token_info(self, coin_id):
        try:
            coin_info = self.coingecko.get_coin_by_id(
                id=coin_id, localization=False, tickers=False, market_data=True,
                community_data=True, developer_data=False, sparkline=False
            )

            links = coin_info.get('links', {})
            chat_info = links.get('chat_url', [])
            socials = {}
            for chat_link in chat_info:
                if not chat_link:
                    continue
                elif 'discord.com' in chat_link:
                    socials['discord'] = chat_link
                elif 't.me' in chat_link:
                    socials['telegram'] = chat_link

            reddit_url = links.get('subreddit_url')
            if reddit_url:
                socials['reddit'] = reddit_url

            if links.get('twitter_screen_name'):
                twitter_url = f'https://twitter.com/{links["twitter_screen_name"]}'
                socials['twitter'] = twitter_url

            repo_info = links.get('repos_url', {})
            github_links = repo_info.get('github', [])
            github = None
            if github_links:
                paths = github_links[0].split("/")
                github = '/'.join(paths[:4])

            return {
                'socialNetworks': socials,
                'sourceCode': github
            }
        except Exception as ex:
            logger.exception(ex)
        return {}

    def get_holders(self, coin_address, chain_id, limit=20):
        """Get number of holders of coin, using Ankr API"""
        url = 'https://rpc.ankr.com/multichain'
        header = {'Content-Type': 'application/json'}
        params = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "ankr_getTokenHolders",
            "params": {
                "blockchain": ChainsAnkr.get_chain_name(chain_id),
                "contractAddress": coin_address,
                "pageSize": limit,
                "pageToken": ""
            }
        }

        response = requests.post(url=url, headers=header, json=params)
        try:
            data = response.json()
            holders = data['result']['holders']
            return holders
        except Exception as ex:
            logger.warning(f"Ankr can't get info of coin {coin_address} on {chain_id}: {ex}.")
        return None

    @sync_log_time_exe(tag=TimeExeTag.request)
    def get_token_exchanges(self, coin_id):
        try:
            tickers_info = self.coingecko.get_coin_ticker_by_id(id=coin_id, order='volume_desc')
            tickers = tickers_info['tickers']

            exchanges = []
            for ticker in tickers:
                market_info = ticker['market']
                exchanges.append({
                    'name': market_info['name'],
                    'id': market_info['identifier'],
                    'base': ticker['base'],
                    'target': ticker['target'],
                    'price': ticker['converted_last']['usd'],
                    'tradingVolume': ticker['converted_volume']['usd']
                })
            return exchanges
        except Exception as ex:
            logger.exception(ex)
        return []
