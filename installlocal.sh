#!/bin/bash
WEB_PATH="https://raw.githubusercontent.com/williamwutq/sheepshaver/main"
SHARE_TYPE="python"

if [ "$SHARE_TYPE" == "python" ]; then
    EXECUTABLE_PATH="share.py"
fi

# Verify existance of EXECUTABLE_PATH and share.1
if [ ! -f "$EXECUTABLE_PATH" ]; then
    echo "Error: $EXECUTABLE_PATH not found. Installing from the web? [y/n]"
    read -r response
    if [[ "$response" == "y" || "$response" == "Y" ]]; then
        # Run the install.sh script to download the files
        if [ ! -f "install.sh" ]; then
            echo "Downloading install.sh..."
            curl -fsSL "$WEB_PATH/install.sh" -o install.sh
            chmod +x install.sh
        fi
        ./install.sh
        rm install.sh
        exit 0
    else
        echo "Installation aborted."
        exit 1
    fi
fi

if [ ! -f "share.1" ]; then
    echo "Error: share.1 not found. Installing from the web? [y/n]"
    read -r response
    if [[ "$response" == "y" || "$response" == "Y" ]]; then
        # Run the install.sh script to download the files
        if [ ! -f "install.sh" ]; then
            echo "Downloading install.sh..."
            curl -fsSL "$WEB_PATH/install.sh" -o install.sh
            chmod +x install.sh
        fi
        ./install.sh
        rm install.sh
        exit 0
    else
        echo "Installation aborted."
        exit 1
    fi
fi

# Move executable to /usr/local/bin
echo "Installing share utility to /usr/local/bin/share..."
sudo cp ${EXECUTABLE_PATH} /usr/local/bin/share
sudo chmod +x /usr/local/bin/share

# Move man page to /usr/local/share/man/man1
sudo cp share.1 /usr/local/share/man/man1/share.1

echo "Installation of local 'share' complete. You can now use the 'share' command."
