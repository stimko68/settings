#!/usr/bin/env python3
"""
Wrapper around calling oc commands
"""
from .__init__ import *

from kubernetes import client
from kubernetes.stream import stream
from openshift.dynamic import DynamicClient
from openshift.dynamic import exceptions

from .custom_exception import CommonException
from .log import setup_logging


urllib3.disable_warnings()


class OpenShiftException(CommonException):
    pass


class OC(object):

    def __init__(self, log_domain='', namespace='default', cluster='dev'):
        self.log_domain = log_domain
        self.log = setup_logging(self.log_domain)

        self.target_cluster = cluster
        self.clusters = {
            'dev': {
                'url': '',
                'token': r'',
            },
            'prod': {
                'url': '',
                'token': '',
            }
        }

        self.namespace = namespace

        self.k8s = None
        self.dyn_client = None
        self.corev1api = None
        self.login()

    def _get_wrapper(self, resource_name, api_version='v1', name_filter_string=None, namespace=None, return_object=False):
        """Wrapper around retrieving data on resources.

        Provides a generic way for other get methods to make simple resource requests.

        :param api_version:         Kubernetes API version to use when making the API call. This may
                                    be different depending on the resource being accessed. Defaults to 'v1'.
        :type api_version:          str
        :param name_filter_string:  String to use to filter the results results by. The string will be used
                                    to filter the results by the `['metadata']['name']` field in each dict.
        :type name_filter_string:   str
        :param resource_name:       Name of the resource to retrieve. Examples are 'Service', 'Pod',
                                    'Deployment', etc. These are names of OpenShift  resource objects.
        :type resource_name:        str
        :param return_object:       Use this option to skip any processing and only return the resource type
                                    object. This is required to perform certain operations such as patching.
        :type return_object:        bool
        :return:                    List of dictionary objects containing the results, or a `openshift.dynamic.client.Resource`
                                    object.
        :rtype:                     list or openshift.dynamic.client.Resource
        """
        if not namespace:
            namespace = self.namespace

        data = self.dyn_client.resources.get(api_version=api_version, kind=resource_name)

        if return_object:
            return_data = data
        else:
            return_data = data.get(namespace=namespace)

            if name_filter_string:
                new_return_data = list()

                for d in return_data['items']:
                    if name_filter_string in d['metadata']['name']:
                        new_return_data.append(d)

                return_data['items'] = new_return_data

        return return_data

    def login(self, cluster=None):
        """Log into the given OpenShift cluster.

        Logs into the given OpenShift cluster; similar to `oc login`.

        :param cluster: Name of the cluster to log into (e.g., 'dev' or 'training')
        :type cluster:  str
        :return:        0 for success, 1 for failure
        """
        if cluster:
            self.target_cluster = cluster

        k8s_cfg = client.Configuration()
        k8s_cfg.host = self.clusters[self.target_cluster]['url']
        k8s_cfg.api_key = {"authorization": f"Bearer {self.clusters[self.target_cluster]['token']}"}
        k8s_cfg.verify_ssl = False

        self.k8s = client.ApiClient(k8s_cfg)
        self.corev1api = client.CoreV1Api(self.k8s)
        self.dyn_client = DynamicClient(self.k8s)

        return 0

    def exec(self, pod_name, command, namespace=None):
        """Run a command inside a pod.

        Executes the given bash command inside the target pod. Similar to using `oc exec`. Does not invoke a shell
        when executing so certain variables like pipes (`|`) won't work. The command can be in the form of a string
        (e.g., `"/bin/bash -c ls /"`) or a list format for commands, which is preferred (e.g.,
        `["/bin/bash", "-c", "ls", "/"]`).

        Code examples from https://github.com/kubernetes-client/python/blob/master/examples/exec.py

        :param pod_name:    Name of the pod to execute the command inside of.
        :type pod_name:     str
        :param command:     Command to run inside of the target container. Can be provided as a string or list.
        :type command:      str or list
        :param namespace:   Namespace to execute the command in.
        :type namespace:    str
        :return:
        """
        if not namespace:
            namespace = self.namespace

        if type(command) == str:
            command = command.split(' ')

        exec_options = {
            'command': command,
            'stdin': True,
            'stdout': True,
            'stderr': True,
            'tty': False,
            '_preload_content': False
        }

        response = stream(self.corev1api.connect_get_namespaced_pod_exec, pod_name, namespace, **exec_options)

        while response.is_open():
            response.update(timeout=1)

            if response.peek_stdout():
                self.log.info(response.read_stdout())

            if response.peek_stderr():
                self.log.error(response.read_stderr())

            if command:
                cmd = command.pop(0)
                self.log.info(f'Executing command: {cmd}')
                response.write_stdin(f'{cmd}\n')
            else:
                break

    def get_deployments(self, namespace=None, deployment_name=None):
        """Get a list of deployment objects.

        Returns a list of deployment objects in the given namespace. The results can be filtered by
        providing a full or partial deployment name.

        :param deployment_name: Full or partial name of a deployment to filter results by
        :type deployment_name:  str
        :param namespace:       Namespace to execute the command in.
        :type namespace:        str
        :return:                List of dicts containing the deployment object descriptions
        :rtype:                 list
        """
        deployments = self._get_wrapper('Deployment', namespace=namespace, name_filter_string=deployment_name)

        return deployments

    def get_deployment_configs(self, namespace=None, deployment_name=None):
        """Get a list of deployment config objects.

        Returns a list of deployment config objects in the given namespace. The results can be filtered by
        providing a full or partial deployment name.

        :param deployment_name: Full or partial name of a deployment to filter results by
        :type deployment_name:  str
        :param namespace:       Namespace to execute the command in.
        :type namespace:        str
        :return:                List of dicts containing the deployment object descriptions
        :rtype:                 list
        """
        deployment_configs = self._get_wrapper('DeploymentConfig', api_version='apps.openshift.io/v1', namespace=namespace, name_filter_string=deployment_name)

        return deployment_configs

    def get_pods(self, namespace=None, filter_name=None):
        """Get a list of running pods.

        Returns a list of running pods in the given namespace. If a filter name is provided only
        the pods that contain that string will be returned. If you ask for a filtered list then you
        will get a list of dict objects; otherwise you get a `kubernetes.client.models.v1_pod_list.V1PodList`
        object.

        :param namespace:       Namespace to execute the command in.
        :type namespace:        str
        :param filter_name:     Full or partial name of a pod to filter the results by
        :type filter_name:      str
        :return:                List of dicts containing the pod object descriptions or a
                                `kubernetes.client.models.v1_pod_list.V1PodList` object.
        :rtype:                 list or kubernetes.client.models.v1_pod_list.V1PodList
        """
        if not namespace:
            namespace = self.namespace

        pods = self.corev1api.list_namespaced_pod(namespace)

        if filter_name:
            original_pods = pods.to_dict()['items']
            new_pods = list()

            for pod in original_pods:
                if filter_name in pod['metadata']['name']:
                    new_pods.append(pod)

            pods = new_pods

        return pods

    def get_projects(self, project_name=None):
        """Get the list of projects.

        Returns a list of projects in the OpenShift cluster. The results can be filtered by providing a
        full or partial project name.

        :param project_name:    (Optional) Provide a project name to only return results for
                                that project.
        :type project_name:     str
        :return:                List of dicts containing the project object descriptions
        :rtype:                 list
        """
        return self._get_wrapper('Project', api_version='project.openshift.io/v1', name_filter_string=project_name)

    def get_services(self, namespace=None, service_name=None):
        """Get a list of services.

        Returns a list of the services in the given namespace. The results can be filtered by providing a
        full or partial service name.

        :param namespace:       Namespace to execute the command in.
        :type namespace:        str
        :param service_name:    Filter the results by providing the full or partial name of a service
        :type service_name:     str
        :return:                List of dicts containing the service object descriptions
        :rtype:                 list
        """
        return self._get_wrapper('Service', namespace=namespace, name_filter_string=service_name)

    def scale_deployment(self, deployment_name, replicas, deployment_type='Deployment', namespace=None):
        """Scale a deployment up or down.

        Scales the given deployment name to the value passed to `replicas`.

        :param deployment_name: Name of the deployment to scale.
        :type deployment_name:  str
        :param replicas:        Number of replicas to scale the deployment to.
        :type replicas:         int
        :param deployment_type: Type of object to look for. In general this will be `Deployment` objects
                                but in some cases you may need to scale `DeploymentConfig` objects.
        :type deployment_type:  str
        :param namespace:       Namespace to execute the command in.
        :type namespace:        str
        :return:                0 for success, 1 for failure
        :rtype:                 int
        """
        if not namespace:
            namespace = self.namespace

        obj = self._get_wrapper(deployment_type, namespace=namespace, return_object=True)

        patch_body = {
            "metadata": {
                "name": deployment_name
            },
            "spec": {
                "replicas": replicas
            }
        }

        try:
            obj.patch(patch_body, namespace=namespace)
            return 0
        except exceptions.NotFoundError as e:
            self.log.exception(e)
            return 1

    def switch_namespace(self, namespace):
        """Switch commands to use a different namespace.

        Switch to a different namespace, which will control the namespace that each command runs against.

        :param namespace:   Name of the namespace to switch to
        :type namespace:    str
        :return:            None
        :rtype:             None
        """
        self.namespace = namespace
