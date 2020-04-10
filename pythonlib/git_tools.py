"""
Wrapper for interacting with Git
"""
import functools
import logging
import os

from git import GitCommandError
from git import NoSuchPathError
from git import Repo

from .custom_exception import CommonException

# Pulled from https://gitpython.readthedocs.io/en/stable/reference.html?highlight=FetchInfo
FETCH_CODES = {
    1: 'NEW_TAG',
    2: 'NEW_HEAD',
    4: 'HEAD_UP_TO_DATE',
    8: 'TAG_UPDATE',
    16: 'REJECTED',
    32: 'FORCED_UPDATE',
    64: 'FAST_FORWARD',
    128: 'ERROR'
}


class GitException(CommonException):
    """Generic Git exception class"""


# Decorator for checking that the local repo exists
def check_local_repository_exists(method):
    """Decorator for checking that the target repo exists and is accessible"""
    @functools.wraps(method)
    def _check_local_repository_exists_wrapper(self, *args, **kwargs):
        if not os.path.exists(self.repo_dir):
            raise GitException(f'The local repo path {self.repo_dir} does not exist or cannot be accessed by you.')
        return method(self, *args, **kwargs)
    return _check_local_repository_exists_wrapper


class GitTools:
    """Primary object for abstracting Git interactions"""

    def __init__(self, repo_dir, remote_name='origin'):
        self.repo_dir = os.path.relpath(repo_dir)
        self.remote_name = remote_name

        try:
            self.repo = Repo(repo_dir)
            self.git_repo = self.repo.git
            self.remote = self.repo.remote(self.remote_name)
        except NoSuchPathError:
            self.repo = None

    @check_local_repository_exists
    def checkout_branch(self, branch_name, create_branch=False):
        """Checks out a branch in Git.

        Checkout the given branch name in the Git repository. Operation will fail if the
        branch does not exist unless `create_branch=True`.

        :param branch_name:     Name of the Git branch to checkout
        :type branch_name:      str
        :param create_branch:   (Optional) Creates the branch if it does not exist
        :type create_branch:    bool
        :return:                Name of the branch that was checked out
        :rtype:                 str
        """
        logging.info(f'Checking out the {branch_name} branch')

        if self.current_branch() == branch_name:
            logging.info('Already on the requested branch')
        else:
            # Try to checkout the given branch name
            for branch in self.repo.heads:
                if str(branch) == branch_name:
                    branch.checkout()
                    break

            # Check to make sure we are on the target branch
            if self.current_branch() != branch_name:
                if create_branch:
                    logging.info('Branch does not exist locally; creating it...')
                    new_branch = self.repo.create_head(branch_name)
                    new_branch.checkout()
                else:
                    raise GitException('Branch does not exist!')

        return branch_name

    def clone_repo(self, start_tag, end_tag, repo_url, diff=False):
        """Clones a remote repository locally.

        Clone a remote repository locally and then performs a diff of the repository's contents
        between two tags (`start_tag` and `end_tag`) if `diff` is set to True, otherwise None

        :param start_tag:   Starting tag to use when performing the git diff
        :type start_tag:    str
        :param end_tag:     Ending tag to use when performing the git diff
        :type end_tag:      str
        :param repo_url:    Repository URL to clone from
        :type repo_url:     str
        :param diff:        Whether or not to actually perform the git diff
        :type diff:         bool
        :return:            A tuple containing the repo object, git object, and the diff_result
        :rtype:             tuple
        """
        self.repo = Repo.clone_from(repo_url, self.repo_dir)
        diff_result = None if not diff else self.get_repo_diff(start_tag, end_tag)

        return self.repo, diff_result

    def get_repo_diff(self, start_tag, end_tag):
        """ Perform a file-name-only diff report of a Git repo between two commits

        :param start_tag:   The commit hash or tag to start the diff from
        :type start_tag:    str
        :param end_tag:     The end hash or tag to diff with `start_tag`
        :type end_tag:      str
        :return:            A \n-delimited string containing the file names changed between `start_tag` and `end_tag`
        :rtype:             str
        """
        self.repo.git.fetch(all=True, tags=True)
        self.repo.git.pull()
        return self.repo.git.diff(start_tag, end_tag, name_only=True, ignore_space_at_eol=True, b=True, w=True)

    @check_local_repository_exists
    def current_branch(self):
        """Get the name of the current branch.

        Returns the name of the currently checked out branch for the given local Git repository.

        :return:    Name of the current branch
        :rtype:     str
        """
        return str(self.repo.active_branch)

    @check_local_repository_exists
    def delete_branch(self, branch_name, local=True, remote=False):
        """Delete a branch in a Git repository.

        Deletes a branch in the Git repository. The `local` and `remote` flags determine
        whether to delete the branch locally, on the remote, or both.

        Some errors will not cause an exception to be raised. For example, if this method
        is called to delete a branch locally and remotely and the branch does not exist
        on the remote, a warning will be logged but no exception thrown.

        :param branch_name: Name of the branch to delete
        :type branch_name:  str
        :param local:       Set to `True` to delete the branch locally
        :type local:        bool
        :param remote:      Set to `True` to delete the branch on the remote repository
        :type remote:       bool
        :return:            Name of the branch that was deleted or None if no branch was deleted.
        :rtype:             str or None
        """
        logging.info(f'Deleting branch {branch_name}')
        branch_deleted = None

        if local:
            logging.info('Deleting the local branch')
            # Can't delete the local branch if we're on it
            if self.current_branch() == branch_name:
                self.checkout_branch(branch_name)

            gitobj = self.repo.git

            try:
                result = gitobj.branch('-d', branch_name)
                branch_deleted = branch_name
                logging.info(result)
            except GitCommandError as gce:
                logging.exception(gce)

        if remote:
            logging.info('Deleting the remote branch')
            remote_branch_name = f'{self.remote_name}/{branch_name}'

            for branch in self.repo.refs:
                if branch.name == remote_branch_name:
                    logging.info(f'Deleting remote branch {branch.name}')
                    self.remote.push(refspec=f':{remote_branch_name}')

        return branch_deleted

    @check_local_repository_exists
    def list_branches(self, safe_checking=True):
        """List the local and remote branches in the local repository.

        Returns a list of all of the local and remote branches in a given local Git repository.
        It's advisable to use `checkout_branch` to checkout the dev branch, then call `update_repo` to
        retrieve the most current refs from the remote repository, then call this function. As a
        shortcut to this, you can set `safe_checking=True` which will do this for you, and then
        checkout the original branch. If the repository already has dev or master checked out, then
        the branch checked out will not change.

        :param safe_checking:   If set to `True`, then will checkout the dev branch and do a 'git pull' before
                                getting the branch list so the local repo has all of the current refs.
        :type safe_checking:    bool
        :return:                Dictionary containing two keys, `local` and `remote`. The values for the keys
                                are lists of the branch names.
        :rtype:                 dict
        """
        logging.info(f'Getting list of all branches in {self.repo_dir}')
        starting_branch = self.current_branch()
        local_branches = set()
        remote_branches = set()

        if safe_checking:
            if self.current_branch not in ('master', 'dev'):
                self.update_repo(branch_name='dev')
            else:
                self.update_repo()

        for ref in self.repo.refs:
            ref = ref.name

            if 'HEAD' in ref:
                pass
            elif ref.startswith('origin'):
                remote_branches.add(ref.replace('origin/', ''))
            else:
                local_branches.add(ref)

        if safe_checking:
            self.checkout_branch(starting_branch)

        return {'local': local_branches, 'remote': remote_branches}

    @check_local_repository_exists
    def update_repo(self, branch_name=None):
        """Perform a `git pull` on the local repository.

        Performs a `git pull` to fetch any new changes from the remote repository.

        :param branch_name: If given this branch will be checked out before the pull operation is performed.
        :type branch_name:  str
        :return:            True for success, False for failure
        :rtype:             bool
        """
        logging.info(f'Updating the repo...')
        pull_data = None

        if branch_name:
            branch = self.checkout_branch(branch_name)
        else:
            branch = self.current_branch()

        fetch_data = self.remote.pull()

        for data in fetch_data:
            if str(data.ref).endswith(branch):
                pull_data = data
                break

        if pull_data.flags == 128:
            raise GitException(f'Error pulling updates from the remote! Info from git: {pull_data.note}')

        logging.info(f'Result of pull operation: {FETCH_CODES[pull_data.flags]}')

        return True

    @check_local_repository_exists
    def commit_to_branch(self, file_list, message, branch_name=None):
        """Commit the given files to the Git repo."""
        if branch_name:
            self.checkout_branch(branch_name)
        else:
            branch_name = self.current_branch

        logging.info(f'Committing to {branch_name}: {message}')
        logging.debug(f'List of files to commit: {file_list}')
        # TODO: Implement the add and commit methods
        # self.git.add(file_list)
        # self.git.commit(message)
