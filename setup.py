import os

from setuptools import setup, find_packages


if __name__ == "__main__":

    base_dir = os.path.dirname(__file__)
    src_dir = os.path.join(base_dir, "src")

    install_requirements = [
        'vivarium==0.9.3',
        'vivarium_public_health==0.10.4',
        'gbd_mapping==2.1.0',
        'vivarium_gbd_access==2.0.4',
        'tables>=3.4.0',
        'pandas<0.25',
        'click',
        'jinja2',
        'loguru',
        'scipy',
    ]

    extras_require = [
        'vivarium_cluster_tools==1.1.1',
        'vivarium_inputs[data]==3.1.1',
    ]

    setup(
        name='lbwsg',
        package_dir={'': 'src'},
        packages=find_packages(where='src'),
        include_package_data=True,

        install_requires=install_requirements,
        extras_require={
            'dev': extras_require,
        },

        zip_safe=False,

        entry_points='''
            [console_scripts]
            get_draws=lbwsg.cli:get_draws
        '''
    )
