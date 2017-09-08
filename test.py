from selenium import webdriver
from seleniumrequests import Chrome

proxy_address = 'http://192.168.50.114:3128'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("--disable-setuid-sandbox")
chrome_options.add_argument('--proxy-server=' + proxy_address)
chrome_options.binary_location = '/opt/google/chrome-beta/google-chrome'

driver = Chrome(executable_path='/opt/google/chromedriver', chrome_options=chrome_options)


response = driver.request('GET', "http://ynet.co.il")


print response