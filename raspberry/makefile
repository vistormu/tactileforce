.ONESHELL:
SHELL := /bin/zsh

run:
	clear && sudo -E go run . run

calibrate:
	clear && sudo go run . calibrate

startup:
	chmod +x /home/raspberry/projects/tactileforce/raspberry/startup/startup.sh
	crontab -e


.PHONY: run calibrate startup
