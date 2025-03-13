.ONESHELL:
SHELL = /bin/zsh

.SILENT:
.PHONY: fy all

fy:
	clear && python main.py --config configs/fy.toml

mx:
	clear && python main.py --config configs/mx.toml

fy-mx:
	clear && python main.py --config configs/fy_mx.toml

f:
	clear && python main.py --config configs/f.toml

all:
	clear && python main.py --config configs/all.toml

server:
	clear && ./abstractme localhost:8080
