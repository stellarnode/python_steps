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

# creds below should contain: BASE_URL, USERNAME, PASSWORD_ENCODED_FOR_HTML, MERCHANT, EMAIL, EMAIL_PASSWORD, DESTINATION_EMAILS_ARRAY, SMTP_SERVER
import daily_rbs_payment_credentials as creds

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

hour_start = format_str_zeros(day_before.hour) + '0000'
day_before_str = format_str_zeros(day_before.day)
month_before_str = format_str_zeros(day_before.month)

# print(day_before)

if today.hour < 22:
    today = today.replace(hour = today.hour + 2)

hour_end = format_str_zeros(today.hour) + '0000'
day = format_str_zeros(today.day)
month = format_str_zeros(today.month)


start = str(today.year) + month_before_str + day_before_str + hour_start
end = str(today.year) + month + day + hour_end
print(start, end)

start_formatted = datetime.strptime(start, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M')
end_formatted = datetime.strptime(end, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M')
print(start_formatted, end_formatted)

url = creds.BASE_URL
url += "userName={0}&password={1}&".format(creds.USERNAME, creds.PASSWORD_ENCODED_FOR_HTML)
url += "language=ru&page=0&size=100&from={0}&to={1}&transactionStates=DEPOSITED&".format(start, end)
url += "merchants={}&searchByCreatedDate=false".format(creds.MERCHANT)
# print(url)


# In[256]:


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
    print(text_to_send)


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


# In[ ]:




