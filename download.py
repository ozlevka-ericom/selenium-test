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
import socket
from gevent.threadpool import ThreadPool
from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException
from esschema import EsSchema
import glob



show_browser_ui = False

hostname = socket.gethostname()

system_ip = 'localhost'

iteration_pause = 5

returns = 1

url_template = "https://drive.google.com/uc?id={}&export=download"

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


file_path = 'links/index.html'

if 'URL_FILE_PATH' in os.environ:
    file_path = os.environ['URL_FILE_PATH']

download_path = '/download'

if 'FILE_DOWNLOAD_PATH' in os.environ:
    download_path = os.environ['FILE_DOWNLOAD_PATH']

if 'ITERATION_PAUSE' in os.environ:
    iteration_pause = int(os.environ['ITERATION_PAUSE'])

if 'SHOW_BROWSER_UI' in os.environ:
    show_browser_ui = os.environ['SHOW_BROWSER_UI'] == "True"


if 'CHROME_LOG_PATH' in os.environ:
    log_path = os.environ['CHROME_LOG_PATH']

maximum_tabs = 5
if 'MAXIMUM_TABS' in os.environ:
    maximum_tabs = int(os.environ['MAXIMUM_TABS'])

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
        'browsing': data,
        'download': True
    }

    if data['error'] is None:
        body['result'] = 'success'
    else:
        body['result'] = 'failed'

    return body


def write_results_to_es(iteration, attempt, url, data, error):
    try:
        body = make_result_body(iteration, attempt, url, data)
        print es_client.index('soakdownload', 'test', body)
    except Exception, ex:
        print ex

cnl = consul.Consul(host=system_ip)

proxy_address = 'http://' + system_ip + ':3128'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("--disable-setuid-sandbox")
chrome_options.add_argument('--proxy-server=' + proxy_address)
prefs = {'download.default_directory' : download_path}
chrome_options.add_experimental_option('prefs', prefs)
chrome_options.binary_location = '/opt/google/chrome/google-chrome'


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
        wait = WebDriverWait(main_driver, 20)

        for i in range(0, returns):
            for line in open(file_path, mode='rb'):
                error = None
                data = None
                try:
                   main_driver.get("http://shield-perf")
                   url = url_template.format(line.strip())
                   try:
                       try:
                           url_input = wait.until(
                               EC.presence_of_element_located((By.ID, "target-url"))
                           )
                       except TimeoutException:
                           raise TimeoutException("Main page load timeout attempt {}".format(i))

                       url_input.send_keys(url + "\n")

                       try:
                           iframe = wait.until(EC.presence_of_element_located(
                               (By.CSS_SELECTOR, "div#frame-wrapper iframe.an-frame")))
                       except TimeoutException:
                           raise TimeoutException("Shield iframe timeout attempt {}".format(i))

                   except Exception as e:
                       print(e)
                except Exception as ex:
                    if isinstance(ex, UnexpectedAlertPresentException):
                        alert = main_driver.switch_to.alert
                        alert.dismiss()
                    else:
                        print(ex)



                max_attempts = 20
                count = 1
                while len(glob.glob(download_path + '/*')) == 0:
                    time.sleep(1)
                    if count >= max_attempts:
                        error = "Download timeout"
                        break
                    else:
                        count += 1

                dir_files = glob.glob(download_path + '/*')
                if len(dir_files) > 0:
                    file_name = os.path.basename(dir_files[0])
                    os.system('rm -f {}/*'.format(download_path))
                else:
                    file_name = ''
                message = None
                try:
                    trs = main_driver.find_elements_by_css_selector("#table-results tr")
                    data = make_data_from_table(trs, error)
                    iframe = main_driver.find_element(By.CSS_SELECTOR, "div#frame-wrapper iframe.an-frame")
                    main_driver.switch_to.frame(iframe)
                    try:
                        message = main_driver.find_element(By.CSS_SELECTOR, "#toast-container div.toast-message")
                    except Exception as expt:
                        if isinstance(expt, NoSuchElementException):
                            error = None
                        else:
                            error = str(expt)
                except Exception as ex:
                    error = str(ex)

                if not message is None:
                    data['error'] = message.text
                    error = 'failed'
                write_results_to_es(i, 0, file_name, data, error)

                time.sleep(iteration_pause)
    except Exception as exs:
        print exs
    finally:
        main_driver.quit()


run_main_line()







