import time

from app.constants.search_constants import RelationshipType
from app.constants.time_constants import TimeConstants
from app.models.entity.contract import TxAndUserMetadata
from app.models.entity.projects.project import Project, ProjectTypes
from app.models.entity.token import Token
from app.models.explorer.visualization import Visualization
from app.utils.list_dict_utils import get_value_with_default, sort_log, merge_logs, coordinate_logs
from app.utils.time_utils import round_timestamp


class Defi(Project):
    def __init__(self, key,  *args, **kwargs):
        super().__init__(key, project_type=ProjectTypes.defi)

    @classmethod
    def get_metadata(cls, obj, json_dict):
        contracts = json_dict.get('contracts', {})
        for contract in obj.contracts:
            contract_dict = contracts.get(contract.key) or {}
            contract.get_transactions_and_users_info(contract_dict)

        obj.metadata['tvl'] = json_dict.get('tvl')
        obj.metadata['tvlChangeLogs'] = sort_log(get_value_with_default(json_dict, 'tvlChangeLogs', {}))
        obj.metadata['capPerTVL'] = json_dict.get('capPerTVL')

    def get_introduction(self):
        return {
            'projectId': self.key,
            'name': self.name,
            'imgUrl': self.img_url,
            'tvl': self.metadata['tvl'],
            'chains': self.chains,
            'rank': self.rank,
            'projectType': self.project_type,
            'tags': self.tags,
            'url': self.url,
            'explorerUrls': [self.url]
        }

    def get_stats(self, history=True):
        tx_and_users = [contract.tx_and_user_metadata for contract in self.contracts]
        tx_and_user_metadata = TxAndUserMetadata.combine(*tx_and_users)

        tvl_change_rate = Token.get_price_change_rate(self.metadata, 'tvlChangeLogs')
        data = {
            'tvl': self.metadata['tvl'],
            'tvlChangeRate': tvl_change_rate,
            'numberOfActiveWallets': tx_and_user_metadata.number_of_active_wallets,
            'numberOfTransactions': tx_and_user_metadata.number_of_transactions,
            'capPerTVL': self.metadata['capPerTVL']
        }
        if history:
            current_time = int(time.time())
            end_time = round_timestamp(current_time, TimeConstants.A_DAY)
            days_30_ago = end_time - 29 * TimeConstants.A_DAY
            history_data_logs = {
                'tvl': coordinate_logs(self.metadata['tvlChangeLogs'], start_time=days_30_ago, frequency=TimeConstants.A_DAY, fill_start_value=True),
                'numberOfTransactions': coordinate_logs(tx_and_user_metadata.number_of_daily_calls, start_time=days_30_ago, frequency=TimeConstants.A_DAY, fill_start_value=True)
            }
            data['history'] = coordinate_logs(merge_logs(history_data_logs), end_time=end_time, frequency=2 * TimeConstants.A_DAY)

        return data

    def get_visualize(self):
        visualize = Visualization()
        visualize.focus(self.to_node())

        for token in self.tokens:
            token_node = token.to_node()
            visualize.add_node(token_node)
            visualize.link_to_node(target=token_node, type_=RelationshipType.release)

        for contract in self.contracts:
            contract_node = contract.to_node()
            visualize.add_node(contract_node)
            visualize.link_to_node(target=contract_node, type_=RelationshipType.has_contract)

        # TODO: get contract supported tokens (reserves list of lending)

        return visualize
