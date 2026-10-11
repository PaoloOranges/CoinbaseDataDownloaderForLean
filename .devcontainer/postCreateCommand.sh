#!/bin/bash
set -e

# Install Homebrew
CI=true /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Configure Homebrew PATH in bashrc
echo >> /root/.bashrc
echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"' >> /root/.bashrc
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"

# Install Homebrew dependencies
sudo apt-get install -y build-essential

# Install GCC and rtk
brew install gcc
brew install rtk

# Configure rtk globally
rtk init --copilot

# Install Python requirements
pip3 install --upgrade pip
pip3 install --user -r requirements.txt
