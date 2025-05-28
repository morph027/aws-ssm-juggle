#!/usr/bin/env python3
"""
aws-ssm-juggle ssm cli program
"""

import sys

from boto3 import session
from botocore import exceptions

from aws_ssm_juggle import (
    show_menu,
)


def ssm_paginator(ssm: session.Session.client, paginator: str, leaf: str, **kwargs):
    """
    aws paginator
    """
    names = []
    paginator = ssm.get_paginator(paginator)
    iterator = paginator.paginate(**kwargs)
    for page in iterator:
        names.extend(page.get(leaf))
    return names


def get_version(ssm: session.Session.client, parameter: str, version: int):
    """
    get parameter history
    """
    if not parameter:
        return parameter, None, None
    if version:
        return parameter, version, None
    print("fetching available parameter history...")
    versions = ssm_paginator(
        ssm=ssm,
        paginator="get_parameter_history",
        leaf="Parameters",
        Name=parameter,
    )
    parameters = [
        [version.get("Version"), version.get("Labels", []), version.get("Value")]
        for version in versions
    ]
    _versions = []
    for idx, param in enumerate(parameters):
        _versions.append(f"{param[0]} 🏷️ {','.join(param[1])}" if param[1] else param[0])
    ret = show_menu(
        items=_versions,
        title="Select parameter version",
        back=False,
        clear_screen=True,
    )
    if ret[0] is None:
        return (None, *ret)
    _version, _index = ret
    _value = parameters[_index][2]
    return (parameter, str(_version).split(" 🏷️ ")[0] or None, _value, _index)


def get_parameter(ssm: session.Session.client, parameter: str):
    """
    get parameter
    """
    if parameter:
        return parameter, None
    print("fetching available parameters...")
    names = ssm_paginator(
        ssm=ssm,
        paginator="describe_parameters",
        leaf="Parameters",
    )
    names = [name.get("Name") for name in names]
    return show_menu(
        items=names,
        title="Select parameter",
        back=False,
        clear_screen=True,
    )


def menu_loop_condition(
    paramater: str,
    version: str,
    value: str,
):
    menu_loop_condition = paramater and version and value
    return menu_loop_condition


def run():
    """main cli function"""
    boto3_session = session.Session()
    ssm = boto3_session.client("ssm")
    parameter, version, value = (None, 0, None)
    try:
        while not menu_loop_condition(
            paramater=parameter,
            version=version,
            value=value,
        ):
            parameter, _ = get_parameter(ssm=ssm, parameter=parameter)
            parameter, version, value, _ = get_version(
                ssm=ssm, parameter=parameter, version=version
            )
    except exceptions.ClientError as err:
        print(err)
        sys.exit(1)
    print(value)


if __name__ == "__main__":
    run()
