import os

import yaml

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, 'group_config.yaml')) as f:
    group_config = yaml.safe_load(f)
