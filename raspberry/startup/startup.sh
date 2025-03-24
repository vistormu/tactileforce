#!/bin/bash

PROJECT_PATH="/home/raspberry/projects/tactileforce/raspberry"
ENV_PATH="/home/raspberry/miniconda3/bin/activate"
IP_PATH="$PROJECT_PATH/startup/ip.txt"
SERVER_PATH="$PROJECT_PATH/abstractme"

# display the ip on the OLED screen
source $ENV_PATH tactile
python $PROJECT_PATH/startup/display.py
conda deactivate

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

cd $PROJECT_PATH
./abstractme $(<"$IP_PATH"):8080
