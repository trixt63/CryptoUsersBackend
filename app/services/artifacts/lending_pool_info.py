from app.services.artifacts.abis.chainlink_abi import CHAINLINK_ABI
from app.services.artifacts.abis.lending_pools.aave_v2_lending_pool_abi import LENDING_POOL_AAVE_V2_ABI
from app.services.artifacts.abis.lending_pools.compound_abis.compound_comptroller_abi import \
    COMPOUND_COMPTROLLER_ABI
from app.services.artifacts.abis.lending_pools.compound_abis.compound_lens import COMPOUND_LENS_ABI
from app.services.artifacts.abis.lending_pools.compound_abis.cream_lens import CREAM_LENS_ABI
from app.services.artifacts.abis.lending_pools.geist.multi_fee_distribution import MULTI_FEE_DISTRIBUTION
from app.services.artifacts.abis.lending_pools.trava_pool.trava_lending_pool_abi import TRAVA_LENDING_POOL_ABI
from app.services.artifacts.abis.lending_pools.venus_abis.comptroller_venus_abi import COMPTROLLER_ABI
from app.services.artifacts.abis.lending_pools.venus_abis.venus_lens import VENUS_LENS
from app.services.artifacts.abis.lending_pools.geist.lending_pool_abi import \
    LENDING_POOL_ABI as GEIST_LENDING_POOL_ABI
from app.services.artifacts.abis.lending_pools.geist.oracle_abi import ORACLE_ABI as GEIST_ORACLE_ABI
from app.services.artifacts.abis.lending_pools.geist.aave_protocol_data_provider import \
    AAVE_PROTOCOL_DATA_PROVIDER
from app.services.artifacts.abis.lending_pools.geist.chef_incentives_controller import CHEF_INCENTIVES_CONTROLLER
from app.constants.contract_constants import ContractConst


class LendingFork:
    AAVE_POOL = 'aave_pool'
    GEIST_POOL = 'geist_pool'
    ALPACA_POOL = 'alpaca_pool'
    COMPTROLLER_POOL = 'comptroller_pool'


class LendingPoolInfo:
    ftm = {
        "0x9fad24f572045c7869117160a571b2e50b10d068": {
            ContractConst.lending_address: "0x9fad24f572045c7869117160a571b2e50b10d068",
            ContractConst.oracle_address: "0xc466e3fee82c6bdc2e17f2eaf2c6f1e91ad10fd3",
            ContractConst.chef_incentive_address: "0x297fddc5c33ef988dd03bd13e162ae084ea1fe57",
            ContractConst.protocol_data_address: "0xf3b0611e2e4d2cd6ab4bb3e01ade211c3f42a8c3",
            ContractConst.multi_fee_address: "0x49c93a95dbcc9a6a4d8f77e59c038ce5020e82f8",
            ContractConst.coin_base_address: "0xd8321aa83fb0a4ecd6348d4577431310a6e0814d",
            ContractConst.name: "geist-ftm",
            ContractConst.chain_id: "0xfa",
            ContractConst.chain_name: "ftm",
            ContractConst.decimals: 18,
            ContractConst.lending_fork: LendingFork.GEIST_POOL,
            ContractConst.multi_fee_abi: MULTI_FEE_DISTRIBUTION,
            ContractConst.lending_abi: GEIST_LENDING_POOL_ABI,
            ContractConst.oracle_abi: GEIST_ORACLE_ABI,
            ContractConst.protocol_data_abi: AAVE_PROTOCOL_DATA_PROVIDER,
            ContractConst.chef_incentive_abi: CHEF_INCENTIVES_CONTROLLER,
            ContractConst.img_url: "https://firebasestorage.googleapis.com/v0/b/token-c515a.appspot.com/o/tokens_v2%2FGEIST.png?alt=media&token=14dd349a-d7b5-49cf-82d2-fcff0967e21b"
        },
        '0xd98bb590bdfabf18c164056c185fbb6be5ee643f': {
            ContractConst.name: 'trava-ftm',
            ContractConst.chain_name: 'ftm',
            ContractConst.decimals: 8,
            ContractConst.lending_address: '0xd98bb590bdfabf18c164056c185fbb6be5ee643f',
            ContractConst.chain_id: "0xfa",
            ContractConst.lending_fork: LendingFork.AAVE_POOL,
            ContractConst.lending_abi: TRAVA_LENDING_POOL_ABI,
            ContractConst.staked_token: '0x1ddec3377347cba814027fbf13a86b6000f201fb',
            ContractConst.staked_incentive_address: '0x9660f97f5a4898a0b0abb4369e925131734c9c0d',
            ContractConst.oracle_address: '0x290346e682d51b97e2c1f186eb61eb49881c5ec7',
            ContractConst.img_url: "https://firebasestorage.googleapis.com/v0/b/token-c515a.appspot.com/o/tokens_v2%2FTRAVA.png?alt=media&token=8ca92414-92e8-4df9-8d52-3730d039e25a"
        },
    }
    eth = {
        '0xd61afaaa8a69ba541bc4db9c9b40d4142b43b9a4': {
            ContractConst.name: 'trava-eth',
            ContractConst.chain_name: 'eth',
            ContractConst.decimals: 8,
            ContractConst.lending_address: '0xd61afaaa8a69ba541bc4db9c9b40d4142b43b9a4',
            ContractConst.chain_id: "0x1",
            ContractConst.lending_fork: LendingFork.AAVE_POOL,
            ContractConst.lending_abi: TRAVA_LENDING_POOL_ABI,
            ContractConst.staked_token: '0x044ede67afdb0f56d7451bb3aaccaeab3f772fad',
            ContractConst.staked_incentive_address: '0x43cf9fb8cf26e46890d6e3a4e6494a843bbb6615',
            ContractConst.oracle_address: '0x2bd81260fe864173b6ec1ec9ee41a76366922565',
            ContractConst.img_url: "https://firebasestorage.googleapis.com/v0/b/token-c515a.appspot.com/o/tokens_v2%2FTRAVA.png?alt=media&token=8ca92414-92e8-4df9-8d52-3730d039e25a"
        },
        "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9": {
            ContractConst.name: 'aave-v2-eth',
            ContractConst.chain_name: 'eth',
            ContractConst.decimals: 8,
            ContractConst.lending_address: '0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9',
            ContractConst.chain_id: "0x1",
            ContractConst.lending_fork: LendingFork.AAVE_POOL,
            ContractConst.lending_abi: LENDING_POOL_AAVE_V2_ABI,
            ContractConst.oracle_address: '0xa50ba011c48153de246e5192c8f9258a2ba79ca9',
            ContractConst.img_url: "https://firebasestorage.googleapis.com/v0/b/token-c515a.appspot.com/o/tokens_v2%2FAAVE.png?alt=media&token=8920bc32-efff-4973-9774-9bf3973d9945"
        },
        "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b": {
            ContractConst.decimals: 18,
            ContractConst.comptroller_address: "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b",
            ContractConst.comptroller_implementation_address: "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b",
            ContractConst.chainlink_address: "0xdbd020caef83efd542f4de03e3cf0c28a4428bd5",
            ContractConst.lending_address: "0xdcbdb7306c6ff46f77b349188dc18ced9df30299",
            ContractConst.lending_abi: COMPOUND_LENS_ABI,
            ContractConst.comptroller_abi: COMPOUND_COMPTROLLER_ABI,
            ContractConst.chain_link_abi: CHAINLINK_ABI,
            ContractConst.speed_function: "compSpeeds",
            ContractConst.metadata_tokens: "cTokenMetadataAll",
            ContractConst.name: "compound-eth",
            ContractConst.chain_id: "0x1",
            ContractConst.chain_name: "ethereum",
            ContractConst.lending_fork: LendingFork.COMPTROLLER_POOL,
            ContractConst.token: "0xc00e94cb662c3520282e6f5717214004a7f26888",
            ContractConst.img_url: "https://firebasestorage.googleapis.com/v0/b/token-c515a.appspot.com/o/tokens_v2%2FCOMP.png?alt=media&token=dede54fd-c2ad-4082-a6b0-b63588b429a5"
        }
    }
    bsc = {
        "0xfd36e2c2a6789db23113685031d7f16329158384": {
            ContractConst.decimals: 18,
            # ContractConst.new_comptroller_address: "0xfd36e2c2a6789db23113685031d7f16329158384",
            ContractConst.comptroller_address: "0xfd36e2c2a6789db23113685031d7f16329158384",
            ContractConst.comptroller_implementation_address: "0xf6c14d4dfe45c132822ce28c646753c54994e59c",
            ContractConst.chainlink_address: "0xbf63f430a79d4036a5900c19818aff1fa710f206",
            ContractConst.lending_address: "0xcda4a4ab96dfc1728ee265b9392373db40e769f2",
            ContractConst.lending_abi: VENUS_LENS,
            ContractConst.comptroller_abi: COMPTROLLER_ABI,
            ContractConst.chain_link_abi: CHAINLINK_ABI,
            ContractConst.speed_function: "venusSpeeds",
            ContractConst.metadata_tokens: "vTokenMetadataAll",
            ContractConst.name: "venus-bsc",
            ContractConst.chain_id: "0x38",
            ContractConst.chain_name: "bsc",
            ContractConst.lending_fork: LendingFork.COMPTROLLER_POOL,
            ContractConst.token: "0xcf6bb5389c92bdda8a3747ddb454cb7a64626c63",
            ContractConst.img_url: "https://firebasestorage.googleapis.com/v0/b/token-c515a.appspot.com/o/tokens_v2%2FXVS.png?alt=media&token=4be10a0c-3396-4a13-a67d-1b840e2240a7"
        },
        "0x589de0f0ccf905477646599bb3e5c622c84cc0ba": {
            ContractConst.decimals: 18,
            ContractConst.comptroller_address: "0x589de0f0ccf905477646599bb3e5c622c84cc0ba",
            ContractConst.comptroller_implementation_address: "0x49a08f9f445af5734cf15a1deab3b1c6a7988fb4",
            ContractConst.chainlink_address: "0xa12fc27a873cf114e6d8bbaf8bd9b8ac56110b39",
            ContractConst.lending_abi: CREAM_LENS_ABI,
            ContractConst.comptroller_abi: COMPOUND_COMPTROLLER_ABI,
            ContractConst.chain_link_abi: CHAINLINK_ABI,
            ContractConst.speed_function: "compSpeeds",
            ContractConst.metadata_tokens: "cTokenMetadataAll",
            ContractConst.name: "cream-bsc",
            ContractConst.chain_id: "0x38",
            ContractConst.chain_name: "bsc",
            ContractConst.lending_fork: LendingFork.COMPTROLLER_POOL,
            ContractConst.lending_address: "0x1a014ffe0cd187a298a7e79ba5ab05538686ea4a",
            ContractConst.token: "0xd4cb328a82bdf5f03eb737f37fa6b370aef3e888",
            ContractConst.img_url: "https://firebasestorage.googleapis.com/v0/b/token-c515a.appspot.com/o/tokens_v2%2FCREAM.png?alt=media&token=9842d618-5a05-430d-b549-6df09585fc4b"
        },
        "0xe29a55a6aeff5c8b1beede5bcf2f0cb3af8f91f5": {
            ContractConst.lending_address: "0xe29a55a6aeff5c8b1beede5bcf2f0cb3af8f91f5",
            ContractConst.oracle_address: "0x3436c4b4a27b793539844090e271591cbcb0303c",
            ContractConst.chef_incentive_address: "0xb7c1d99069a4eb582fc04e7e1124794000e7ecbf",
            ContractConst.protocol_data_address: "0xc9704604e18982007fdea348e8ddc7cc652e34ca",
            ContractConst.multi_fee_address: "0x685d3b02b9b0f044a3c01dbb95408fc2eb15a3b3",
            ContractConst.coin_base_address: "0xb1ebdd56729940089ecc3ad0bbeeb12b6842ea6f",
            ContractConst.name: "valas-bsc",
            ContractConst.chain_id: "0x38",
            ContractConst.chain_name: "bsc",
            ContractConst.lending_fork: LendingFork.GEIST_POOL,
            ContractConst.decimals: 18,
            ContractConst.multi_fee_abi: MULTI_FEE_DISTRIBUTION,
            ContractConst.lending_abi: GEIST_LENDING_POOL_ABI,
            ContractConst.oracle_abi: GEIST_ORACLE_ABI,
            ContractConst.protocol_data_abi: AAVE_PROTOCOL_DATA_PROVIDER,
            ContractConst.chef_incentive_abi: CHEF_INCENTIVES_CONTROLLER,
            ContractConst.img_url: "https://firebasestorage.googleapis.com/v0/b/token-c515a.appspot.com/o/tokens_v2%2FVALAS.png?alt=media&token=8f745486-e1eb-41a2-9b95-dc6c3558fca7"
        },
        '0x75de5f7c91a89c16714017c7443eca20c7a8c295': {
            ContractConst.name: 'trava-bsc',
            ContractConst.chain_name: 'bsc',
            ContractConst.lending_fork: LendingFork.AAVE_POOL,
            ContractConst.lending_abi: TRAVA_LENDING_POOL_ABI,
            ContractConst.decimals: 8,
            ContractConst.lending_address: '0x75de5f7c91a89c16714017c7443eca20c7a8c295',
            ContractConst.chain_id: "0x38",
            ContractConst.oracle_address: '0x7cd53b71bf56cc6c9c9b43719fe98e7c360c35df',
            ContractConst.staked_incentive_address: '0x4c481e66798c6c82af77d1e14d3233fe5d592a0b',
            ContractConst.staked_token: '0x170772a06affc0d375ce90ef59c8ec04c7ebf5d2',
            ContractConst.img_url: "https://firebasestorage.googleapis.com/v0/b/token-c515a.appspot.com/o/tokens_v2%2FTRAVA.png?alt=media&token=8ca92414-92e8-4df9-8d52-3730d039e25a"
        },
    }
    mapper = {
        "0x38": bsc,
        "0x1": eth,
        "0xfa": ftm
    }
    AAVE_FORKS = [
        "0x75de5f7c91a89c16714017c7443eca20c7a8c295",
        "0xe29a55a6aeff5c8b1beede5bcf2f0cb3af8f91f5",
        "0x9fad24f572045c7869117160a571b2e50b10d068",
        "0xd98bb590bdfabf18c164056c185fbb6be5ee643f",
        "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9",
        "0xd61afaaa8a69ba541bc4db9c9b40d4142b43b9a4"
    ]
