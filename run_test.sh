#!/bin/bash


if ((EUID != 0)); then
    echo " Please run it as Root"
    echo "sudo $0 $@"
    exit
fi



DOCKER_VERSION="5:18.09.5"
DOCKER_COMPOSE_VERSION=1.21.2
export LC_ALL=C

function install_docker() {
    if [ ! -x /usr/bin/docker ] || [ "$(docker version | grep -c $DOCKER_VERSION)" -lt 1 ]; then
        log_message "***************     Installing docker-engine: $DOCKER_VERSION"
            apt-get --assume-yes -y install apt-transport-https software-properties-common

            #Docker Installation of a specific Version
            curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
            sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
            echo -n "apt-get -qq update ..."
            apt-get -qq update
            echo "done"
            apt-cache policy docker-ce
            echo "Installing Docker: docker-ce=$DOCKER_VERSION*"
            apt-get -y --assume-yes --allow-downgrades install "docker-ce=$DOCKER_VERSION*"
            sleep 5
            systemctl restart docker
            sleep 5
    fi
}

function install_docker_compose() {
    if [ ! -x /usr/local/bin/docker-compose ] || [ "$(docker-compose version | grep -c $DOCKER_COMPOSE_VERSION)" -lt 1 ]; then
       curl -L https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
       chmod +x /usr/local/bin/docker-compose
    fi
}


function install_python_deps() {
    if [ "$(pip3 freeze | grep -c PyYAML)" -lt 1 ]; then
        apt-get install -y python3-pip
        pip3 install -r install-dep.txt
    fi
}


install_docker
install_docker_compose
install_python_deps

if [ ! -d /tmp/elastic ]; then
    mkdir -p /tmp/elastic
    chmod 777 /tmp/elastic
fi

sysctl -w vm.max_map_count=262144

chmod +x start-soak-test.py
./start-soak-test.py "${@}"

