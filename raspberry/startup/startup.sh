#!/bin/zsh
sleep 30

PROJECT_PATH="/home/raspberry/projects/tactileforce/raspberry/"
IP_PATH="$PROJECT_PATH/startup/ip.txt"
SERVER_PATH="$PROJECT_PATH/abstractme"

# display the ip on the OLED screen
cd $PROJECT_PATH/startup
source .venv/bin/activate
python display.py

# check if ip.txt exists
if [[ ! -f "$IP_PATH" ]]; then
    echo "Error: File '$IP_PATH' not found."
    exit 1
fi

# check if the binary exists and is executable
if [[ ! -x "$SERVER_PATH" ]]; then
    echo "Error: Binary '$SERVER_PATH' not found or not executable."
    exit 1
fi

cd ..
./abstractme $(<"$IP_PATH"):8080
