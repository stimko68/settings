#!/bin/bash
# Setup script for fresh OS install

if [[ "$EUID" -ne 0 ]]; then
    echo "Script must be run as root!"
    exit 1
fi

echo "Enable nopasswd for sudo"
sudo sed -i "s/\%sudo.*/\%sudo ALL=\(ALL\) NOPASSWD:ALL/" /etc/sudoers 

echo ""
echo "Adding oranchelo icon theme PPA"
sudo add-apt-repository -y ppa:oranchelo/oranchelo-icon-theme

echo ""
echo "Installing packages"
sudo apt install oranchelo-icon-theme vim git

echo ""
echo "Set VIM as the default editor"
sudo update-alternatives --set editor /usr/bin/vim.tiny 

echo ""
echo "Setting up config files"
cp -f .gitconfig .vimrc ~/
mkdir ~/tmp

echo ""
echo "Tilix config"
sudo ln -s /etc/profile.d/vte-2.91.sh /etc/profile.d/vte.sh
echo "$(cat .bashrc)" >> ~/.bashrc
echo "You must import the Tilix config file manually"

echo ""
echo "+-------------------- Done --------------------+"
