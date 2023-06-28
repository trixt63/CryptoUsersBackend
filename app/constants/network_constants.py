class NetworkType:
    BSC = 'bsc'
    ETH = 'ethereum'
    FTM = 'ftm'
    POLYGON = 'polygon'


class Chain:
    BSC = '0x38'
    ETH = '0x1'
    FTM = '0xfa'
    POLYGON = '0x89'

    mapping = {
        NetworkType.BSC: BSC,
        NetworkType.ETH: ETH,
        NetworkType.FTM: FTM,
        NetworkType.POLYGON: POLYGON
    }

    chain_names = {
        BSC: 'BSC',
        ETH: 'Ethereum',
        FTM: 'Fantom',
        POLYGON: 'Polygon'
    }

    explorers = {
        BSC: 'https://bscscan.com/',
        ETH: 'https://etherscan.io/',
        FTM: 'https://ftmscan.com/',
        POLYGON: 'https://polygonscan.com/'

    }

    estimate_block_time = {
        BSC: 3,
        ETH: 12,
        FTM: 1,
        POLYGON: 2
    }

    def get_all_chain_id(self):
        return [self.BSC, self.ETH, self.FTM, self.POLYGON]


class ChainsAnkr:
    """Chain name for Ankr API"""
    arbitrum = '0xa4b1'
    avalanche = '0xa86a'
    bsc = '0x38'
    eth = '0x1'
    fantom = '0xfa'
    polygon = '0x89'
    syscoin = '0x57'
    optimism = '0xa'

    reversed_mapping = {
        bsc: 'bsc',
        eth: 'eth',
        fantom: 'fantom',
        polygon: 'polygon',
        avalanche: 'avalanche'
    }

    @staticmethod
    def get_chain_name(chain_id):
        return ChainsAnkr.reversed_mapping.get(chain_id)


class ProviderURI:
    bsc_provider_uri = 'https://rpc.ankr.com/bsc'
    eth_provider_uri = 'https://rpc.ankr.com/eth'
    ftm_provider_uri = 'https://rpc.ankr.com/fantom'
    polygon_provider_uri = 'https://rpc.ankr.com/polygon'

    # bsc_provider_uri = os.getenv('BSC_PROVIDER_ARCHIVE')
    # eth_provider_uri = os.getenv('ETHEREUM_PROVIDER_ARCHIVE')
    # ftm_provider_uri = os.getenv('FTM_PROVIDER_ARCHIVE')

    mapping = {
        Chain.BSC: bsc_provider_uri,
        Chain.ETH: eth_provider_uri,
        Chain.FTM: ftm_provider_uri,
        Chain.POLYGON: polygon_provider_uri
    }


DEFAULT_CREDIT_SCORE = 105

BNB = '0x0000000000000000000000000000000000000000'
WBNB = '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'

EMPTY_TOKEN_IMG = 'https://firebasestorage.googleapis.com/v0/b/token-c515a.appspot.com/o/tokens_v2%2Fempty-token.png?alt=media&token=2f9dfcc1-88a0-472c-a51f-4babc0c583f0'

WRAPPED_NATIVE_TOKENS = {
    Chain.BSC: '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c',
    Chain.ETH: '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
    Chain.FTM: '0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83',
    Chain.POLYGON: '0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270'
}
