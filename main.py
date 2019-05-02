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



show_browser_ui = False

hostname = socket.gethostname()

system_ip = 'localhost'

iteration_pause = 5

returns = 1

if 'TEST_CYCLES' in os.environ:
    returns = int(os.environ['TEST_CYCLES'])

if 'SYSTEM_UNDER_TEST_IP' in os.environ:
    system_ip = os.environ['SYSTEM_UNDER_TEST_IP']

log_path = '/opt/driver/logs'

if 'CHROME_LOGS_PATH' in os.environ:
    log_path = os.environ['CHROME_LOGS_PATH']

es_host = 'localhost:9200'

if 'ES_HOST' in os.environ:
    es_host = os.environ['ES_HOST']

kibana_host = "http://localhost:5601"

if "KIBANA_HOST" in os.environ:
    kibana_host = os.environ["KIBANA_HOST"]


file_path = 'test-url-list.txt'

if 'URL_FILE_PATH' in os.environ:
    file_path = os.environ['URL_FILE_PATH']

if 'ITERATION_PAUSE' in os.environ:
    iteration_pause = int(os.environ['ITERATION_PAUSE'])

if 'SHOW_BROWSER_UI' in os.environ:
    show_browser_ui = os.environ['SHOW_BROWSER_UI'] == "True"


if 'CHROME_LOG_PATH' in os.environ:
    log_path = os.environ['CHROME_LOG_PATH']

maximum_tabs = 5
if 'MAXIMUM_TABS' in os.environ:
    maximum_tabs = int(os.environ['MAXIMUM_TABS'])

wait_time_out = 20
if 'WAIT_TIME_OUT' in os.environ:
    wait_time_out = int(os.environ['WAIT_TIME_OUT'])

es_client = Elasticsearch(hosts=[es_host])

wait_for_elasticsearch = True
es_retries = 200
counter = 1
while wait_for_elasticsearch:
    try:
        es_client.search()
        wait_for_elasticsearch = False
    except Exception, e:
        print e

    if counter < es_retries:
        counter = counter + 1
    else:
        raise Exception("Elasticsearch is not avaliable after " + str(counter) + " retries")
    time.sleep(1)

schema = EsSchema(es_client)
schema.make_schema()

kibana = Kibana(kibana_host)
kibana.import_dashboard("data/dashboard.json")


def make_result_body(iteration, attempt, url, data):
    browsers = fetch_free_browsers()
    print str(datetime.now()) + ' Free browsers: ' + str(len(browsers['free'])) + " Used browsers: " + str(
        len(browsers['used']))
    print str(datetime.now()) + ' ' + str(browsers)



    body = {
        'url': url,
        '@timestamp': datetime.utcnow(),
        'browsers': {
            'free': len(browsers['free']),
            'used': len(browsers['used'])
        },
        'iteration': (iteration + 1),
        'attempt': attempt,
        'hostname': hostname,
        'data_type': "main"
    }

    if data['error'] is None:
        body['result'] = 'success'
    else:
        body['result'] = 'failed'
        body['error'] = data['error']

    return body


def write_results_to_es(iteration, attempt, url, data, error):
    try:
        body = make_result_body(iteration, attempt, url, data)
        index = 'soaktest'
        print es_client.index(index, body)
        bulk = []
        for item in data['data']:
            performance = {
              'url': body['url'],
              '@timestamp': body['@timestamp'],
              'hostname': hostname,
              'attempt': attempt,
              'data_type': "performance",
              "browsing": {
                  "data": item
              }
            }
            index_item = {
                "_index": index,
                "_op_type": "index",
                '_source': performance
            }

            bulk.append(index_item)
        print H.bulk(es_client, bulk)
    except Exception, ex:
        print ex

consul_host = system_ip
consul_port = 8500
if 'CONSUL_HOST' in os.environ:
    consul_host = os.environ['CONSUL_HOST']
if 'CONSUL_PORT' in os.environ:
    consul_port = int(os.environ['CONSUL_PORT'])

cnl = consul.Consul(host=consul_host, port=consul_port)

proxy_address = 'http://' + system_ip + ':3128'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("--disable-setuid-sandbox")
chrome_options.add_argument('--proxy-server=' + proxy_address)
chrome_options.binary_location = '/opt/google/chrome/google-chrome'


def fetch_free_browsers():
    ss = cnl.catalog.service("shield-browser")
    browsers = {
        'free': [],
        'used': []
    }
    for s in ss[1]:
       if 'free' in s['ServiceTags']:
           browsers['free'].append(s)
       elif 'used' in  s['ServiceTags']:
           browsers['used'].append(s)
    return browsers


if not show_browser_ui:
    display = Display(visible=0, size=(800, 600))
    display.start()


desired_capabilities = None


service_log_path = "chromedriver.log"
service_args = ['--verbose', '--log-path=' + log_path + '/' + service_log_path]

pool = ThreadPool(5)

def clear_half_tabs(driver):
    for _ in range(0, int(maximum_tabs / 2)):
        driver.switch_to.window(driver.window_handles[0])
        driver.close()

def make_data_from_table(trs, error):
    data = []
    for tr in trs[1:]:
        tds = tr.find_elements_by_tag_name('td')
        data.append({
            'name': tds[0].text,
            'client_time': tds[1].text,
            'server_time': tds[2].text
        })
    if not error is None:
        return {
            'error': error,
            'data': data
        }
    return {
        'error': None,
        'data': data
    }

def run_main_line():
    main_driver = webdriver.Chrome(executable_path='/opt/google/chromedriver', service_args=service_args, chrome_options=chrome_options, desired_capabilities=desired_capabilities)  # usr/lib/chromium-browser/chromedriver')
    try:
        wait = WebDriverWait(main_driver, wait_time_out)

        for i in range(0, returns):
            for line in open(file_path, mode='rb'):
                error = None
                data = None
                for j in range(1,4):
                    try:
                       main_driver.get("http://shield-perf")
                       try:
                           url = wait.until(
                               EC.presence_of_element_located((By.ID, "target-url"))
                           )
                       except TimeoutException:
                           raise TimeoutException("Main page load timeout attempt {}".format(i))


                       url.clear()
                       url.send_keys(line)
                       try:
                           iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#frame-wrapper iframe.an-frame")))
                       except TimeoutException:
                           raise TimeoutException("Shield iframe timeout attempt {}".format(i))

                       main_driver.switch_to.frame(iframe)
                       try:
                           wait.until(EC.presence_of_element_located((By.ID, "canvas")))
                       except TimeoutException:
                            print "Access now timeout attempt {}".format(i)
                       main_driver.switch_to.window(main_driver.window_handles[0])

                       page_loaded = False
                       #"page fully loaded"

                       last_error = None
                       try:
                           wait.until(
                               EC.presence_of_element_located((By.ID,"page-loaded"))
                           )
                       except TimeoutException:
                           last_error = "Page fully loaded timeout attempt {}".format(i)

                       time.sleep(iteration_pause)

                       trs = main_driver.find_elements_by_css_selector("#table-results tr")

                       data = make_data_from_table(trs, last_error)

                    except Exception, e:
                        print e
                        error = e

                    write_results_to_es( i, j, line, data, error)

                # try:
                #     if len(main_driver.window_handles) >= maximum_tabs:
                #         clear_half_tabs(main_driver)
                #         current_handle = main_driver.window_handles[-1]
                #         main_driver.switch_to.window(current_handle)
                # except Exception, e:
                #     print e



                time.sleep(iteration_pause)
    except Exception as exs:
        print exs
    finally:
        main_driver.quit()


run_main_line()







