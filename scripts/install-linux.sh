#!/bin/bash

#!/bin/bash

install_dir="${HOME}/.figgy/installations/first"

# Linux Example (change download URL for MacOs)
echo "Installing figgy in directory: ${install_dir}"
mkdir -p ${install_dir}

# Download Figgy
echo "Downloading..."
cd ${install_dir} && curl -s https://www.figgy.dev/releases/cli/latest/linux/figgy.zip > figgy.zip

# Unzip Figgy
echo "Unzipping..."
unzip figgy.zip > /dev/null

