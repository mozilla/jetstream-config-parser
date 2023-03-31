import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from .metric import MetricDefinition

if TYPE_CHECKING:
    from .config import ConfigCollection

FILE_PATH = Path(os.path.dirname(__file__))
METRICS_QUERY = FILE_PATH / "templates" / "metrics_query.sql"


def generate_metrics_sql(
    config_collection: "ConfigCollection",
    metrics: List[str],
    platform: str,
    group_by: Union[List[str], Dict[str, str]] = [],
    where: Optional[str] = None,
):
    """Generates a SQL query for metrics and specified parameters."""
    metric_definitions: List[MetricDefinition] = []
    for slug in metrics:
        definition = config_collection.get_metric_definition(slug, platform)

        if definition is None:
            raise ValueError(f"No definition for metric {slug} on platform {platform} found.")

        metric_definitions.append(definition)

    metrics_per_data_source: Dict[str, Any] = {}
    for metric in metric_definitions:
        if metric.select_expression is None:
            raise ValueError(f"No definition for metric {metric.name}")

        metric.select_expression = (
            config_collection.get_env().from_string(metric.select_expression).render()
        )

        if metric.data_source is None:
            raise ValueError(f"No data source for metric {metric.name}")

        if metric.data_source.name in metrics_per_data_source:
            metrics_per_data_source[metric.data_source.name]["metrics"].append(metric)
        else:
            data_source = config_collection.get_data_source_definition(
                metric.data_source.name, platform
            )

            if data_source is None:
                raise ValueError(f"No valid data source definition found for metric {metric.name}")

            # default parameters need to be set explicitly otherwise they'll be None
            data_source.client_id_column = data_source.client_id_column or "client_id"
            data_source.submission_date_column = (
                data_source.submission_date_column or "submission_date"
            )

            metrics_per_data_source[metric.data_source.name] = {
                "data_source": data_source,
                "metrics": [metric],
            }

    # group by should be a dictionary with the key being the alias and
    # the value the potentially nested field;
    # it can also be specified as list if all fields are top-level fields that don't need an alias
    if isinstance(group_by, list):
        group_by = {g: g for g in group_by}

    template = METRICS_QUERY.read_text()
    return (
        config_collection.get_env()
        .from_string(template)
        .render(
            **{
                "metrics_per_data_source": metrics_per_data_source,
                "where": where,
                "group_by": group_by,
            }
        )
    )
