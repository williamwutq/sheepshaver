#!/bin/bash
WEB_PATH="https://raw.githubusercontent.com/williamwutq/sheepshaver/main"
SHARE_TYPE="python"
PIP="pip3"

# Check type and dependencies
if [ "$SHARE_TYPE" == "python" ]; then
    # Install Python dependencies
    echo "Installing Python dependencies..."
    $PIP install pathlib datetime argparse
    EXECUTABLE_PATH="share.py"
fi

# Download share.py and share.1 using curl
echo "Downloading share.py..."
curl -fsSL "$WEB_PATH/$EXECUTABLE_PATH" -o ${EXECUTABLE_PATH}

echo "Downloading share.1..."
curl -fsSL "$WEB_PATH/share.1" -o share.1

# Move executable to /usr/local/bin
echo "Installing share utility to /usr/local/bin/share..."
sudo cp ${EXECUTABLE_PATH} /usr/local/bin/share
sudo chmod +x /usr/local/bin/share

# Move man page to /usr/local/share/man/man1
sudo cp share.1 /usr/local/share/man/man1/share.1

echo "Installation complete. You can now use the 'share' command."