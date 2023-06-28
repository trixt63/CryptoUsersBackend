import time

from app.constants.search_constants import RelationshipType
from app.constants.time_constants import TimeConstants
from app.models.entity.projects.project import Project, ProjectTypes
from app.models.entity.token import Token
from app.models.explorer.visualization import Visualization
from app.utils.list_dict_utils import sort_log, get_value_with_default, combined_logs, merge_logs, coordinate_logs


class Exchange(Project):
    def __init__(self, key,  *args, **kwargs):
        super().__init__(key, project_type=ProjectTypes.exchange)

    @classmethod
    def get_metadata(cls, obj, json_dict):
        tokens = json_dict.get('tokens', {})
        chains = set()
        for token_key in json_dict.get('supportedTokenAddresses', {}):
            token_dict = tokens.get(token_key)
            if token_dict:
                token = Token.from_dict(token_dict)
                obj.tokens.append(token)
                chains.update(token.chains)

        obj.chains = list(chains)
        obj.tags = []
        if 'spot_exchange' in json_dict.get('sources', {}):
            obj.tags.append('Spot Exchange')
        if 'derivative_exchange' in json_dict.get('sources', {}):
            obj.tags.append('Derivative Exchange')

        obj.metadata['volume'] = json_dict.get('spotVolume', 0) + json_dict.get('derivativeVolume', 0)
        obj.metadata['numberOfMarkets'] = json_dict.get('spotMarkets', 0) + json_dict.get('derivativeMarkets', 0)
        obj.metadata['numberOfCoins'] = json_dict.get('numberOfCoins')

        spot_volume_change_logs = sort_log(get_value_with_default(json_dict, 'spotVolumeChangeLogs', {}))
        derivative_volume_change_logs = sort_log(get_value_with_default(json_dict, 'derivativeVolumeChangeLogs', {}))
        obj.metadata['volumeChangeLogs'] = combined_logs(spot_volume_change_logs, derivative_volume_change_logs)

    def get_introduction(self):
        return {
            'projectId': self.key,
            'name': self.name,
            'imgUrl': self.img_url,
            'volume': self.metadata['volume'],
            'chains': self.chains,
            'rank': self.rank,
            'projectType': self.project_type,
            'tags': self.tags,
            'url': self.url,
            'explorerUrls': [self.url]
        }

    def get_stats(self, history=True):
        volume_change_rate = Token.get_price_change_rate(self.metadata, 'volumeChangeLogs')
        data = {
            'volume': self.metadata['volume'],
            'volumeChangeRate': volume_change_rate,
            'numberOfMarkets': self.metadata['numberOfMarkets'],
            'numberOfCoins': self.metadata['numberOfCoins']
        }
        if history:
            current_time = int(time.time())
            days_30_ago = current_time - TimeConstants.DAYS_30
            history_data_logs = {
                'volume': coordinate_logs(self.metadata['volumeChangeLogs'], start_time=days_30_ago, frequency=TimeConstants.A_DAY),
            }
            data['history'] = coordinate_logs(merge_logs(history_data_logs), end_time=current_time, frequency=TimeConstants.A_DAY)

        return data

    def get_visualize(self):
        visualize = Visualization()
        visualize.focus(self.to_node())

        for token in self.tokens:
            token_node = token.to_node()
            visualize.add_node(token_node)
            visualize.link_to_node(target=token_node, type_=RelationshipType.support)

        for contract in self.contracts:
            contract_node = contract.to_node()
            visualize.add_node(contract_node)
            visualize.link_to_node(target=contract_node, type_=RelationshipType.has_contract)

        return visualize
