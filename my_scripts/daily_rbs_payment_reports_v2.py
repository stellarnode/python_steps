#!/usr/bin/env python
# coding: utf-8

# In[253]:

import numpy as np
import pandas as pd
# import json, requests
from pandas.io.json import json_normalize
from datetime import datetime, timedelta
import smtplib as smtp
from getpass import getpass
import urllib, json

# creds below should contain: BASE_URL, USERNAME, PASSWORD_ENCODED_FOR_HTML, MERCHANT, EMAIL, EMAIL_PASSWORD, DESTINATION_EMAILS_ARRAY, SMTP_SERVER
import daily_rbs_payment_credentials as creds

base_url = creds.BASE_URL
username = creds.USERNAME
password = creds.PASSWORD_ENCODED_FOR_HTML
merchant = creds.MERCHANT

# In[254]:

today = datetime.now()
delta = 1

if today.hour <= 9 or delta > 1:
    day_before = today - timedelta(days = delta)
    day_before = day_before.replace(hour = 0, minute = 0, second = 0)
else:
    day_before = today.replace(hour = 0, minute = 0, second = 0)

hour_start = '000000'
hour_end = '080000'

def format_str_zeros(x):
    if x < 10:
        out = '0' + str(x)
    else:
        out = str(x)
    return out

def construct_url(base_url, username, password, page, start, end, merchant):
    # MAXIMUM SUPPORTED PAGESIZE IS 200 (SEE RBS MANUAL)
    url = ''
    url = base_url
    url += "userName={0}&password={1}&".format(username, password)
    url += "language=ru&page={0}&size=200&from={1}&to={2}&transactionStates=DEPOSITED&".format(page, start, end)
    url += "merchants={}&searchByCreatedDate=false".format(merchant)
    return url

hour_start = format_str_zeros(day_before.hour) + '0000'
day_before_str = format_str_zeros(day_before.day)
month_before_str = format_str_zeros(day_before.month)

# print(day_before)

if today.hour < 22:
    today = today.replace(hour = today.hour + 2)

hour_end = format_str_zeros(today.hour) + format_str_zeros(today.minute) + format_str_zeros(today.second)
day = format_str_zeros(today.day)
month = format_str_zeros(today.month)

start = str(today.year) + month_before_str + day_before_str + hour_start
end = str(today.year) + month + day + hour_end
print('daily report timeframe:')
print(start, end)

start_formatted = datetime.strptime(start, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M')
end_formatted = datetime.strptime(end, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M')
print(start_formatted, end_formatted)
print('\n')

# url = construct_url(base_url, username, password, 0, start, end, merchant)

###########################################################################################
### START OF MONTHLY SALES CALCULATIONS ###################################################

month_beginning = today.replace(day = 1, hour = 0, minute = 0, microsecond = 0)
monthly_hour_start_str = format_str_zeros(month_beginning.hour) + '0000'
monthly_day_start_str = format_str_zeros(month_beginning.day)
monthly_month_start_str = format_str_zeros(month_beginning.month)
month_start = str(month_beginning.year) + monthly_month_start_str + monthly_day_start_str + monthly_hour_start_str
month_end_dt = month_beginning
if month_beginning.month == 12:
    month_end_dt = month_beginning.replace(year = month_beginning.year + 1)
    month_end_dt = month_end_dt.replace(month = 1)
else:
    month_end_dt = month_end_dt.replace(month = month_end_dt.month + 1)
monthly_month_end_str = format_str_zeros(month_end_dt.month)
month_end = str(month_end_dt.year) + monthly_month_end_str + monthly_day_start_str + monthly_hour_start_str

pager = 0
total_sales = 0
total_payments = 0
text_to_send_monthly = ''

url_monthly = construct_url(base_url, username, password, pager, month_start, month_end, merchant)

print('monthly sales calculation...')
print('monthly calcuations timeframe:')
print(month_start, month_end)
print('url monthly: ', url_monthly)

def calculate_sales(monthly_paginator, sales):
    # response_monthly = pd.read_json(monthly_paginator, orient='columns')
    response_monthly = monthly_paginator
    response_monthly = json_normalize(response_monthly['orderStatuses'])
    report_monthly = response_monthly[['amount', 'bankInfo.bankName', 'orderDescription', 'cardAuthInfo.cardholderName', 'cardAuthInfo.paymentSystem', 'ip', 'orderNumber']].copy()
    report_monthly['Date'] = response_monthly['authDateTime'].apply(lambda x: datetime.fromtimestamp(x // 1000).isoformat(sep='T'))
    report_monthly['customterEmail'] = response_monthly['merchantOrderParams'].apply(lambda x: x[0]['value'])
    report_monthly['amount'] = report_monthly['amount'].apply(lambda x: float(x) / 100)
    return sales + report_monthly['amount'].sum()

with urllib.request.urlopen(url_monthly) as url:
    monthly_paginator = json.loads(url.read().decode())

    if monthly_paginator and monthly_paginator['totalCount'] > 0 and monthly_paginator['pageSize'] > 0:
        total_payments = monthly_paginator['totalCount']
        page_size = monthly_paginator['pageSize']
        i = int(total_payments / page_size) + 1
        print('total payments from json: ', total_payments)
        print('page size from json: ', page_size)
        print('number of iterations: ', i)
        # print(monthly_paginator)
        # print('**************************************')

        total_sales = calculate_sales(monthly_paginator, total_sales)
        pager += 1

        # print(pager)
        # print(total_sales)

        while pager <= i:
            url_monthly = construct_url(base_url, username, password, pager, month_start, end, merchant)

            with urllib.request.urlopen(url_monthly) as url:
                monthly_paginator = json.loads(url.read().decode())

                if monthly_paginator['orderStatuses']:
                    total_sales = calculate_sales(monthly_paginator, total_sales)

                    print('iterator at the end: ', pager)
                    print('total calculated sales: ', total_sales)
            pager += 1

        text_to_send_monthly = '\n\n\nCurrent month: {}.'.format(str(month_beginning.year) + '-' + monthly_month_start_str)
        text_to_send_monthly += '\nTotal b2c sales this month: {} (including VAT).'.format(total_sales)
        text_to_send_monthly += '\nTotal number of payments this month: {}.'.format(total_payments)

    else:
        text_to_send_monthly = '\n\n\nNo completed payments this month yet.'

print(text_to_send_monthly)

########################################################################
########################################################################


########################################################################
### START OF DAYLY REPORTS #############################################
########################################################################
### REMEMBER: ONCE THE NUMBER OF DAILY PAYMENTS INCREASER TO OVER 200 ##
### THIS WILL HAVE TO BE ADJUSTED TO PAGINATION SINCE RBS ONLY SUPPORTS
### 200 ENTRIES MAX PER PAGE ###########################################

# In[256]:
url = construct_url(base_url, username, password, 0, start, end, merchant)
print('\n\ndaily payments report...')
print('url: ', url)

response = pd.read_json(url, orient='columns')

if response['orderStatuses'].empty:
    text_to_send = 'No completed payments from {} to {}.'.format(start_formatted, end_formatted)
    print(text_to_send)
else:
    text_to_send = 'List of payments from {} to {}: \n\n'.format(start_formatted, end_formatted)
    # print(response['orderStatuses'])
    
    response = json_normalize(response['orderStatuses'])
    # response.to_excel('/Users/stellarnode/Desktop/response.xls')
    # response.head()
    
    report = response[['amount', 'bankInfo.bankName', 'orderDescription', 'cardAuthInfo.cardholderName', 'cardAuthInfo.paymentSystem', 'ip', 'orderNumber']].copy()
    report['Date'] = response['authDateTime'].apply(lambda x: datetime.fromtimestamp(x // 1000).isoformat(sep='T'))
    report['customterEmail'] = response['merchantOrderParams'].apply(lambda x: x[0]['value'])
    report['amount'] = report['amount'].apply(lambda x: float(x) / 100)
    
    report.rename(index=str, columns={'amount': 'AMOUNT',
                                      'bankInfo.bankName': 'BANK_NAME',
                                      'orderDescription': 'ORDER_NUMBER',
                                      'cardAuthInfo.cardholderName': 'CARDHOLDER_NAME',
                                      'cardAuthInfo.paymentSystem': 'PAYMENT_SYSTEM',
                                      'ip': 'IP_ADDRESS',
                                      'Date': 'DATE',
                                      'customterEmail': 'CUSTOMER_EMAIL',
                                      'orderNumber': 'ORDER_CODE'},
                                      inplace = True)
    
    text_to_send = text_to_send + report.to_string()
    # print(text_to_send)

### For monthly payment report

text_to_send += text_to_send_monthly
print('\n\n\nfinal report to be sent by email...\n\n\n')
print(text_to_send)
print('\n\n\nsending email...')
### 


# In[257]:


email = creds.EMAIL
password = creds.EMAIL_PASSWORD
dest_email = creds.DESTINATION_EMAILS_ARRAY
subject = 'SmartU Payments from {} to {}'.format(start_formatted, end_formatted)
email_text = text_to_send

message = 'From: {}\nTo: {}\nSubject: {}\n\n{}'.format('SmartU Mailer <' + email + '>',
                                                       dest_email, 
                                                       subject, 
                                                       email_text)

server = smtp.SMTP_SSL(creds.SMTP_SERVER)
server.set_debuglevel(1)
server.ehlo(email)
server.login(email, password)
server.auth_plain()
server.sendmail(email, dest_email, message)
server.quit()

print('\n\n\ndone.')

# In[ ]:




