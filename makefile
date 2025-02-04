.ONESHELL:
SHELL := /bin/bash

run:
	clear && sudo go run . run

startup:
	chmod +x /home/raspberry/projects/tactileforce/startup/startup.sh
	crontab -e


.PHONY: run startup
