#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
from pandas.io.json import json_normalize
from datetime import datetime, timedelta
from pytz import timezone
from dateutil.tz import tzlocal
import smtplib as smtp
from getpass import getpass
import urllib, json

# creds below should contain: BASE_URL, USERNAME, PASSWORD_ENCODED_FOR_HTML,
# MERCHANT, EMAIL, EMAIL_PASSWORD, DESTINATION_EMAILS_ARRAY, SMTP_SERVER
import daily_rbs_payment_credentials as creds

base_url = creds.BASE_URL
username = creds.USERNAME
password = creds.PASSWORD_ENCODED_FOR_HTML
merchant = creds.MERCHANT

today = datetime.now(tzlocal()).astimezone(timezone('Europe/Moscow'))
delta = 1

# test cases
# today = datetime(2020, 1, 30, 6)
# today = datetime(2019, 12, 31, 21, 59)
# today = datetime(2020, 1, 31, 21, 59)
# today = datetime(2019, 11, 29, 6)
# today = datetime(2020, 2, 2, 12)

text_to_send = ''

def format_str_zeros(x):
    if x < 10:
        out = '0' + str(x)
    else:
        out = str(x)
    return out

def create_datetime_search_str(dt):
    year = str(dt.year)
    month = format_str_zeros(dt.month)
    day = format_str_zeros(dt.day)
    hour = format_str_zeros(dt.hour)
    minute = format_str_zeros(dt.minute)
    second = format_str_zeros(dt.second)
    return year + month + day + hour + minute + second

def construct_url(base_url, username, password, page, start, end, merchant):
    # MAXIMUM SUPPORTED PAGESIZE IS 200 (SEE RBS MANUAL)
    url = ''
    url = base_url
    url += "userName={0}&password={1}&".format(username, password)
    url += "language=ru&page={0}&size=200&from={1}&to={2}&transactionStates=DEPOSITED&".format(page, start, end)
    url += "merchants={}&searchByCreatedDate=false".format(merchant)
    return url

def print_timeframes(period, start, end):
    print(period + ' ' + 'report timeframe:')
    print (start, end)

### CALCULATE START AND END DATETIMES FOR REQUESTS (DAY, MONTH, YEAR)

### ... for the day

if today.hour <= 9 or delta > 1:
    day_before = today - timedelta(days = delta)
    day_before = day_before.replace(hour = 0, minute = 0, second = 0)
else:
    day_before = today.replace(hour = 0, minute = 0, second = 0)

# if today.hour < 22:
#     today = today.replace(hour = today.hour + 2)

start = create_datetime_search_str(day_before)
end = create_datetime_search_str(today)
print_timeframes('daily', start, end)

start_formatted = datetime.strptime(start, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M')
end_formatted = datetime.strptime(end, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M')
print(start_formatted, end_formatted)

### ... for the month

# Uncomment the following line and comment the line after it to get a specific month report and not the current month report
# month_beginning = today.replace(month = 2, day = 1, hour = 0, minute = 0, second = 0, microsecond = 0)
month_beginning = today.replace(day = 1, hour = 0, minute = 0, second = 0, microsecond = 0)
month_start = create_datetime_search_str(month_beginning)

if month_beginning.month == 12:
    month_end_dt = month_beginning.replace(year = month_beginning.year + 1)
    month_end_dt = month_end_dt.replace(month = 1)
else:
    month_end_dt = month_beginning.replace(month = month_beginning.month + 1)

month_end = create_datetime_search_str(month_end_dt)

print_timeframes('monthly', month_start, month_end)

### ... for the year

year_dt = today.replace(month = 1, day = 1, hour = 0, minute = 0, second = 0, microsecond = 0)
year_start = create_datetime_search_str(year_dt)
year_end = create_datetime_search_str(year_dt.replace(year = year_dt.year + 1))

print_timeframes('yearly', year_start, year_end)


################################################################################
################################################################################
################################################################################


def calculate_sales(report):
    report['amountFloat'] = report['amount'].apply(lambda x: float(x) / 100)
    return report['amountFloat'].sum()

def combine_report_pages(response_json, report):
    if response_json['orderStatuses']:
        report_page = json_normalize(response_json['orderStatuses'])
        return report.append(report_page, ignore_index=True)
    else:
        return report

def get_complete_report(base_url, username, password, start_page, start, end, merchant):
    report = pd.DataFrame()
    total_records = 0
    number_of_pages = 0
    url_for_period = construct_url(base_url, username, password, start_page, start, end, merchant)
    print(url_for_period + '\n')
    
    with urllib.request.urlopen(url_for_period) as url:
        report_first_page = json.loads(url.read().decode())
        report = combine_report_pages(report_first_page, report)
        
        if report_first_page and report_first_page['totalCount'] > 0 and report_first_page['pageSize'] > 0:
            total_records = report_first_page['totalCount']
            page_size = report_first_page['pageSize']
            number_of_pages = int(total_records / page_size) + 1
                
            for i in range(1, number_of_pages):
                url_for_page = construct_url(base_url, username, password, i, start, end, merchant)
                with urllib.request.urlopen(url_for_page) as url:
                    report_page = json.loads(url.read().decode())
                    if report_page['orderStatuses']:
                        report = combine_report_pages(report_page, report)

    return {
        'report': report,
        'total_records': total_records,
        'number_of_pages': number_of_pages
    }


def create_output_for_daily_report(report_full):
    text_to_send_daily = ''
    report = report_full[['amount', 'bankInfo.bankName', 'orderDescription', 'cardAuthInfo.cardholderName', 'cardAuthInfo.paymentSystem', 'ip', 'orderNumber']].copy()    
    report['Date'] = report_full['authDateTime'].apply(lambda x: datetime.fromtimestamp(x // 1000, tzlocal()).astimezone(timezone('Europe/Moscow')).isoformat(sep='T'))
    report['customterEmail'] = report_full['merchantOrderParams'].apply(lambda x: x[0]['value'])
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

    text_to_send_daily = report.to_string() + '\n\n\n'

    report['DAY TOTAL'] = report['DATE'].apply(lambda x: x[:10])
    report['TOTAL'] = report['AMOUNT']
    # text_to_send_daily += 'Sales from from {} to {}:'.format(start_formatted, end_formatted) + '\n'
    text_to_send_daily += report.groupby(by='DAY TOTAL')['TOTAL'].sum().to_string()

    return text_to_send_daily

### DAILY REPORT

print('\ndaily payments report...')

daily_report_obj = get_complete_report(base_url, username, password, 0, start, end, merchant)
daily_report = daily_report_obj['report']

if not daily_report.empty:
    total_sales_daily = calculate_sales(daily_report)
    text_to_send_daily = 'List of payments from {} to {}: \n\n'.format(start_formatted, end_formatted)
    text_to_send_daily += create_output_for_daily_report(daily_report)
else:
    text_to_send_daily = 'No completed payments from {} to {}.\n\n'.format(start_formatted, end_formatted)

### MONTHLY REPORT

print('\nmonthly payments report...')

monthly_report_obj = get_complete_report(base_url, username, password, 0, month_start, month_end, merchant)
monthly_report = monthly_report_obj['report']
total_payments_monthly = monthly_report_obj['total_records']
text_to_send_monthly = '\n\nMONTH TOTAL {}'.format(str(month_beginning.year) + '-' + format_str_zeros(month_beginning.month))

if not monthly_report.empty:
    total_sales_monthly = calculate_sales(monthly_report)
    text_to_send_monthly += '\nCompleted b2c transactions: {}'.format(total_payments_monthly)
    text_to_send_monthly += '\nRBS registered b2c sales: {} (incl. VAT)'.format(total_sales_monthly)
else:
    text_to_send_monthly += '\nNo completed payments this month yet.'    

### YEARLY REPORT

print('\nyearly payments report...')

yearly_report_obj = get_complete_report(base_url, username, password, 0, year_start, year_end, merchant)
yearly_report = yearly_report_obj['report']
total_payments_yearly = yearly_report_obj['total_records']
text_to_send_yearly = '\n\nYEAR TOTAL {}'.format(str(today.year))

if not yearly_report.empty:
    total_sales_yearly = calculate_sales(yearly_report)
    text_to_send_yearly += '\nCompleted b2c transactions: {}'.format(total_payments_yearly)
    text_to_send_yearly += '\nRBS registered b2c sales: {} (incl. VAT)'.format(total_sales_yearly)
else:
    text_to_send_yearly += '\nNo completed payments this year yet.' 

### FULL REPORT TO SEND

text_to_send = text_to_send_daily + text_to_send_monthly + text_to_send_yearly
print('\n\nfinal report to be sent by email...')
print(text_to_send)
print('\n\nSENDING EMAIL...')

### SEND REPORT BY EMAIL ###

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

print('\n\nDONE.')

###




