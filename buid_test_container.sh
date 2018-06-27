#!/bin/bash -x

if [ -z "$1" ]; then
    TAG=`date +"%y%m%d-%H.%M"`
else
    TAG=$1
fi

docker build -t ozlevka/python-test:latest .
docker tag ozlevka/python-test:latest ozlevka/python-test:$TAG
docker build -t ozlevka/python-test-download:latest -f Dockerfile-download
docker tag ozlevka/python-test-download:latest ozlevka/python-test-download:$TAG