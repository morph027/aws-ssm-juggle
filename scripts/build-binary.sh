#!/usr/bin/env bash
# Build standalone linux binaries of ec2-juggle and ecs-juggle using nuitka.
# Usage: scripts/build-binary.sh [ec2-juggle|ecs-juggle ...]  (default: both)
# Output: dist/linux/<platform>/<command> and dist/linux/<platform>/<command>_<arch>
set -e

if [ "${DEBUG:-0}" -eq 1 ]; then
    set -x
fi

NUITKA_VERSION="${NUITKA_VERSION:-4.3}"
declare -A modules=(
    ["ec2-juggle"]="aws_ssm_juggle.ec2"
    ["ecs-juggle"]="aws_ssm_juggle.ecs"
)
if [ "$#" -eq 0 ]; then
    set -- ec2-juggle ecs-juggle
fi
for command in "$@"; do
    if [ -z "${modules[${command}]:-}" ]; then
        echo "Unknown command: ${command} (expected one of: ${!modules[*]})"
        exit 1
    fi
done

deps=()
for dep in patchelf gcc ccache curl; do
    if ! command -v "${dep}" >/dev/null 2>&1; then
        deps+=("${dep}")
    fi
done
if [[ -n "${deps[*]}" ]]; then
    echo "Installing dependencies (${deps[*]})"
    if [ "${EUID}" -ne 0 ]; then
        cmd=("sudo")
    else
        cmd=()
    fi
    # shellcheck source=/dev/null
    . /etc/os-release
    case "${ID}" in
    fedora)
        cmd+=("dnf" "-y")
        deps+=("libatomic-static")
        ;;
    debian | ubuntu)
        cmd+=("apt-get" "-y")
        "${cmd[@]}" update
        ;;
    esac
    "${cmd[@]}" install "${deps[@]}"
fi

arch="$(uname -m)"
case "${arch}" in
"aarch64")
    platform="linux/arm64"
    smp_arch="ubuntu_arm64"
    ;;
"x86_64")
    platform="linux/amd64"
    smp_arch="ubuntu_64bit"
    ;;
*)
    echo "Unsupported architecture: ${arch}"
    exit 1
    ;;
esac

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

python3 -m venv "${tmpdir}/venv"
"${tmpdir}/venv/bin/pip" install --quiet --upgrade pip
"${tmpdir}/venv/bin/pip" install --quiet . "nuitka==${NUITKA_VERSION}" zstandard

mkdir -p "dist/${platform}"

# smoke test: aws_ssm_juggle exits on import if session-manager-plugin is missing
if ! command -v session-manager-plugin >/dev/null 2>&1; then
    curl -sSfL -o "${tmpdir}/smp.deb" \
        "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/${smp_arch}/session-manager-plugin.deb"
    mkdir -p "${tmpdir}/bin"
    dpkg-deb --fsys-tarfile "${tmpdir}/smp.deb" |
        tar --strip-components=4 -C "${tmpdir}/bin" -xf - usr/local/sessionmanagerplugin/bin/session-manager-plugin
    export PATH="${tmpdir}/bin:${PATH}"
fi
for command in "$@"; do
    echo -e "from ${modules[${command}]} import run\n\nrun()" >"${tmpdir}/cli.py"
    "${tmpdir}/venv/bin/python" -m nuitka \
        --onefile \
        --assume-yes-for-downloads \
        --remove-output \
        --output-dir="${tmpdir}/build" \
        -o "${PWD}/dist/${platform}/${command}" \
        "${tmpdir}/cli.py"
    "dist/${platform}/${command}" --help
    cp "dist/${platform}/${command}" "dist/${platform}/${command}_${arch}"
done
