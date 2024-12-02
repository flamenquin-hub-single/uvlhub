from app.modules.explore.repositories import ExploreRepository
from core.services.BaseService import BaseService


class ExploreService(BaseService):
    def __init__(self):
        super().__init__(ExploreRepository())

    def filter(self, query="", sorting="newest",
               publication_type="any", tags=[],
               min_files=None, max_files=None,
               min_leaf_count=None, max_leaf_count=None,
               min_depth=None, max_depth=None,
               min_av_branching_factor=None,
               max_av_branching_factor=None,
               leaf_feature_name="",
               core_feature_name="", **kwargs):
        return self.repository.filter(query, sorting, publication_type, tags, min_files, max_files,
                                      min_leaf_count, max_leaf_count, min_depth, max_depth,
                                      min_av_branching_factor, max_av_branching_factor, leaf_feature_name,
                                      core_feature_name, **kwargs)
