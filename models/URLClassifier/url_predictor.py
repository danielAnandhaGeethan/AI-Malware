"@author: Arjun P"
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import re
from urllib.parse import urlparse
from tld import get_tld
from sklearn.preprocessing import LabelEncoder
from lightgbm import LGBMClassifier
import pickle
import pandas as pd
import utils.utils as utils

#Use of IP or not in domain
def having_ip_address(url):
    match = re.search(
        '(([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.'
        '([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\/)|'  # IPv4
        '((0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\/)' # IPv4 in hexadecimal
        '(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}', url)  # Ipv6
    if match:
        # print match.group()
        return 1
    else:
        # print 'No matching pattern found'
        return 0



#First Directory Length
def fd_length(url):
    urlpath= urlparse(url).path
    try:
        return len(urlpath.split('/')[1])
    except:
        return 0


#Length of Top Level Domain
def tld_length(tld):
    try:
        return len(tld)
    except:
        return -1

def letter_count(url):
    letters = 0
    for i in url:
        if i.isalpha():
            letters = letters + 1
    return letters

def digit_count(url):
    digits = 0
    for i in url:
        if i.isnumeric():
            digits = digits + 1
    return digits

def count_symbol(url):
    perc_count = url.count('%')
    return perc_count

def count_questionmark(url):
    ques_count = url.count('?')
    return ques_count

def count_dash(url):
    dash_count = url.count('-')
    return dash_count

def count_equal(url):
    equal_count = url.count('=')
    return equal_count

#Length of URL
def url_length(url):
    url_length = len(url)
    return url_length

#Hostname Length
def hostname_length(url):
    parsed_url = urlparse(url)
    hostname_length = len(parsed_url.hostname)
    return hostname_length

def count_https(url):
    https_count = url.count('https')
    return https_count

def count_http(url):
    http_count = url.count('http')
    return http_count

def count_w_www(url):
    w_count = url.count('www')
    return w_count

def count_at(url):
    at_count = url.count('@')
    return at_count

def no_of_dir(url):
    urldir = urlparse(url).path
    return urldir.count('/')

def no_of_embed(url):
    urldir = urlparse(url).path
    return urldir.count('//')

def shortening_service(url):
    match = re.search('bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|'
                      'yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|'
                      'short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|'
                      'doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|'
                      'db\.tt|qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|'
                      'q\.gs|is\.gd|po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|'
                      'x\.co|prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|'
                      'tr\.im|link\.zip\.net',
                      url)
    if match:
        return 1
    else:
        return 0

def suspicious_words(url):
    match = re.search('PayPal|login|signin|bank|account|update|free|lucky|service|bonus|ebayisapi|webscr',
                      url)
    if match:
        return 1
    else:
        return 0

def suspicious_words(url):
    match = re.search('PayPal|login|signin|bank|account|update|free|lucky|service|bonus|ebayisapi|webscr',
                      url)
    if match:
        return 1
    else:
        return 0

def count_dot(url):
    dot_count = url.count('.')
    return dot_count

def abnormal_url(url):
    hostname = urlparse(url).hostname
    hostname = str(hostname)
    pattern = re.escape(hostname)
    match = re.search(pattern, url)
    if match:
        # print match.group()
        return 1
    else:
        # print 'No matching pattern found'
        return 0

def lgbm_clf(input_url):
    # prepare input features for the model
    input_features = []
    input_features.append(having_ip_address(input_url))
    input_features.append(abnormal_url(input_url))
    input_features.append(count_dot(input_url))
    input_features.append(count_w_www(input_url))
    input_features.append(count_at(input_url))
    input_features.append(no_of_dir(input_url))
    input_features.append(no_of_embed(input_url))
    input_features.append(shortening_service(input_url))
    input_features.append(count_https(input_url))
    input_features.append(count_http(input_url))
    input_features.append(count_symbol(input_url))
    input_features.append(count_questionmark(input_url))
    input_features.append(count_dash(input_url))
    input_features.append(count_equal(input_url))
    input_features.append(url_length(input_url))
    input_features.append(hostname_length(input_url))
    input_features.append(suspicious_words(input_url))
    input_features.append(fd_length(input_url))
    input_features.append(tld_length(get_tld(input_url, fail_silently=True)))
    input_features.append(digit_count(input_url))
    input_features.append(letter_count(input_url))
    with open(utils.ROOT_PATH + "/weights/url_lgbm.pkl", "rb") as f:
        LGB_C = pickle.load(f)
    # predict output
    predicted_output = LGB_C.predict([input_features])[0]

    # print predicted output label
    print("Input URL:", input_url)
    print("Predicted output label:", predicted_output)

if __name__ == "__main__":
    lgbm_clf("https://facebook.com/asdf")
