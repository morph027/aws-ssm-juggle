#!/usr/bin/env python3
"""
aws-ssm-juggle ecs cli program
"""

import json
import sys
from subprocess import check_call

import configargparse
import shtab
from boto3 import session
from botocore import exceptions

from aws_ssm_juggle import (
    get_boto3_profiles,
    ignore_user_entered_signals,
    port_forward,
    show_menu,
)


class ECSSession:
    """
    ECSSession
    """

    def __init__(
        self,
        boto3_session: session.Session,
        cluster: str,
        command: str,
        container: str,
        container_index: int,
        local_port: int,
        remote_port: int,
        task: str,
        task_details: dict,
    ):
        """
        ECSSession
        """
        self.boto3_session = boto3_session
        self.cluster = cluster
        self.command = command
        self.container = container
        self.container_index = container_index
        self.ecs = self.boto3_session.client("ecs")
        self.local_port = local_port
        self.remote_port = remote_port
        self.ssm = self.boto3_session.client("ssm")
        self.task = task
        self.task_details = task_details
        self.runtime_id = task_details.get("tasks")[0].get("containers")[container_index].get("runtimeId")
        if not self.runtime_id:
            raise RuntimeError("unable to get runtimeId from container, looks like it's not running.")
        self.target = f"ecs:{self.cluster}_{self.runtime_id.split('-')[0]}_{self.runtime_id}"

    def port_forward(self):
        port_forward(
            boto3_session=self.boto3_session,
            remote_port=self.remote_port,
            local_port=self.local_port,
            target=self.target,
        )

    def execute_command(self):
        """
        execute command
        """
        try:
            ecs_execute_command_session = self.ecs.execute_command(
                cluster=self.cluster,
                container=self.container,
                task=self.task,
                command=self.command,
                interactive=True,
            ).get("session")
        except exceptions.ClientError as err:
            print(err)
            sys.exit(1)
        args = [
            "session-manager-plugin",
            json.dumps(ecs_execute_command_session),
            self.boto3_session.region_name,
            "StartSession",
            self.boto3_session.profile_name,
            json.dumps(
                {"Target": self.target},
            ),
        ]
        with ignore_user_entered_signals():
            check_call(args)


def get_parser():
    """argument parser"""
    parser = configargparse.ArgParser(
        prog="ecs-juggle",
        auto_env_var_prefix="ECS_JUGGLE_",
    )
    shtab.add_argument_to(
        parser,
        ["--print-completion"],
        help="Print shell-completion. Run '. <(ecs-juggle --print-completion bash)' to load.",
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
        "--cluster",
        help="ECS cluster name",
    )
    parser.add_argument(
        "--service",
        help="ECS service name",
    )
    parser.add_argument(
        "--task",
        help="ECS task id",
    )
    parser.add_argument(
        "--container",
        help="ECS container name",
    )
    subparsers = parser.add_subparsers(
        dest="action",
        help="action",
    )
    subparsers.required = True
    forward = subparsers.add_parser("forward", help="Portforwarding")
    forward.add_argument(
        "--remote-port",
        help="ECS container remote port",
        type=int,
    )
    forward.add_argument(
        "--local-port",
        help="Local port for forwarding. Defaults to random port (0)",
        type=int,
        default=0,
    )
    command = subparsers.add_parser("command", help="Execute command")
    command.add_argument(
        "--command",
        help="Execute command",
        default="/bin/bash",
    )
    return parser


def ecs_paginator(ecs: session.Session.client, paginator: str, leaf: str, **kwargs):
    """
    aws paginator
    """
    arns = []
    paginator = ecs.get_paginator(paginator)
    iterator = paginator.paginate(**kwargs)
    for page in iterator:
        arns.extend(page.get(leaf))
    return arns


def get_cluster(ecs: session.Session.client, cluster: str):
    """
    get clusters
    """
    if cluster:
        return cluster, None
    print("fetching available clusters...")
    arns = ecs_paginator(
        ecs=ecs,
        paginator="list_clusters",
        leaf="clusterArns",
    )
    clusters = [cluster.split("/")[-1] for cluster in arns]
    return show_menu(
        items=clusters,
        title="Select cluster",
        back=False,
        clear_screen=True,
    )


def get_service(ecs: session.Session.client, service: str, cluster: str):
    """
    get service
    """
    if not cluster:
        return cluster, None, None
    if service:
        return cluster, service, None
    print("fetching available services...")
    arns = ecs_paginator(
        ecs=ecs,
        paginator="list_services",
        leaf="serviceArns",
        cluster=cluster,
    )
    services = [service.split("/")[-1] for service in arns]
    ret = show_menu(
        items=services,
        title=f"[{cluster}]\nSelect service",
        clear_screen=True,
    )
    if ret[0] is None:
        return (None, *ret)
    return (cluster, *ret)


def get_task(ecs: session.Session.client, task: str, cluster: str, service: str):
    """
    get services
    """
    if not service:
        return cluster, service, None, None
    if task:
        return cluster, service, task, None
    print("fetching available tasks...")
    arns = ecs_paginator(
        ecs=ecs,
        paginator="list_tasks",
        leaf="taskArns",
        cluster=cluster,
        serviceName=service,
    )
    tasks = [task.split("/")[-1] for task in arns]
    ret = show_menu(
        items=tasks,
        title=f"[{cluster}|{service}]\nSelect task",
        clear_screen=True,
    )
    if ret[0] is None:
        return (cluster, None, *ret)
    return (cluster, service, *ret)


def get_container(cluster: str, service: str, task: str, containers: list, container: str):
    """
    get container
    """
    if container:
        return task, container, containers.index(container)
    ret = show_menu(
        items=containers,
        title=f"[{cluster}|{service}|{task}]\nSelect container",
        clear_screen=True,
    )
    if ret[0] is None:
        return (None, *ret)
    return (task, *ret)


def get_port(
    cluster: str,
    service: str,
    task: str,
    containers: list,
    container: str,
    ports: list,
    port: int,
):
    """
    get port
    """
    if port:
        return None, port, None
    ret = show_menu(
        items=ports,
        title=f"[{cluster}|{service}|{task}|{container}]\nSelect port",
        clear_screen=True,
    )
    if ret[0] is None:
        return (None, *ret)
    return (container, *ret)


def menu_loop_condition(cluster: str, service: str, task: str, container: str, remote_port: int, action: str):
    menu_loop_condition = cluster and service and task and container
    if action == "forward":
        menu_loop_condition = menu_loop_condition and remote_port
    return menu_loop_condition


def run():
    """main cli function"""
    parser = get_parser()
    arguments = parser.parse_args()
    boto3_session_args = {
        "region_name": arguments.region,
        "profile_name": arguments.profile,
    }
    boto3_session = session.Session(**boto3_session_args)
    ecs = boto3_session.client("ecs")
    command, remote_port, local_port = None, None, None
    if "command" in arguments:
        command = arguments.command
    if "remote_port" in arguments:
        remote_port = arguments.remote_port
    if "local_port" in arguments:
        local_port = arguments.local_port
    cluster, service, task, container, remote_port, task_definition = (
        arguments.cluster,
        arguments.service,
        arguments.task,
        arguments.container,
        remote_port,
        None,
    )
    try:
        while not menu_loop_condition(
            cluster=cluster,
            service=service,
            task=task,
            container=container,
            remote_port=remote_port,
            action=arguments.action,
        ):
            cluster, _ = get_cluster(ecs=ecs, cluster=cluster)
            cluster, service, _ = get_service(ecs=ecs, cluster=cluster, service=service)
            cluster, service, task, _ = get_task(ecs=ecs, cluster=cluster, service=service, task=task)
            if cluster and task:
                task_details = ecs.describe_tasks(cluster=cluster, tasks=[task])
                containers = [container.get("name") for container in task_details.get("tasks")[0].get("containers")]
                ret = get_container(
                    cluster=cluster,
                    service=service,
                    task=task,
                    containers=containers,
                    container=container,
                )
                task, container, container_index = ret
            if (arguments.action == "forward" and container) and not remote_port:
                task_definition_arn = task_details.get("tasks")[0].get("taskDefinitionArn")
                task_definition = task_definition or ecs.describe_task_definition(
                    taskDefinition=task_definition_arn
                ).get("taskDefinition")
                ports = []
                for _container in task_definition.get("containerDefinitions"):
                    if _container.get("name") == container:
                        ports = [
                            str(_port_mapping.get("containerPort")) for _port_mapping in _container.get("portMappings")
                        ]
                        break
                container, remote_port, _ = get_port(
                    cluster=cluster,
                    service=service,
                    task=task,
                    container=container,
                    containers=containers,
                    ports=ports,
                    port=remote_port,
                )
        ecs_session = ECSSession(
            cluster=cluster,
            boto3_session=boto3_session,
            command=command,
            container=container,
            container_index=container_index,
            local_port=local_port,
            remote_port=remote_port,
            task=task,
            task_details=task_details,
        )
        function = {
            "forward": ecs_session.port_forward,
            "command": ecs_session.execute_command,
        }
        print("---")
        print(f"cluster: {cluster}")
        print(f"service: {service}")
        print(f"task: {task}")
        print(f"container: {container}")
        print("---")
        function.get(arguments.action)()
    except exceptions.ClientError as err:
        print(err)
        sys.exit(1)


if __name__ == "__main__":
    run()
