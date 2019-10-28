import json
import os

from sys import stdout, stderr


def correct_dict(dict_):
    for k, field in dict_.items():
        if isinstance(field, dict):
            dict_[k] = correct_dict(field)
        elif isinstance(field, list):
            dict_[k] = list(correct_dict(dict(zip(range(len(field)), field))).values())
        elif isinstance(field, str):
            if field.startswith("x"):
                dict_[k] = int(field[1:], base=16)
    return dict_


def load(name):
    """
    loads a json module and returns the result s a dictionary
    """
    path = "configs/{0}.json".format(name)
    stdout.write("Loading: {0:<90}".format(path + " ..."))
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return {
            "__meta__": {
                "errors": [e],
                "outcome": "fatal error",
                "filepath": path,
                "filename": path.split("/")[-1]
            }
          }
    stdout.write("Success\n")
    data = correct_dict(data)

    data["__meta__"] = {
        "errors": [],
        "outcome": "success",
        "filepath": path,
        "filename": path.split("/")[-1]
    }
    return data


def can_load(name):
    """
    checks if a json module of this name is available
    """
    directory = "/".join((__file__.split("/"))[:-1])
    return os.path.isfile(directory + "/configs/" + name + ".json")


def save(name, data):
    """
    saves a dictionary as a json module by a given name
    """
    with open("configs/{0}.json".format(name), encoding="UTF-8") as f:
        json.dump(data, f)


def load_all():
    """
    loads all modules specified in the entrance file
    """
    gen = load("entrance")
    for f, v in gen.items():
        if f != "__meta__":
            gen[f] = load(v)
    return gen
