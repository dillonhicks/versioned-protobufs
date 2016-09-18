SHELL := /usr/bin/env bash

SPACE :=
SPACE +=
join-with = $(subst $(SPACE),$1,$(strip $2))

MODEL_BASE_DIR = src
MODEL_SCHEMA_TYPE=proto3
MODEL_SCHEMA_EXT=*.proto
MODEL_VERSION =
MODEL_VERSION_DIR := $(shell echo $(MODEL_VERSION) | tr '.' '/')
MODEL_DIR = $(MODEL_BASE_DIR)/$(MODEL_SCHEMA_TYPE)/$(MODEL_VERSION_DIR)
MODEL_FILES = $(wildcard $(MODEL_DIR)/$(MODEL_SCHEMA_EXT))

BUILD_DIR=build
PROTOBUF_COMMON_LIB_REPO=https://github.com/googleapis/googleapis.git
PROTOBUF_COMMON_PATH=googleapis

PROTOC_PLUGIN_DIR=python/plugins/bin
PROTOC_PATHS=--proto_path=$(MODEL_DIR) --proto_path=$(PROTOBUF_COMMON_PATH)

RELEASE_LANG=python
RELEASE_PREFIX=release
RELEASE_SUFFIX=
RELEASE_PARTS=$(RELEASE_PREFIX) $(RELEASE_LANG) $(MODEL_VERSION) $(RELEASE_SUFFIX)
RELEASE_NAME=$(call join-with,-,$(RELEASE_PARTS))

#
# Python Specific
#
PY_BIN_DIR=python/bin
PY_NAMESPACE='{{cookiecutter.project_namespace}}'


.PHONY: all


all:
	exit 1


print:
	@echo $(MODEL_SCHEMA_TYPE)
	@echo $(MODEL_SCHEMA_EXT)
	@echo $(MODEL_VERSION)
	@echo $(MODEL_VERSION_DIR)
	@echo $(MODEL_DIR)
	@echo $(MODEL_FILES)

googleapis:
	git clone $(PROTOBUF_COMMON_LIB_REPO) googleapis

venv:
	virtualenv venv
	source ./venv/bin/activate && pip install -r requirements.txt

bootstrap: venv googleapis
	@echo ok!


compile:
	-@mkdir $(BUILD_DIR)
	protoc $(PROTOC_PATHS) --python_out=$(BUILD_DIR) $(MODEL_FILES)


compile-debug:
	-@mkdir $(BUILD_DIR)
	protoc --plugin=protoc-gen-custom=$(PROTOC_PLUGIN_DIR)/json_schema_output_plugin.py \
		--custom_out=$(BUILD_DIR) \
		--proto_path=$(MODEL_DIR) \
		--python_out=$(BUILD_DIR) \
		$(MODEL_FILES)

pre-release: clean compile
	./$(PY_BIN_DIR)/release.py \
		--version $(MODEL_VERSION) \
		--build-dir $(BUILD_DIR) \
		--namespace $(PY_NAMESPACE) \
	 	--build

	cp -R build/gen-src .
	cp -R build/setup.py .


release: clean compile pre-release
	git checkout -b $(RELEASE_NAME)
	git add gen-src
	git add setup.py
	git commit -m "Release $(RELEASE_NAME)"

	@echo
	@echo
	@echo "########### $(RELEASE_NAME) #############"
	@echo "Status: built and verified!"
	@echo "After inspecting the release, remember to push the release branch:"
	@echo
	@echo "    git push -u origin $(RELEASE_NAME)"
	@echo


clean:
	rm -rfv $(BUILD_DIR)
	rm -rf setup.py gen-src
	find . -name '*.pyc' -exec rm -fv {} \;


really-clean: clean
	rm -rfv venv
	rm -rfv googleapis
