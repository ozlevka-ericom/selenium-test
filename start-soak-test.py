#!/usr/bin/python3


"""
Create Soak Test Environment
"""

import subprocess, os

if os.getuid() != 0:
    print("Please run this script as super user (sudo)")
    exit(1)

def install_pip_packages():
    import pip
    pip.main(["install", "PyYaml"])

def configure_locale():
    command = 'locale-gen --purge en_US.UTF-8 ' \
              + '&& echo -e \'LANG="en_US.UTF-8"\nLANGUAGE="en_US:en"\n\' > /etc/default/locale'
    subprocess.call(command, shell=True)


def check_packages_installed():
    try:
        import pip
        list_packages = [pkg.key for pkg in pip.get_installed_distributions()]
        installed = False
        for p in list_packages:
            if p.lower() == "pyyaml":
                installed = True
                break
        if not installed:
            install_pip_packages()
    except Exception as ex:
        if "No module named 'pip'" in str(ex):
            configure_locale()
            subprocess.call("apt-get update && apt-get install -y python3-pip", shell=True)
            install_pip_packages()


check_packages_installed()


print('Hello world')


