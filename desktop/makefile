.ONESHELL:
SHELL := /bin/zsh

.SILENT:

dataset_path = datasets/squishy
test_dataset_path = datasets/squishy/test-data

create:
	python create_dataset.py
	cd $(dataset_path)
	python create_dataset.py
	cd ../..
	# cp $(test_dataset_path)/data.csv $(dataset_path)/test/data.csv

train:
	clear && python train.py

send:
	cahier send raspberrydelft models/transformer.onnx /home/raspberry/projects/tactileforce/models/
