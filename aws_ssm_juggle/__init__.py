import json
import os

from boto3 import session
from botocore import exceptions
from simple_term_menu import TerminalMenu


def show_menu(items: list, title: str, source: list = None, back: bool = True):
    """
    menu function
    """
    index = None
    source = source or items
    if back:
        items = items + ["Back"]
    menu = TerminalMenu(
        items,
        title=f'? {title} (Press "q"/"ESC" to quit):\n',
        show_search_hint=True,
    )
    index = menu.show()
    if index is None:
        exit(0)
    if items[index] == "Back":
        return None, index
    return source[index], index


def port_forward(boto3_session: session.Session, remote_port: int, local_port: int, target: str):
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
