#!/bin/bash


docker run --rm -e "SYSTEM_UNDER_TEST_IP=192.168.50.74" -e "ES_HOST=192.168.50.54:9201" -e "TEST_CYCLES=2" -v /home/ozlevka/projects/selenium-test/download:/opt/driver/logs ozlevka/python-test-download:latest