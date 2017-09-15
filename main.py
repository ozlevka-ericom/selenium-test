from datetime import datetime
from pyvirtualdisplay import Display
from selenium.webdriver.chrome.options import Options, DesiredCapabilities
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import consul
import os
from elasticsearch import Elasticsearch
import socket



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


file_path = 'test-url-list.txt'

if 'URL_FILE_PATH' in os.environ:
    file_path = os.environ['URL_FILE_PATH']

if 'ITERATION_PAUSE' in os.environ:
    iteration_pause = int(os.environ['ITERATION_PAUSE'])

if 'SHOW_BROWSER_UI' in os.environ:
    show_browser_ui = bool(os.environ['SHOW_BROWSER_UI'])


if 'CHROME_LOG_PATH' in os.environ:
    log_path = os.environ['CHROME_LOG_PATH']

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



cnl = consul.Consul(host=system_ip)

proxy_address = 'http://' + system_ip + ':3128'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("--disable-setuid-sandbox")
chrome_options.add_argument('--proxy-server=' + proxy_address)
chrome_options.binary_location = '/opt/google/chrome-beta/google-chrome'


def fetch_free_browsers():
    ss = cnl.agent.services()
    browsers = {
        'free': [],
        'used': []
    }
    for s in ss:
        if ss[s]['Service'] == 'shield-browser':
           if 'free' in ss[s]['Tags']:
               browsers['free'].append(s)
           elif 'used' in  ss[s]['Tags']:
               browsers['used'].append(s)
    return browsers


if not show_browser_ui:
    display = Display(visible=0, size=(800, 600))
    display.start()


desired_capabilities = None


service_log_path = "chromedriver.log"
service_args = ['--verbose', '--log-path=' + log_path + '/' + service_log_path]

main_driver = webdriver.Chrome(executable_path='/opt/google/chromedriver', service_args=service_args, chrome_options=chrome_options, desired_capabilities=desired_capabilities)     #usr/lib/chromium-browser/chromedriver')

for i in range(0, returns):
    for line in open(file_path, mode='rb'):
        try:
            browsers = fetch_free_browsers()
            print str(datetime.now()) + ' Free browsers: ' + str(len(browsers['free'])) + " Used browsers: " + str(len(browsers['used']))
            print str(datetime.now()) + ' ' + str(browsers)
            main_driver.get(line)
            error = None

            canvas = WebDriverWait(main_driver, 10).until(
                EC.presence_of_element_located((By.ID, "canvas"))
            )

            menu = WebDriverWait(main_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "nav.context-menu"))
            )

            if not canvas:
                raise Exception('Canvas not found')
            elif not canvas.__class__.__name__ == 'WebElement':
                raise Exception('Canvas is not WebElement')

            if not menu:
                raise Exception('menu not found')
            elif not menu.__class__.__name__ == 'WebElement':
                raise Exception('menu is not WebElement')

        except Exception, e:
            error = e


        body = {
            'url': line,
            '@timestamp': datetime.utcnow(),
            'browsers': {
                'free': len(browsers['free']),
                'used': len(browsers['used'])
            },
            'iteration': (i + 1),
            'hostname': hostname
        }

        if error is None:
            body['result'] = 'success'
        else:
            body['result'] = 'failed'
            body['error'] = str(type(error))
        es_client.index('soaktest', 'test', body)

        time.sleep(iteration_pause)

main_driver.quit()







