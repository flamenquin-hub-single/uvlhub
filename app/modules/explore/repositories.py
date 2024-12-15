import re
from sqlalchemy import any_, or_
import unidecode
from app.modules.dataset.models import Author, DSMetaData, DataSet, PublicationType
from app.modules.featuremodel.models import FMMetaData, FeatureModel
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def filter(self, query="", sorting="newest",
               publication_type="any", tags=[],
               min_files=None, max_files=None,
               min_leaf_count=None, max_leaf_count=None,
               min_depth=None, max_depth=None,
               min_av_branching_factor=None, max_av_branching_factor=None,
               leaf_feature_name="", core_feature_name="",
               **kwargs):
        # Normalize and remove unwanted characters
        normalized_query = unidecode.unidecode(query).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)

        filters = []
        min_files = int(min_files) if min_files is not None else None
        max_files = int(max_files) if max_files is not None else None

        min_leaf_count = int(min_leaf_count) if min_leaf_count is not None else None
        max_leaf_count = int(max_leaf_count) if max_leaf_count is not None else None

        min_depth = int(min_depth) if min_depth is not None else None
        max_depth = int(max_depth) if max_depth is not None else None

        min_av_branching_factor = float(min_av_branching_factor) if min_av_branching_factor is not None else None
        max_av_branching_factor = float(max_av_branching_factor) if max_av_branching_factor is not None else None

        for word in cleaned_query.split():
            filters.append(DSMetaData.title.ilike(f"%{word}%"))
            filters.append(DSMetaData.description.ilike(f"%{word}%"))
            filters.append(Author.name.ilike(f"%{word}%"))
            filters.append(Author.affiliation.ilike(f"%{word}%"))
            filters.append(Author.orcid.ilike(f"%{word}%"))
            filters.append(FMMetaData.uvl_filename.ilike(f"%{word}%"))
            filters.append(FMMetaData.title.ilike(f"%{word}%"))
            filters.append(FMMetaData.description.ilike(f"%{word}%"))
            filters.append(FMMetaData.publication_doi.ilike(f"%{word}%"))
            filters.append(FMMetaData.tags.ilike(f"%{word}%"))
            filters.append(DSMetaData.tags.ilike(f"%{word}%"))

        datasets = (
            self.model.query
            .join(DataSet.ds_meta_data)
            .join(DSMetaData.authors)
            .join(DataSet.feature_models)
            .join(FeatureModel.fm_meta_data)
            .filter(or_(*filters))
            .filter(DSMetaData.dataset_doi.isnot(None))  # Exclude datasets with empty dataset_doi
        )

        if publication_type != "any":
            matching_type = None
            for member in PublicationType:
                if member.value.lower() == publication_type:
                    matching_type = member
                    break

            if matching_type is not None:
                datasets = datasets.filter(DSMetaData.publication_type == matching_type.name)

        if tags:
            datasets = datasets.filter(DSMetaData.tags.ilike(any_(f"%{tag}%" for tag in tags)))

        # Order by created_at
        if sorting == "oldest":
            datasets = datasets.order_by(self.model.created_at.asc())
        elif sorting == "filesize_asc":
            datasets = datasets.all()
            datasets = sorted(datasets, key=lambda ds: ds.get_file_total_size(), reverse=False)
        elif sorting == "filesize_desc":
            datasets = datasets.all()
            datasets = sorted(datasets, key=lambda ds: ds.get_file_total_size(), reverse=True)
        else:
            datasets = datasets.order_by(self.model.created_at.desc())

        if min_files is not None:
            datasets = [dataset for dataset in datasets if dataset.get_files_count() >= min_files]
        if max_files is not None:
            datasets = [dataset for dataset in datasets if dataset.get_files_count() <= max_files]

        filtered_datasets = []

        for dataset in datasets:
            feature_models = dataset.feature_models  
            dataset_passes_filter = False  

            for model in feature_models:
                stats = model.calculate_statistics()  
                leaf_count = stats["leaf_count"]
                depth = stats["max_depth"]
                branching_factor = stats["branching_factor"]

                # Aplicar filtros a las estadísticas del modelo
                if ((min_leaf_count is not None and leaf_count < min_leaf_count) or
                    (max_leaf_count is not None and leaf_count > max_leaf_count) or
                    (min_depth is not None and depth < min_depth) or
                    (max_depth is not None and depth > max_depth) or
                    (min_av_branching_factor is not None and branching_factor < min_av_branching_factor) or
                        (max_av_branching_factor is not None and branching_factor > max_av_branching_factor)):
                    continue

                if leaf_feature_name:
                    leaf_feature_names = model.get_leaf_feature_names()
                    print(leaf_feature_name)
                    if leaf_feature_name not in leaf_feature_names:
                        continue

                if core_feature_name:
                    core_feature_names = model.get_core_feature_names()
                    if core_feature_name not in core_feature_names:
                        continue

                dataset_passes_filter = True
                print("dataset_passes_filter")
                break

            if dataset_passes_filter:
                filtered_datasets.append(dataset)  

        return filtered_datasets
