import os
import yaml


def read_config():
    """
    Reads the YAML config file
    """
    default = {
        'host': 'affinity.pw',
        'port': 6697,
        'nickname': ['Cipher', 'Cipher_', 'Cipher__'],
        'password': '',
        'ssl': True
    }
    path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(path, 'config.yaml'), 'r') as f:
        conf = yaml.load(f)

    for key in default:
        if key in conf:
            default[key] = conf[key]

    if not isinstance(default['nickname'], list):
        default['nickname'] = [default['nickname']]

    return default

