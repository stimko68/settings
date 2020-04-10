"""
Module for abstracting interactions with Artifactory
"""
from .__init__ import *

from .checksum import generate_checksum
from .string_helper import remove_from_start_if_present

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


DEFAULT_ARTIFACTORY_URL = ''


class ArtifactoryRequestException(Exception):
    pass


class Artifactory(object):
    storage_api = '/api/storage'
    aql_api = '/api/search/aql'

    def __init__(self, artifactory_url=DEFAULT_ARTIFACTORY_URL, api_token=None):
        self.artifactory_url = artifactory_url

        if not self.artifactory_url:
            raise Exception('No Artifactory URL found! Aborting')

        self.api_token = api_token

        if self.api_token is None:
            env_api_token = os.environ.get('ARTIFACTORY_API_TOKEN')
            if env_api_token:
                self.api_token = env_api_token

        if not self.api_token:
            logging.warning('NO ARTIFACTORY API KEY WAS PROVIDED! SOME REQUESTS MAY FAIL!')

        self.session = requests.session()

    def _cleanup_url(self, url):
        """Cleans up the URL string before the request is processed.

        This helper method is designed to clean up the URL by removing unwanted elements. For example,
        if the url string already starts with the Artifactory URL then it is not added, but if it's
        missing then it is.

        :param url: URL to process
        :type url:  str
        :return:    Cleaned string that's ready for the request object to process
        :rtype:     str
        """
        logging.debug(f'URL provided: {url}')

        if url.startswith(self.artifactory_url):
            url = url.replace(self.artifactory_url, '')

        url = remove_from_start_if_present(url, '/')
        url = os.path.join(self.artifactory_url, url)

        logging.debug(f'URL after cleanup: {url}')

        return url

    def _request_wrapper(self, request_type, uri, **request_headers):
        """Wrapper around making HTTP requests.

        Abstracts making HTTP requests so that the requests are made in a consistent manner and other code
        in this library is more DRY.

        :param request_type:    Type of HTTP request (e.g., GET, POST, PUT, etc)
        :type request_type:     str
        :param uri:             URI where to make the request. The base Artifactory URL will be added.
        :type uri:              str
        :param request_headers: Additional headers that should be tacked onto the request.
        :return:                HTTP response object
        :rtype:                 requests.models.Response
        """
        headers = {
            'X-JFrog-Art-Api': self.api_token
        }

        if request_headers:
            headers.update(**request_headers)

        # Check for a data entry, which means the request is a file upload
        # If the data key is present, then remove it from the dictionary object
        file_data = headers.pop('data', None)

        # Check for any non-string values in the headers dict
        for key, value in headers.items():
            if type(value) in (bool, int, float):
                headers[key] = str(value)

        url = self._cleanup_url(uri)

        logging.debug(f'Making a {request_type.upper()} request to {url}')

        request_obj = getattr(self.session, request_type.lower())

        response_obj = request_obj(url, data=file_data, headers=headers, verify=False)

        if not str(response_obj.status_code).startswith('2'):
            response_obj.raise_for_status()

        return response_obj

    # HTTP abstraction methods
    def get(self, uri, **request_headers):
        """Wrapper around HTTP GET.

        Abstraction of calling session.get().

        :param uri:             URI of the HTTP request
        :type uri:              str
        :param request_headers: Optional additional headers to pass with the HTTP request.
        :return:                HTTP response object
        :rtype:                 requests.models.Response
        """
        return self._request_wrapper('get', uri, **request_headers)

    def post(self, uri, **request_headers):
        """Wrapper around HTTP POST.

        Abstraction of calling session.post().

        :param uri:             URI of the HTTP request
        :type uri:              str
        :param request_headers: Optional additional headers to pass with the HTTP request.
        :return:                HTTP response object
        :rtype:                 requests.models.Response
        """
        return self._request_wrapper('post', uri, **request_headers)

    def put(self, uri, **request_headers):
        """Wrapper around HTTP PUT.

        Abstraction of calling session.put().

        :param uri:             URI of the HTTP request
        :type uri:              str
        :param request_headers: Optional additional headers to pass with the HTTP request.
        :return:                HTTP response object
        :rtype:                 requests.models.Response
        """
        return self._request_wrapper('put', uri, **request_headers)

    def delete(self, uri, **request_headers):
        """Wrapper around HTTP DELETE.

        Abstraction of calling session.delete().

        :param uri:             URI of the HTTP request
        :type uri:              str
        :param request_headers: Optional additional headers to pass with the HTTP request.
        :return:                HTTP response object
        :rtype:                 requests.models.Response
        """
        return self._request_wrapper('delete', uri, **request_headers)

    def file_exists(self, repository_name, file_name, return_extra_data=False):
        """Check that a file exists in Artifactory.

        Checks that a file exists in Artifactory. Returns a boolean indicating whether or not the file exists.

        If `return_extra_data=True` here is a sample of the metadata dict object returned:

        {
            "repo" : "conit-file-local",
            "path" : "/docker-compose/1.20.1/docker-compose-Linux-x86_64",
            "created" : "2018-04-02T21:23:22.626Z",
            "createdBy" : "admin",
            "lastModified" : "2018-04-02T21:23:13.000Z",
            "modifiedBy" : "admin",
            "lastUpdated" : "2018-04-02T21:23:13.000Z",
            "downloadUri" : "https://conitartifactory.edc.ds1.usda.gov/artifactory/conit-file-local/docker-compose/1.20.1/docker-compose-Linux-x86_64",
            "mimeType" : "application/octet-stream",
            "size" : "10850496",
            "checksums" : {
              "sha1" : "12e68161e7c35136758d87e511fbb8107097a8fa",
              "md5" : "7f5e10990994efbcc55c253c404112d0",
              "sha256" : "11a6923c2a589b946598fe205c8f645e57f3f4ee153d3b7315b7e1993c1b2ad1"
            },
            "originalChecksums" : {
              "sha1" : "12e68161e7c35136758d87e511fbb8107097a8fa",
              "md5" : "7f5e10990994efbcc55c253c404112d0",
              "sha256" : "11a6923c2a589b946598fe205c8f645e57f3f4ee153d3b7315b7e1993c1b2ad1"
            },
            "uri" : "https://conitartifactory.edc.ds1.usda.gov/artifactory/api/storage/conit-file-local/docker-compose/1.20.1/docker-compose-Linux-x86_64"
        }

        :param repository_name:     Artifactory repository name (e.g., conit-file-local)
        :type: repository_name:     str
        :param file_name:           Name of the file to download. If the file is in a subdirectory in the repository
                                    then the file name should include the path (e.g., path/to/file.txt)
        :type file_name:            str
        :param return_extra_data:   (Optional) Set this to `True` if you want extra metadata returned instead of just
                                    a boolean if the file exists in Artifactory. The extra metadata returned is the
                                    headers from the Artifactory HTTP response.
        :type return_extra_data:    bool
        :return:                    True if the file exists and False if it does not, or a dict object containing the
                                    headers from the Artifactory HTTP response.
        :rtype:                     bool or dict
        """
        logging.info(f'Checking for the existence of {file_name}')

        url_path = os.path.join(self.storage_api, repository_name, file_name)
        logging.debug(f'url_path: {url_path}')

        response = self.get(url_path)

        if return_extra_data:
            return json.loads(response.text)
        else:
            return response.status_code == 200

    def retrieve_file(self, repository_name, file_name, local_file=None, return_extra_data=False):
        """Download a file from Artifactory.

        Downloads a file from Artifactory given the repository name, file name, and the local path where the
        file should be saved. If the local path (`local_file`) isn't provided then the remote filename is used
        and saved in the current working directory.

        :param repository_name:     Artifactory repository name (e.g., conit-file-local)
        :type: repository_name:     str
        :param file_name:           Name of the file to download. If the file is in a subdirectory in the repository
                                    then the file name should include the path (e.g., path/to/file.txt)
        :type file_name:            str
        :param local_file:          (Optional) Local filename and path to where the file should be saved. If nothing is
                                    provided then the file will be saved using the remote filename to the current
                                    directory. Paths provided can be relative but MUST end in the filename!
        :param return_extra_data:   (Optional) Set this to `True` if you want extra metadata returned in addition to
                                    the path where the file was saved. The extra metadata is the headers returned by
                                    Artifactory when the file is successfully downloaded.
        :type return_extra_data:    bool
        :return:                    Location where the file was downloaded
        :rtype:                     str or tuple(str, dict)
        :raises:                    ArtifactoryRequestException
        """
        artifactory_path = f'{self.artifactory_url}/{repository_name}/{file_name}'

        logging.info(f'Downloading file from {artifactory_path}')

        if not local_file:
            local_file = os.path.join(os.getcwd(), file_name.split('/')[-1])
        else:
            local_file = os.path.abspath(local_file)

        response = self.get(f'{repository_name}/{file_name}', stream=True)

        try:
            provided_md5 = response.headers['X-Checksum-Md5']

            with open(local_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            logging.info('Validating downloaded file...')

            downloaded_md5 = generate_checksum(local_file, 'md5')

            if provided_md5 != downloaded_md5:
                raise ArtifactoryRequestException(f'Download failed! The downloaded file\'s checksum ({downloaded_md5}) does not match '
                                                  f'what was provided by Artifactory ({provided_md5})')

        except OSError as ose:
            logging.exception(ose)
            raise ArtifactoryRequestException(ose)

        logging.info(f'File saved to {local_file}')

        if return_extra_data:
            return local_file, response.headers
        else:
            return local_file

    def upload_file(self, repository_name, file_name, local_file):
        """Upload a local file to Artifactory.

        Uploads a local file to Artifactory. Does the work of calculating the file checksums and pushing the
        file to the requested repository. If you want the file to be uploaded to a specific path in the given
        repository then that path needs to be provided as part of the `file_name` parameter.

        :param repository_name: Artifactory repository name (e.g., conit-file-local)
        :type: repository_name: str
        :param file_name:       Name and path of the file in the remote repository. For example, if uploading the
                                file `blerg.txt` then this parameter could be `path/to/blerg.txt`. If just the file
                                name is provided then the file will be uploaded to the root of the given repository.
        :param local_file:      Path to the local file to be uploaded. The path can be relative to the current
                                working directory. If no path is provided it is assumed to be the current working
                                directory. The path MUST include the filename!
        :return:                Full path to the remote file once the upload is complete.
        :rtype:                 str
        """
        local_file = os.path.abspath(local_file)

        logging.info(f"Uploading file {local_file}")

        if not os.path.exists(local_file):
            raise OSError(f'The given file at {local_file} does not exist or is not accessible by the current user.')

        # Generate the checksums for the file
        upload_headers = {
            'X-Checksum-Md5': generate_checksum(local_file, 'md5'),
            'X-Checksum-Sha1': generate_checksum(local_file, 'sha1'),
            'X-Checksum-Sha256': generate_checksum(local_file, 'sha256')
        }

        url_path = os.path.join(repository_name, file_name)

        with open(local_file, 'rb') as f:
            upload_headers['data'] = f
            response = self.put(url_path, **upload_headers)

        upload_location = response.headers['Location']

        logging.info(f'File successfully uploaded to {upload_location}')

        return upload_location

    def aql_query(self, aql, encoding='UTF-8'):
        """
        Executes an arbitrary AQL query against the Artifactory AQL API

        :param aql:         The AQL string representing the query to run
        :type aql:          str
        :param encoding:    The encoding used to decode the response
        :type encoding:     str
        :return:            A JSON object representing the query result
        :rtype:             json
        """
        try:
            response = self.post(self.aql_api, data=aql)
            result = json.loads(response.content.decode(encoding))
            return result
        except Exception as e:
            logging.exception(e)
