.ONESHELL:
SHELL := /bin/bash

run:
	clear && sudo go run . run

calibrate:
	clear && sudo go run . calibrate

startup:
	chmod +x /home/raspberry/projects/tactileforce/raspberry/startup/startup.sh
	crontab -e


.PHONY: run calibrate startup
