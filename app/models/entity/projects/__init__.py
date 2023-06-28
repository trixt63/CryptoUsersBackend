from app.models.entity.projects.defi import Defi
from app.models.entity.projects.exchange import Exchange
from app.models.entity.projects.nft import NFT
from app.models.entity.projects.project import ProjectTypes

project_cls_mapping = {
    ProjectTypes.defi: Defi,
    ProjectTypes.nft: NFT,
    ProjectTypes.exchange: Exchange
}
