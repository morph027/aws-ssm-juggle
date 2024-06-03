import json
import os
from tempfile import gettempdir

from boto3 import session
from botocore import exceptions
from diskcache import Cache
from InquirerPy import inquirer
from InquirerPy.base import Choice

cache = Cache(os.path.join(gettempdir(), "_aws-ssm-juggle_cache"))


def show_menu(
    items: list,
    title: str,
    source: list = None,
    back: bool = True,
    clear_screen: bool = False,
) -> tuple:
    """
    menu function
    """
    if clear_screen:
        print("\033c", end="", flush=True)
    source = source or items
    indices = dict(zip(source, list(range(0, len(source)))))
    if back:
        items.append(Choice(value=None, name="Back"))
    try:
        selection = inquirer.fuzzy(
            message=title,
            long_instruction='Type to search - Press "ESC" to quit',
            choices=items,
            keybindings={"interrupt": [{"key": "escape"}]},
        ).execute()
    except KeyboardInterrupt:
        exit(0)
    if selection is None:
        return None, len(source)
    return selection, indices[selection]


def port_forward(boto3_session: session.Session, remote_port: int, local_port: int, target: str) -> None:
    """
    forward port
    """
    parameters = {
        "portNumber": [str(remote_port)],
        "localPortNumber": [str(local_port)],
    }
    ssm = boto3_session.client("ssm")
    try:
        ssm_start_session = ssm.start_session(
            Target=target,
            DocumentName="AWS-StartPortForwardingSession",
            Parameters=parameters,
        )
    except exceptions.ClientError as err:
        print(err)
        exit(1)
    args = [
        "session-manager-plugin",
        json.dumps(
            {
                "SessionId": ssm_start_session.get("SessionId"),
                "TokenValue": ssm_start_session.get("TokenValue"),
                "StreamUrl": ssm_start_session.get("StreamUrl"),
            }
        ),
        boto3_session.region_name,
        "StartSession",
        boto3_session.profile_name,
    ]
    args.extend(
        [
            json.dumps(
                {
                    "Target": target,
                    "DocumentName": "AWS-StartPortForwardingSession",
                    "Parameters": parameters,
                }
            ),
        ]
    )
    try:
        os.execvp(
            "session-manager-plugin",
            args,
        )
    except FileNotFoundError:
        print("session-manager-plugin missing!")


@cache.memoize(expire=600)
def get_boto3_profiles() -> list:
    return session.Session().available_profiles
