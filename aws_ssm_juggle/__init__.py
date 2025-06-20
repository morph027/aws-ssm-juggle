import json
import os
import signal
import sys
from contextlib import contextmanager
from getpass import getuser
from subprocess import DEVNULL, Popen, check_call
from tempfile import gettempdir

from boto3 import session
from botocore import exceptions
from diskcache import Cache
from InquirerPy import inquirer
from InquirerPy.base import Choice

tmpdir = os.path.join(gettempdir(), f"_aws-ssm-juggle_cache_{getuser()}")
os.makedirs(tmpdir, exist_ok=True, mode=0o700)
cache = Cache(tmpdir)

is_windows = sys.platform == "win32"

try:
    check_call(["session-manager-plugin", "--version"], stdout=DEVNULL)
except FileNotFoundError:
    print("session-manager-plugin is missing")
    sys.exit(1)


# see https://github.com/aws/aws-cli/blob/v2/awscli/compat.py
@contextmanager
def ignore_user_entered_signals():
    """
    Ignores user entered signals to avoid process getting killed.
    """
    if is_windows:
        signal_list = [signal.SIGINT]
    else:
        signal_list = [signal.SIGINT, signal.SIGQUIT, signal.SIGTSTP]
    actual_signals = []
    for user_signal in signal_list:
        actual_signals.append(signal.signal(user_signal, signal.SIG_IGN))
    try:
        yield
    finally:
        for sig, user_signal in enumerate(signal_list):
            signal.signal(user_signal, actual_signals[sig])


def flush(clear_screen: bool):
    if clear_screen:
        print("\033c", end="", flush=True)


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
    flush(clear_screen)
    source = source or items
    if not source:
        print(f"{title} - No results found")
        if not back:
            sys.exit(78)
        input("\nPress <enter> to continue")
        flush(clear_screen)
        return None, len(source)
    indices = dict(zip(source, list(range(0, len(source)))))
    if back:
        items.append(Choice(value=None, name="Back"))
    items.append(Choice(value="quit", name="Quit"))
    try:
        selection = inquirer.fuzzy(
            message=title,
            long_instruction='Type to search - Press "ESC" to quit',
            choices=items,
            keybindings={"interrupt": [{"key": "escape"}, {"key": "c-c"}]},
        ).execute()
    except KeyboardInterrupt:
        sys.exit(0)
    if selection is None:
        return None, len(source)
    if selection == "quit":
        sys.exit(0)
    return selection, indices[selection]


def port_forward(
    boto3_session: session.Session,
    remote_port: int,
    local_port: int,
    target: str,
    background: bool = False,
) -> None:
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
        sys.exit(1)
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
    if background:
        return Popen(args, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, start_new_session=True)
    with ignore_user_entered_signals():
        check_call(args)


@cache.memoize(expire=600)
def get_boto3_profiles() -> list:
    return session.Session().available_profiles
