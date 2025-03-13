.ONESHELL:
SHELL := /bin/bash

run:
	clear && sudo go run . run

calibrate:
	clear && sudo go run . calibrate

startup:
	chmod +x /home/raspberry/projects/tactileforce/startup/startup.sh
	crontab -e

server:
	clear && ./abstractme 145.94.60.82:8080


.PHONY: run calibrate startup
