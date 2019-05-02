#!/usr/bin/env bash


docker run --rm \
    -e "SYSTEM_UNDER_TEST_IP=192.168.50.18" \
    -e "TEST_CYCLES=1000" \
    -e "ES_HOST=192.168.50.12:9201" \
    -e ITERATION_PAUSE=10 \
    -e "CHROME_LOG_PATH=." \
    -e "KIBANA_HOST=http://192.168.50.12:5603" \
    ozlevka/python-test:latest
