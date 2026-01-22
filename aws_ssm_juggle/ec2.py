#!/usr/bin/env python3

import json
from subprocess import CalledProcessError, check_call

import configargparse
import shtab
from boto3 import session
from botocore import exceptions
from munch import DefaultMunch

from aws_ssm_juggle import (
    get_boto3_profiles,
    ignore_user_entered_signals,
    port_forward,
    show_menu,
)


class EC2Session:
    """
    EC2Session
    """

    def __init__(
        self,
        boto3_session: session.Session,
        instance_id: str,
        **kwargs,
    ):
        self.boto3_session = boto3_session
        self.ec2 = self.boto3_session.client("ec2")
        self.instance_id = instance_id
        self.document = kwargs.get("document")
        self.local_port = kwargs.get("local_port")
        self.parameters = (kwargs.get("parameters"),)
        self.remote_port = kwargs.get("remote_port")
        self.ssh_args = kwargs.get("ssh_args")
        self.scp_args = kwargs.get("scp_args")
        self.ssm = self.boto3_session.client("ssm")
        self.target = self.instance_id

    def start(self):
        session_parameters = {
            "Target": self.instance_id,
        }
        if self.document:
            session_parameters.update(
                {
                    "DocumentName": self.document,
                }
            )
        # somehow get's passed as tuple
        if all(self.parameters):
            session_parameters.update(
                {
                    "Parameters": next(iter(self.parameters)),
                }
            )
        try:
            ssm_start_session = self.ssm.start_session(**session_parameters)
        except exceptions.ClientError as err:
            print(err)
            exit(1)
        session_response = {
            "SessionId": ssm_start_session.get("SessionId"),
            "TokenValue": ssm_start_session.get("TokenValue"),
            "StreamUrl": ssm_start_session.get("StreamUrl"),
        }
        _args = [
            "session-manager-plugin",
            json.dumps(session_response),
            self.boto3_session.region_name,
            "StartSession",
            self.boto3_session.profile_name,
            json.dumps(session_parameters),
        ]
        with ignore_user_entered_signals():
            check_call(_args)

    def _ssh_scp_proxy_command(self):
        session_parameters = {
            "Target": self.instance_id,
            "DocumentName": "AWS-StartSSHSession",
            "Parameters": {
                "portNumber": [str(22)],
            },
        }
        try:
            ssm_start_session = self.ssm.start_session(**session_parameters)
        except exceptions.ClientError as err:
            print(err)
            exit(1)
        session_response = {
            "SessionId": ssm_start_session.get("SessionId"),
            "TokenValue": ssm_start_session.get("TokenValue"),
            "StreamUrl": ssm_start_session.get("StreamUrl"),
        }
        return f"ProxyCommand=session-manager-plugin '{json.dumps(session_response)}' {self.boto3_session.region_name} StartSession {self.boto3_session.profile_name} '{json.dumps(session_parameters)}'"

    def ssh(self, args: str = ""):
        proxy_command = self._ssh_scp_proxy_command()
        _args = ["ssh"]
        if args:
            _args.extend(args.split(" "))
        _args.extend(
            [
                "-o",
                proxy_command,
                f"{self.instance_id}.{self.boto3_session.region_name}.compute.internal",
            ]
        )
        with ignore_user_entered_signals():
            try:
                check_call(_args)
            except CalledProcessError as e:
                print(f"\nError:\n{e}")

    def scp(self, source: str, target: str, args: str = ""):
        proxy_command = self._ssh_scp_proxy_command()
        _args = ["scp"]
        if args:
            _args.extend(args.split(" "))
        if source.startswith("{instance}"):
            _scp = [
                f"{self.instance_id}.{self.boto3_session.region_name}.compute.internal{source.replace('{instance}', '')}",
                target,
            ]
        elif target.startswith("{instance}"):
            _scp = [
                source,
                f"{self.instance_id}.{self.boto3_session.region_name}.compute.internal{target.replace('{instance}', '')}",
            ]
        else:
            print("Missing {instance} in either source or target")
            exit(1)
        _args.extend(
            [
                "-o",
                proxy_command,
            ]
            + _scp
        )
        with ignore_user_entered_signals():
            try:
                check_call(_args)
            except CalledProcessError as e:
                print(f"\nError:\n{e}")

    def port_forward(self):
        port_forward(
            boto3_session=self.boto3_session,
            remote_port=self.remote_port,
            local_port=self.local_port,
            target=self.target,
        )


def get_parser():
    """argument parser"""
    parser = configargparse.ArgParser(
        prog="ec2-juggle",
        auto_env_var_prefix="EC2_JUGGLE_",
    )
    shtab.add_argument_to(
        parser,
        ["--print-completion"],
        help="Print shell-completion. Run '. <(ec2-juggle --print-completion bash)' to load.",
    )
    parser.add_argument(
        "--profile",
        help="AWS Profile",
        choices=get_boto3_profiles(),
    )
    parser.add_argument(
        "--region",
        help="AWS region name",
        default="eu-central-1",
    )
    parser.add_argument(
        "--instance-id",
        help="EC2 instance id",
    )
    parser.add_argument(
        "--instance-name",
        help="Show only EC2 instances where name matches (e.g. 'web' matches 'my-app-web-server')",
    )
    subparsers = parser.add_subparsers(
        dest="action",
        help="action",
    )
    subparsers.required = True
    start = subparsers.add_parser("start", help="Start interactive ssm session")
    start.add_argument(
        "--document",
        help="document to use for ssm session (e.g. 'AWS-StartInteractiveCommand')",
    )
    start.add_argument(
        "--parameters",
        help='(json) parameters to use for the ssm session document (e.g. \'{"command": ["bash -l"]}\')',
        type=json.loads,
    )
    ssh = subparsers.add_parser("ssh", help="Start ssh session")
    ssh.add_argument(
        "--ssh-args",
        help="ssh command arguments to pass on",
    )
    scp = subparsers.add_parser("scp", help="Start scp session")
    scp.add_argument(
        "--source",
        help="scp source - use {instance} as placeholder if you want to use the ec2 instance as source (e.g. {instance}:/tmp/foo)",
        required=True,
    )
    scp.add_argument(
        "--target",
        help="scp target - use {instance} as placeholder if you want to use the ec2 instance as target (e.g. {instance}:/tmp/foo)",
        required=True,
    )
    scp.add_argument(
        "--scp-args",
        help="scp command arguments to pass on",
    )
    forward = subparsers.add_parser("forward", help="Start ssh session")
    forward.add_argument(
        "--remote-port",
        help="EC2 instance remote port",
        type=int,
        required=True,
    )
    forward.add_argument(
        "--local-port",
        help="Local port for forwarding. Defaults to random port (0)",
        type=int,
        default=0,
    )
    return DefaultMunch.fromDict(parser)


def ec2_paginator(boto3_session: session.Session, paginator: str, leaf: str, **kwargs):
    """
    aws paginator
    """
    res = []
    ec2 = boto3_session.client("ec2")
    paginator = ec2.get_paginator(paginator)
    iterator = paginator.paginate(**kwargs)
    for page in iterator:
        res.extend(page.get(leaf))
    return res


def get_instance_id(boto3_session: session.Session, instance_id: str, instance_name: str = ""):
    """
    get instance_id
    """
    if instance_id:
        return instance_id, None
    print("fetching available instances...")
    filters = [
        {
            "Name": "instance-state-name",
            "Values": ["running"],
        },
    ]
    if instance_name:
        filters.append({"Name": "tag:Name", "Values": [f"*{instance_name}*"]})
    reservations = ec2_paginator(
        boto3_session=boto3_session,
        paginator="describe_instances",
        leaf="Reservations",
        Filters=filters,
    )
    instances = []
    for reservation in reservations:
        for instance in reservation.get("Instances"):
            tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
            instances.append(f"{instance.get('InstanceId')} - {tags.get('Name')}")
    return show_menu(
        items=instances,
        title="Select instance id",
        back=False,
    )


def run():
    """main cli function"""
    parser = get_parser()
    arguments = parser.parse_args()
    boto3_session_args = {
        "region_name": arguments.region,
        "profile_name": arguments.profile,
    }
    boto3_session = session.Session(**boto3_session_args)
    ec2_session_args = {}
    instance_name = arguments.instance_name
    instance_id = arguments.instance_id
    if "document" in arguments and arguments.document:
        ec2_session_args.update(
            {
                "document": arguments.document,
            }
        )
    if "local_port" in arguments and arguments.local_port:
        ec2_session_args.update(
            {
                "local_port": arguments.local_port,
            }
        )
    if "parameters" in arguments and arguments.parameters:
        ec2_session_args.update(
            {
                "parameters": arguments.parameters,
            }
        )
    if "remote_port" in arguments and arguments.remote_port:
        ec2_session_args.update(
            {
                "remote_port": arguments.remote_port,
            }
        )
    try:
        while not instance_id:
            instance_id, _ = get_instance_id(
                boto3_session=boto3_session,
                instance_id=instance_id,
                instance_name=instance_name,
            )
            instance_id = instance_id.split(" - ")[0]
        ec2_session = EC2Session(
            boto3_session=boto3_session,
            instance_id=instance_id,
            **ec2_session_args,
        )
        match arguments.action:
            case "start":
                ec2_session.start()
            case "ssh":
                ec2_session.ssh(
                    args=arguments.ssh_args,
                )
            case "scp":
                ec2_session.scp(
                    source=arguments.source,
                    target=arguments.target,
                    args=arguments.scp_args,
                )
            case "forward":
                ec2_session.port_forward()
    except exceptions.ClientError as err:
        print(err)
        exit(1)


if __name__ == "__main__":
    run()
