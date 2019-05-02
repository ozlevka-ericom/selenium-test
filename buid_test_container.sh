#!/bin/bash

if [[ -z "$1" || "$1" == "upload"   ]]; then
    TAG=`date +"%y%m%d-%H.%M"`
else
    TAG=$1
fi

echo "$TAG"

docker build -t ozlevka/python-test:latest .
#docker build -t ozlevka/python-test-download:latest -f Dockerfile-download .


if [[ "$1" = "upload" ]]; then

    echo "Upload builded scripts"
    docker tag ozlevka/python-test:latest ozlevka/python-test:$TAG
    docker push ozlevka/python-test:$TAG
#    docker tag ozlevka/python-test-download:latest ozlevka/python-test-download:$TAG
#    docker push ozlevka/python-test-download:$TAG
fi