from pathlib import Path
import pickle
import sys
from typing import TextIO, List
import warnings

import click
from loguru import logger

# Define GBD sex ids for usage with central comp tools.
LWBSG_REI_ID = 339
SEX_IDS = [1, 2]
GBD_ROUND_ID = 5
GBD_REPORTING_LOCATION_SET_ID = 1
GBD_MODEL_RESULTS_LOCATION_SET_ID = 35


@click.command()
@click.option('-o', '--output-dir', type=click.Path())
@click.option('-m', '--measure',
              type=click.Choice(['exposure', 'relative_risk', 'population_attributable_fraction']))
@click.option('-l', '--location', type=click.STRING)
def make_lbwsg_pickle(output_dir: str, measure: str, location: str):
    output_path = Path(output_dir).resolve() / f'{location}_{measure}.pickle'
    configure_logging(output_path)
    main(output_path, location, measure)


def main(path: Path, location: str, measure: str):
    import tables
    tables_version = tables.__version__
    if path.exists():
        logger.info(f'Removing old file at {str(path)}.')
        path.unlink()

    measure_source_map = {
        'exposure': 'exposure',
        'relative_risk': 'rr',
        'population_attributable_fraction': 'burdenator'
    }
    source = measure_source_map[measure]
    location_id = get_location_id(location)

    logger.info(f'Attempting to pull data from {source} for location {location}, id {location_id} '
                f'using tables version {tables_version}.')

    try:
        data = get_draws(
            gbd_id_type='rei_id',
            gbd_id=LWBSG_REI_ID,
            source=source,
            location_id=location_id,
            sex_id=SEX_IDS,
            age_group_id=get_age_group_id(),
            gbd_round_id=GBD_ROUND_ID,
            status='best'
        )
        logger.info(f'Data pulling succesful, writing to {str(path)}.')

        with path.open('wb') as f:
            pickle.dump(data, f)
        print(f'Pickled draws for {source} in {location} to file {str(path)}')
    except Exception:
        logger.info(f'Unable to pull data. Exiting.')
        sys.exit(0)


def get_draws(*args, **kwargs):
    """Wrapper around central comp's get_draws.api.get_draws"""
    from get_draws.api import get_draws as get_draws_
    warnings.filterwarnings("default", module="get_draws")
    return get_draws_(*args, **kwargs)


def get_age_group_id() -> List[int]:
    """Get the age group ids associated with a gbd round."""
    from db_queries import get_age_metadata
    warnings.filterwarnings("default", module="db_queries")
    age_group_set_id = 12  # "The disaggregated age groups used by GBD 2016, 2017, and 2019"
    return list(get_age_metadata(age_group_set_id, GBD_ROUND_ID)['age_group_id'].values)


def get_location_id(location: str) -> int:
    from db_queries import get_location_metadata
    import pandas as pd
    reporting = get_location_metadata(location_set_id=GBD_REPORTING_LOCATION_SET_ID, gbd_round_id=GBD_ROUND_ID)
    reporting = reporting.filter(["location_id", "location_name"])
    model_results = get_location_metadata(location_set_id=GBD_MODEL_RESULTS_LOCATION_SET_ID, gbd_round_id=GBD_ROUND_ID)
    model_results = model_results.filter(["location_id", "location_name"])
    locations = pd.concat([reporting, model_results], ignore_index=True, axis=0).drop_duplicates()
    location_map = {r.location_name: r.location_id for _, r in locations.iterrows()}
    return location_map[location]


def add_logging_sink(sink: TextIO, verbose: int, colorize: bool = False, serialize: bool = False):
    """Adds a logging sink to the global process logger.

    Parameters
    ----------
    sink
        Either a file or system file descriptor like ``sys.stdout``.
    verbose
        Verbosity of the logger.
    colorize
        Whether to use the colorization options from :mod:`loguru`.
    serialize
        Whether the logs should be converted to JSON before they're dumped
        to the logging sink.

    """
    message_format = ('<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
                      '<cyan>{function}</cyan>:<cyan>{line}</cyan> '
                      '- <level>{message}</level>')
    if verbose == 0:
        logger.add(sink, colorize=colorize, level="WARNING", format=message_format, serialize=serialize)
    elif verbose == 1:
        logger.add(sink, colorize=colorize, level="INFO", format=message_format, serialize=serialize)
    elif verbose >= 2:
        logger.add(sink, colorize=colorize, level="DEBUG", format=message_format, serialize=serialize)


def configure_logging(output_path):
    logger.remove(0)  # Clear default configuration
    add_logging_sink(sys.stdout, verbose=2, colorize=True)

    log_file = output_path.parent / 'logs' / f'{output_path.stem}.log'
    if log_file.exists():
        log_file.unlink()
    add_logging_sink(log_file, verbose=2)
