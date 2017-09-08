#!/bin/bash


docker run --rm -e "SYSTEM_UNDER_TEST_IP=192.168.50.114" -e "ES_HOST=192.168.50.150:9201" -e "TEST_CYCLES=2" ozlevka/python-test:170907-15.25