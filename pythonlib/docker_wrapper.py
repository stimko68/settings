"""
Abstract interacting with Docker
"""
import os
import socket

import docker


CLIENT = docker.APIClient(base_url='unix://var/run/docker.sock')


class DockerException(Exception):
    """Custom exception for Docker errors"""


def get_current_container():
    """Get the hostname for the current container"""
    return socket.gethostname()


def get_host_volume_mount(container_path, sudo):
    """
    Retrieve the host volume that is mounted to the container at the container_path
    that is given. The result is a host centric path to the files in the container_path.
    This involves walking up the directory structure of the container_path until
    there's a matching volume mount from the docker inspect command.

    Ex docker run:
    docker run -v /my-host-volume/data:/workspace/my/important/file.txt busybox

    The host volume mount to file.txt would be:
    /my-host-volume/data/my/important/file.txt
    """
    return_path = None

    if container_path and container_path != '/':
        host_path = get_host_path_for_mount(container_path, sudo)
        if host_path:
            return_path = host_path

        # Move up one directory and try to match again
        mount = get_host_volume_mount(os.path.dirname(container_path), sudo)
        if mount:
            # Up the stack, add the paths back to the source mount.
            return_path = os.path.join(mount, os.path.basename(container_path))

    return return_path


def get_host_path_for_mount(container_path, sudo):  # pylint: disable=unused-argument
    """
    Search the docker inspect output for mounts that match
    the container_path.
    This probably only works on Docker 1.13 or 17.X or later versions, when they
    changed the inspect spec from 'volumes' to 'Mounts'.
    """
    mounts = CLIENT.inspect_container(get_current_container()).get('Mounts', [])

    for mount in mounts:
        if container_path == mount['Destination']:
            return mount['Source']
    return None
