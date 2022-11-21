import yaml


def get_args_config_file(yaml_file_path: str) -> dict:
    # Load parameters of configuration file
    with open(yaml_file_path, "r") as stream:
        try:
            yaml_config_params = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            raise exc

    return yaml_config_params


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    keys = dict1.keys() | dict2.keys()

    return {k: {**dict1.get(k, {}), **dict2.get(k, {})} for k in keys}
