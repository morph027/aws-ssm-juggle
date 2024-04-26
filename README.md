# aws-ssm-juggle

## Installation

```
pip install aws-ssm-juggle
```

## Pre-requisites

### [session-manager-plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)

#### Linux

```bash
curl https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb -o "/tmp/session-manager-plugin.deb"
mkdir -p ~/bin
dpkg-deb --fsys-tarfile /tmp/session-manager-plugin.deb | tar --strip-components=4 -C ~/bin/ -xvf - usr/local/sessionmanagerplugin/bin/session-manager-plugin
```

#### MacOS

`brew install --cask session-manager-plugin`

### Infrastructure

Use [ecs-exec-checker](https://github.com/aws-containers/amazon-ecs-exec-checker) to check for the pre-requisites to use ECS exec.

## ecs-juggle

Inspired by [ecsgo](https://github.com/tedsmitt/ecsgo) (`ecspy` is in use already).

Provides a tool to interact with AWS ECS tasks.

Currently provides:

* interactive execute-command (e.g. shell)
* port-forwarding

You can supply command-line arguments to specify which cluster/service/task/... to use or will be prompted with a nice menu.


### Usage

See `ecs-juggle --help` for all features.

#### Execute command

Select all from menu:

```bash
ecs-juggle command
```

#### Port forwarding

Select all from menu:

```bash
ecs-juggle forward
```

Specify port and select the rest from menu:

```bash
ecs-juggle --remote-port 8080 forward
```
