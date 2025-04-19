PARTICLE := $(shell which particle)
JQ := $(shell which jq)
PLATFORM := p2
OS := 6.2.1


ifeq ($(PARTICLE),)
$(error Poetry is not installed and is required)
endif

ifneq ("$(wildcard .env)","")
    include .env
	export $(shell sed 's/=.*//' .env)
endif

ifeq ("$(wildcard wifi-creds.json)","")
    $(shell touch wifi-creds.json)
endif

SSID := $(shell cat wifi-creds.json | jq '.network')

.PHONY: clear-wifi add-wifi join-wifi init-wifi compile flash monitor-local

clear-wifi:
	$(PARTICLE) wifi clear

add-wifi:
	$(PARTICLE) wifi add --file wifi-creds.json

join-wifi:
	${PARTICLE} wifi join --ssid $(SSID)

init-wifi: clear-wifi add-wifi join-wifi

compile:
	$(PARTICLE) compile $(PLATFORM) --target $(OS)

flash:
	$(PARTICLE) flash --local . --target $(OS)

monitor-local:
	$(PARTICLE) serial monitor --follow