#!/bin/bash

if [[ -z "$1" || "$1" == "upload"   ]]; then
    TAG=`date +"%y%m%d-%H.%M"`
else
    TAG=$1
fi

docker build -t "ozlevka/white-test:$TAG" -f Dockerfile-dev .