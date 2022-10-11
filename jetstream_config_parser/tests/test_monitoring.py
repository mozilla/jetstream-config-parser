from pathlib import Path
from textwrap import dedent

import pytest
import toml

from jetstream_config_parser.monitoring import MonitoringConfiguration, MonitoringSpec

TEST_DIR = Path(__file__).parent
DEFAULT_METRICS_CONFIG = TEST_DIR / "data" / "default_metrics.toml"


class TestMonitoringSpec:
    def test_trivial_configuration(self, config_collection):
        spec = MonitoringSpec.from_dict({})
        assert isinstance(spec, MonitoringSpec)
        cfg = spec.resolve(experiment=None, configs=config_collection)
        assert isinstance(cfg, MonitoringConfiguration)
        assert cfg.metrics == []

    def test_metric_definition(self, config_collection):
        config_str = dedent(
            """
            [project]
            metrics = ["test"]

            [metrics]
            [metrics.test]
            select_expression = "SELECT 1"
            data_source = "foo"

            [metrics.test.statistics]
            sum = {}

            [data_sources]
            [data_sources.foo]
            from_expression = "test"
            """
        )
        spec = MonitoringSpec.from_dict(toml.loads(config_str))
        assert spec.metrics.definitions["test"].select_expression == "SELECT 1"
        assert spec.data_sources.definitions["foo"].from_expression == "test"
        conf = spec.resolve(experiment=None, configs=config_collection)
        assert conf.metrics[0].metric.name == "test"
        assert conf.metrics[0].metric.data_source.name == "foo"

    def test_duplicate_metrics_are_okay(self, config_collection):
        config_str = dedent(
            """
            [project]
            metrics = ["test", "test"]

            [metrics]
            [metrics.test]
            select_expression = "SELECT 1"
            data_source = "foo"

            [metrics.test.statistics]
            sum = {}

            [data_sources]
            [data_sources.foo]
            from_expression = "test"
            """
        )
        spec = MonitoringSpec.from_dict(toml.loads(config_str))
        cfg = spec.resolve(experiment=None, configs=config_collection)
        assert len(cfg.metrics) == 1

    def test_data_source_definition(self, config_collection):
        config_str = dedent(
            """
            [project]
            metrics = ["test", "test2"]

            [metrics]
            [metrics.test]
            select_expression = "SELECT 1"
            data_source = "eggs"

            [metrics.test.statistics]
            sum = {}

            [metrics.test2]
            select_expression = "SELECT 1"
            data_source = "silly_knight"

            [metrics.test2.statistics]
            sum = {}

            [data_sources.eggs]
            from_expression = "england.camelot"

            [data_sources.silly_knight]
            from_expression = "france"
            """
        )
        spec = MonitoringSpec.from_dict(toml.loads(config_str))
        cfg = spec.resolve(experiment=None, configs=config_collection)
        test = [p for p in cfg.metrics if p.metric.name == "test"][0]
        test2 = [p for p in cfg.metrics if p.metric.name == "test2"][0]
        assert test.metric.data_source.name == "eggs"
        assert "camelot" in test.metric.data_source.from_expression
        assert test2.metric.data_source.name == "silly_knight"
        assert "france" in test2.metric.data_source.from_expression

    def test_merge(self, config_collection):
        """Test merging configs"""
        config_str = dedent(
            """
            [metrics]
            [metrics.test]
            select_expression = "SELECT 1"
            data_source = "foo"

            [metrics.test.statistics]
            sum = {}

            [metrics.test2]
            select_expression = "SELECT 2"
            data_source = "foo"

            [metrics.test2.statistics]
            sum = {}

            [data_sources]
            [data_sources.foo]
            from_expression = "test"

            [dimensions]
            [dimensions.foo]
            select_expression = "bar"
            data_source = "foo"
            """
        )
        spec = MonitoringSpec.from_dict(toml.loads(config_str))

        config_str = dedent(
            """
            [project]
            name = "foo"
            metrics = ["test", "test2"]

            [metrics]
            [metrics.test]
            select_expression = "SELECT 'd'"
            data_source = "foo"

            [metrics.test.statistics]
            sum = {}

            [data_sources]
            [data_sources.foo]
            from_expression = "bar"
            """
        )
        spec2 = MonitoringSpec.from_dict(toml.loads(config_str))
        spec.merge(spec2)
        cfg = spec.resolve(experiment=None, configs=config_collection)

        assert cfg.project.name == "foo"
        test = [p for p in cfg.metrics if p.metric.name == "test"][0]
        test2 = [p for p in cfg.metrics if p.metric.name == "test2"][0]
        assert test.metric.select_expression == "SELECT 'd'"
        assert test.metric.data_source.name == "foo"
        assert test.metric.data_source.from_expression == "bar"
        assert test2.metric.select_expression == "SELECT 2"

    def test_unknown_metric_failure(self, config_collection):
        config_str = dedent(
            """
            [project]
            name = "foo"
            metrics = ["test", "test2"]

            [metrics]
            [metrics.test]
            select_expression = "SELECT 'd'"
            data_source = "foo"

            [metrics.test.statistics]
            sum = {}

            [data_sources]
            [data_sources.foo]
            from_expression = "test"
            """
        )

        with pytest.raises(ValueError) as e:
            spec = MonitoringSpec.from_dict(toml.loads(config_str))
            spec.resolve(experiment=None, configs=config_collection)

        assert "No definition for metric test2." in str(e)