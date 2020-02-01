import click
import pickle

from vivarium_gbd_access.utilities import get_draws
from vivarium_gbd_access.gbd import get_age_group_id
from gbd_mapping import risk_factors
from vivarium_inputs.utility_data import get_location_id

# Define GBD sex ids for usage with central comp tools.
COMBINED = [3]
GBD_ROUND_ID = 5


@click.command()
@click.option('-s', '--source',
              default='all',
              show_default=True,
              help='Data source')
@click.option('-l', '--location',
              default='all',
              show_default=True,
              help='Location to make specification for.')
def get_draws(source: str, location: str):
    draws = get_draws(
        gbd_id_type='rei_id',
        gbd_id=risk_factors.low_birth_weight_and_short_gestation.gbd_id,
        source='exposure',
        location_id=get_location_id(location),
        sex_id=COMBINED,
        age_group_id=get_age_group_id(),
        gbd_round_id=GBD_ROUND_ID,
        status='best'
    )

    filename = f'{location}_{source}.pkl'
    with open(filename, 'wb') as f:
        pickle.dump(draws, f)

    print(f'Pickled draws for {source} in {location} to file {filename}')
