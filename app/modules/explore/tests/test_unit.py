import pytest
from app.modules.explore.services import ExploreService
from app.modules.auth.seeders import AuthSeeder
from app.modules.dataset.seeders import DataSetSeeder


@pytest.fixture(scope='module')
def test_client(test_client):
    """
    Fixture that sets up the test environment by initializing necessary data:
    - Seeds users via AuthSeeder.
    - Seeds datasets via DataSetSeeder.
    """
    with test_client.application.app_context():
        users = AuthSeeder()
        users.run()

        seeder = DataSetSeeder()
        seeder.run()

    yield test_client


def test_filtering_service_file_count(test_client):
    """
    Test to ensure that the filtering service correctly counts datasets
    based on the number of files within the specified range (0 to 10).
    """
    explore_service = ExploreService()
    datasets = explore_service.filter(min_files=0, max_files=10)
    expected_dataset_count = 4  # Expected all datasets, 4.
    assert len(datasets) == expected_dataset_count, \
        f"Expected {expected_dataset_count} datasets, but got {len(datasets)}"


def test_filtering_service_num_of_leaf(test_client):
    """
    Test to ensure that the filtering service correctly counts datasets
    based on the number of leaf nodes within the specified range (2 to 6).
    """
    explore_service = ExploreService()
    datasets = explore_service.filter(min_leaf_count=2, max_leaf_count=6)
    expected_dataset_count = 1  # Expect only dataset 4, as it is the file "file10.uvl," which has 6 leaves.
    assert len(datasets) == expected_dataset_count, \
        f"Expected {expected_dataset_count} datasets, but got {len(datasets)}"


def test_filtering_service_depth(test_client):
    """
    Test to ensure that the filtering service correctly counts datasets
    based on the depth within the specified range (3 to 10).
    """
    explore_service = ExploreService()
    datasets = explore_service.filter(min_depth=3, max_depth=10)
    expected_dataset_count = 3
    # Expect all datasets except dataset 3, as it is the file "file10.uvl," which has a depth of 2.
    assert len(datasets) == expected_dataset_count, \
        f"Expected {expected_dataset_count} datasets, but got {len(datasets)}"


def test_filtering_service_average_branching_factor(test_client):
    """
    Test to ensure that the filtering service correctly counts datasets
    based on the average branching factor within the specified range (0 to 2).
    """
    explore_service = ExploreService()
    datasets = explore_service.filter(min_av_branching_factor=0, max_av_branching_factor=2)
    expected_dataset_count = 2
    # Expect datasets "sample dataset 2" and "sample dataset 4" for the file "file5.uvl"
    # and "file10.uvl" as both files have an average branching factor of 2.
    assert len(datasets) == expected_dataset_count, \
        f"Expected {expected_dataset_count} datasets, but got {len(datasets)}"


def test_filtering_service_leaf_feature_name(test_client):
    """
    Test to ensure that the filtering service correctly counts datasets
    based on the leaf feature name "Server".
    """
    explore_service = ExploreService()
    datasets = explore_service.filter(leaf_feature_name="Server")
    expected_dataset_count = 2
    # Expected datasets "sample dataset 1" and "sample dataset 3" for the files "file1.uvl"
    # and "file9.uvl" as they are identical and contain "Server" in the leaf feature name.
    assert len(datasets) == expected_dataset_count, \
        f"Expected {expected_dataset_count} datasets, but got {len(datasets)}"


def test_filtering_service_core_feature_name(test_client):
    """
    Test to ensure that the filtering service correctly counts datasets
    based on the core feature name "FitnessMonitor".
    """
    explore_service = ExploreService()
    datasets = explore_service.filter(core_feature_name="FitnessMonitor")
    expected_dataset_count = 2
    # Expected datasets "sample dataset 1" and "sample dataset 2" for the files "file2.uvl"
    # and "file5.uvl" as they contain "FitnessMonitor" in the core feature name.
    assert len(datasets) == expected_dataset_count, \
        f"Expected {expected_dataset_count} datasets, but got {len(datasets)}"

def test_check_sorting_smallest_first(test_client):
    """
    Test to ensure that the filtering service correctly sorts datasets
    based on the size, with smallest first.
    """
    explore_service = ExploreService()
    datasets_sorted = explore_service.filter(sorting="filesize_asc")
    first_ds = datasets_sorted[0]
    assert first_ds.name()=="Sample dataset 4", f"Expected smallest dataset to be 'Sample dataset 4', but got '{first_ds.name()}' instead"

def test_check_sorting_largest_first(test_client):
    """
    Test to ensure that the filtering service correctly sorts datasets
    based on the size, with largest first.
    """
    explore_service = ExploreService()
    datasets_sorted = explore_service.filter(sorting="filesize_desc")
    first_ds = datasets_sorted[0]
    assert first_ds.name()=="Sample dataset 2", f"Expected smallest dataset to be 'Sample dataset 2', but got '{first_ds.name()}' instead"