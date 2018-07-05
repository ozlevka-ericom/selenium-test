#!/usr/bin/python3


"""
Create Soak Test Environment
"""

import subprocess, os, sys
import argparse, yaml
from datetime import datetime

SYSTEM_UNDER_TEST="SYSTEM_UNDER_TEST_IP={}"
TEST_CYCLES="TEST_CYCLES={}"
ITERATION_PAUSE="ITERATION_PAUSE={}"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-ip", dest="ip", required=True, help="IP of system to test")
    parser.add_argument("-b", dest="browsers", required=True, help="Number of browser workers")
    parser.add_argument("-d", dest="downloads", required=True, help="Number of download workers")
    parser.add_argument("-i", dest="iterations", default=1000, help="Number of iterations")
    parser.add_argument("-p", dest="pause", default=20, help="Pause between url fetching")

    return parser.parse_args()

def make_running_config(compose, arguments):
    compose['services']['test']['environment'].append(SYSTEM_UNDER_TEST.format(arguments.ip))
    compose['services']['test']['environment'].append(TEST_CYCLES.format(arguments.iterations))
    compose['services']['test']['environment'].append(ITERATION_PAUSE.format(arguments.pause))
    compose['services']['test-download']['environment'].append(SYSTEM_UNDER_TEST.format(arguments.ip))
    compose['services']['test-download']['environment'].append(TEST_CYCLES.format(arguments.iterations))
    compose['services']['test-download']['environment'].append(ITERATION_PAUSE.format(arguments.pause))


def main():
    arguments = parse_args()
    now = datetime.now()
    current_compose_name = './docker-compose-{0}-{1}-{2}.yml'.format(now.day, now.hour, now.minute)
    with open('./compose.yml', mode='r') as file:
        compose = yaml.load(file)

    make_running_config(compose, arguments)

    with open(current_compose_name, mode="w") as file:
        yaml.dump(compose, file)
    run_command = "docker-compose --file {0} up -d --scale test={1} --scale test-download={2}".format(current_compose_name, arguments.browsers, arguments.downloads)
    subprocess.run(run_command, shell=True)


if __name__ == '__main__':
    main()

