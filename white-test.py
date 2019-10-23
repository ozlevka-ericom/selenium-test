from datetime import datetime
from pyvirtualdisplay import Display
from selenium.webdriver.common.by import By
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import consul
import os, sys
from elasticsearch import Elasticsearch
import elasticsearch.helpers as H
import socket
from gevent.threadpool import ThreadPool
from selenium.common.exceptions import TimeoutException
from esschema import EsSchema
from kibana.client import Kibana

def make_web_drver(system_ip):
    proxy_address = 'http://' + system_ip + ':3128'
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument('--proxy-server=' + proxy_address)
    chrome_options.binary_location = '/opt/google/chrome/google-chrome'
    log_path = "."
    service_log_path = "chromedriver.log"
    service_args = ['--verbose', '--log-path=' + log_path + '/' + service_log_path]
    desired_capabilities = None
    return webdriver.Chrome(executable_path='/opt/google/chromedriver', service_args=service_args,
                                   chrome_options=chrome_options,
                                   desired_capabilities=desired_capabilities)  # usr/lib/chromium-browser/chromedriver')


def check_result(urls):
    client = Elasticsearch()
    for url in urls:
        query = {
          "query": {
            "bool": {
              "must": [
                {
                  "range": {
                    "@timestamp": {
                      "gte": "now-3m"
                    }
                  }
                },
                {
                  "term": {
                    "Domain": {
                      "value": "{}".format(url.replace('http://','').replace('https://','').replace('/','').replace('\n',''))
                    }
                  }
                }
              ]
            }
          }
        }
        res = client.search("connections-*", body=query)
        if res["hits"]["total"]["value"] >= 1:
            print("{} is OK".format(url))


def main(args):
    if len(args) == 2:
        driver = make_web_drver(args[1])
        with open("./white-test-urls.txt", mode='r') as file:
            urls = file.readlines()
        for url in urls:
            driver.get(url)
            ready = False
            counter = 1
            while not ready and counter <= 4:
                page_state = driver.execute_script('return document.readyState;')
                ready = page_state == 'complete'
                counter += 1
                time.sleep(1)

            print("{0} ready:{1} take:{2}".format(url, ready, counter))
        check_result(urls)
    else:
        print("No IP address")
        exit(1)


if __name__ == "__main__":
    # with open("./white-test-urls.txt", mode='r') as file:
    #     urls = file.readlines()
    # check_result(urls)
    main(sys.argv)