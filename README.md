[![pipeline status](https://gitlab.com/simko33f/settings/badges/master/pipeline.svg)](https://gitlab.com/simko33f/settings/-/commits/master)

# NAS Settings
This repo is a backup of settings files I use for my Linux installs. It also contains a setup script for new Linux installs.

# Setup
Before running the setup script this repository must be cloned, so follow these steps:
1. Install git
    ```
    sudo apt update && sudo apt install git
    ```

2. Generate an SSH keypair and add it to GitHub
    ```
    ssh-keygen
    ```

3. Clone this repository
    ```
    git clone git@gitlab.com:simko33f/settings.git 
    ```

4. Setup a virtualenv
    ```
    mkvirtualenv --python=3 settings
    ```
    
4. Run the setup script
    ```
    sudo ./setup.sh
    ```

# Testing
Use the following command to run tests locally. It requires Docker and make:

    make test
