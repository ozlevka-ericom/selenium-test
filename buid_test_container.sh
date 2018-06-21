#!/bin/bash -x

if [ -z "$1" ]; then
    TAG=`date +"%y%m%d-%H.%M"`
else
    TAG=$1
fi

docker build -t ozlevka/python-test:latest .
docker tag ozlevka/python-test:latest ozlevka/python-test:$TAG