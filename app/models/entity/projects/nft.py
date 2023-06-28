import time

from app.constants.search_constants import RelationshipType
from app.constants.time_constants import TimeConstants
from app.models.entity.projects.project import Project, ProjectTypes
from app.models.entity.token import Token
from app.models.explorer.visualization import Visualization
from app.utils.list_dict_utils import get_value_with_default, sort_log, merge_logs, coordinate_logs
from app.utils.math_utils import divide
from app.utils.time_utils import round_timestamp


class NFT(Project):
    def __init__(self, key, *args, **kwargs):
        super().__init__(key, project_type=ProjectTypes.nft)

    @classmethod
    def get_metadata(cls, obj, json_dict):
        for token in obj.tokens:
            token.name = obj.name
            token.symbol = json_dict.get('symbol', 'NFT')
            token.price = json_dict.get('price')
            token.price_change_rate = token.__class__.get_price_change_rate(json_dict, 'priceChangeLogs')

        obj.metadata['price'] = json_dict.get('price')
        obj.metadata['priceChangeLogs'] = sort_log(get_value_with_default(json_dict, 'priceChangeLogs', {}))
        obj.metadata['volume'] = json_dict.get('volume')
        obj.metadata['volumeChangeLogs'] = sort_log(get_value_with_default(json_dict, 'volumeChangeLogs', {}))
        obj.metadata['numberOfItems'] = json_dict.get('numberOfItems')
        obj.metadata['numberOfOwners'] = json_dict.get('numberOfOwners')
        obj.metadata['numberOfListedItems'] = json_dict.get('numberOfListedItems')

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
        price_change_rate = Token.get_price_change_rate(self.metadata, 'priceChangeLogs')
        volume_change_rate = Token.get_price_change_rate(self.metadata, 'volumeChangeLogs')

        listed_rate = divide(self.metadata['numberOfListedItems'], self.metadata['numberOfItems'])
        unique_rate = divide(self.metadata['numberOfOwners'], self.metadata['numberOfItems'])

        data = {
            'price': self.metadata['price'],
            'priceChangeRate': price_change_rate,
            'volume': self.metadata['volume'],
            'volumeChangeRate': volume_change_rate,
            'numberOfItems': self.metadata['numberOfItems'],
            'listedRate': listed_rate,
            'numberOfOwners': self.metadata['numberOfOwners'],
            'uniqueRate': unique_rate
        }

        if history:
            current_time = int(time.time())
            end_time = round_timestamp(current_time, TimeConstants.A_DAY)
            days_30_ago = end_time - 28 * TimeConstants.A_DAY
            history_data_logs = {
                'price': coordinate_logs(self.metadata['priceChangeLogs'], start_time=days_30_ago, frequency=TimeConstants.A_DAY, fill_start_value=True),
                'volume': coordinate_logs(self.metadata['volumeChangeLogs'], start_time=days_30_ago, frequency=TimeConstants.A_DAY, fill_start_value=True)
            }
            data['history'] = coordinate_logs(merge_logs(history_data_logs), end_time=end_time, frequency=TimeConstants.A_DAY)

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

        return visualize
