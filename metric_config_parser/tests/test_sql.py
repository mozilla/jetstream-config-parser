from pathlib import Path

import pytest

ROOT = Path(__file__).parent
TEST_DATA = ROOT / "sql"


def test_generate_query_single_metric(config_collection):
    assert (
        config_collection.get_metrics_sql(metrics=["active_hours"], platform="firefox_desktop")
        == (TEST_DATA / "test_generate_query_single_metric.expected.sql").read_text()
    )


def test_generate_query_multiple_metrics(config_collection):
    assert (
        config_collection.get_metrics_sql(
            metrics=["active_hours", "days_of_use"], platform="firefox_desktop"
        )
        == (TEST_DATA / "test_generate_query_multiple_metrics.expected.sql").read_text()
    )


def test_generate_query_with_parameters(config_collection):
    assert (
        config_collection.get_metrics_sql(
            metrics=["active_hours", "days_of_use"],
            platform="firefox_desktop",
            group_by=["build_id", "sample_id"],
            where="submission_date = '2023-01-01' AND normalized_channel = 'release'",
        )
        == (TEST_DATA / "test_generate_query_with_parameters.expected.sql").read_text()
    )

    assert (
        config_collection.get_metrics_sql(
            metrics=["active_hours", "days_of_use"],
            platform="firefox_desktop",
            group_by={"build_id": "build_id", "sample_id": "sample_id"},
            where="submission_date = '2023-01-01' AND normalized_channel = 'release'",
        )
        == (TEST_DATA / "test_generate_query_with_parameters.expected.sql").read_text()
    )


def test_generate_query_with_multiple_metrics_different_data_sources(config_collection):
    assert (
        config_collection.get_metrics_sql(
            metrics=["active_hours", "days_of_use", "unenroll", "view_about_logins"],
            platform="firefox_desktop",
            group_by=["build_id", "sample_id"],
            where="submission_date = '2023-01-01' AND normalized_channel = 'release'",
        )
        == (
            TEST_DATA
            / "test_generate_query_with_multiple_metrics_different_data_sources.expected.sql"
        ).read_text()
    )


def test_no_metric_definition_found(config_collection):
    with pytest.raises(ValueError):
        config_collection.get_metrics_sql(metrics=["doesnt-exist"], platform="firefox_desktop")
