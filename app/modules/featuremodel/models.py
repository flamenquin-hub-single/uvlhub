from app import db
from sqlalchemy import Enum as SQLAlchemyEnum

from app.modules.dataset.models import Author, PublicationType
from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.fm_metamodel.operations import FMAverageBranchingFactor, FMCountLeafs
from flamapy.metamodels.fm_metamodel.operations import FMMaxDepthTree


class FeatureModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_set_id = db.Column(db.Integer, db.ForeignKey('data_set.id'), nullable=False)
    fm_meta_data_id = db.Column(db.Integer, db.ForeignKey('fm_meta_data.id'))
    files = db.relationship('Hubfile', backref='feature_model', lazy=True, cascade="all, delete")
    fm_meta_data = db.relationship('FMMetaData', uselist=False, backref='feature_model', cascade="all, delete")

    def __repr__(self):
        return f'FeatureModel<{self.id}>'

    def calculate_statistics(self):
        from app.modules.hubfile.services import HubfileService
        hubfile = HubfileService().get_by_id(self.id)
        fm = UVLReader(hubfile.get_path()).transform()

        leaf_counter = FMCountLeafs()
        leaf_counter.execute(fm)
        leaf_count = leaf_counter.get_result()

        depth_calculator = FMMaxDepthTree()
        depth_calculator.execute(fm)
        max_tree_depth = depth_calculator.get_result()

        branching_factor_calculator = FMAverageBranchingFactor()
        branching_factor_calculator.execute(fm)
        average_branching_factor = branching_factor_calculator.get_result()

        return {
            "leaf_count": leaf_count,
            "max_depth": max_tree_depth,
            "branching_factor": average_branching_factor
        }


class FMMetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uvl_filename = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(SQLAlchemyEnum(PublicationType), nullable=False)
    publication_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    uvl_version = db.Column(db.String(120))
    fm_metrics_id = db.Column(db.Integer, db.ForeignKey('fm_metrics.id'))
    fm_metrics = db.relationship('FMMetrics', uselist=False, backref='fm_meta_data')
    authors = db.relationship('Author', backref='fm_metadata', lazy=True, cascade="all, delete",
                              foreign_keys=[Author.fm_meta_data_id])

    def __repr__(self):
        return f'FMMetaData<{self.title}'


class FMMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solver = db.Column(db.Text)
    not_solver = db.Column(db.Text)

    def __repr__(self):
        return f'FMMetrics<solver={self.solver}, not_solver={self.not_solver}>'
