import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sbn
from datetime import datetime
import requests
import json
from pandas.io.json import json_normalize
from pytz import timezone
from dateutil.tz import tzlocal
import smtplib as smtp

import alfacrm_daily_lessons_credentials as creds

base_url = creds.BASE_URL
login_url = base_url + creds.LOGIN_URL
email = creds.LOGIN
api_key = creds.API_KEY

# 4 = Сопровождение, 3 = Продажи
branch = 4
text_to_send =''

today = datetime.now(tzlocal()).astimezone(timezone('Europe/Moscow'))

def format_str_zeros(x):
    if x < 10:
        out = '0' + str(x)
    else:
        out = str(x)
    return out

year = str(today.year)
month = format_str_zeros(today.month)
year_month = str(year) + '-' + month

print('Current month: ', year_month)

data = {'email': email, 'api_key': api_key}
response = requests.post(login_url, json = data)
json_response = response.json()
headers = {'X-ALFACRM-TOKEN': json_response['token']}

# response = requests.post(base_url + 'v2api/branch/index', headers = headers, data = {"is_active":1,"page":0})
# response = requests.post(base_url + 'v2api/4/customer/index', headers = headers, data = {"lead_status_id":1,"page":0})
# json_response = response.json()
# data = json_normalize(json_response['items'])


def get_report_data(base_url, branch, year):
    response = requests.post(base_url + 'v2api/{}/lesson/index'.format(branch), headers = headers)
    json_response = response.json()
    data = json_normalize(json_response['items'])

    number_of_pages = int(json_response['total'] / json_response['count']) + 1

    print('Total number of pages available: ', number_of_pages)

    for i in range(1, number_of_pages):
        response_i = requests.post(base_url + 'v2api/{}/lesson'.format(branch), headers = headers, json = {'page': i})
        json_response_i = response_i.json()
        data_i = json_normalize(json_response_i['items'])
        data = data.append(data_i, ignore_index = True)
        # print(str(i) + ' . ', end = '')
        if data_i['date'][0][:4] != year:
            print('Number of pages downloaded: ', i + 1)
            # print(data_i)
            break
    return data

def convert_id_to_type(x):
    types = ['', 'One-on-One', '', 'Intro', 'Gift', 'Group']
    return types[x]

def convert_id_to_subject(x):
    subjects = ['', 'English', 'Math', 'Russian']
    return subjects[x]

def unpack_and_prepare_data(data, year):
    data['MONTH'] = data['date'].apply(lambda x: x[:7])
    data['year'] = data['date'].apply(lambda x: x[:4])
    select = data[data['year'] == year].copy()
    select['id_2'] = select['details'].apply(lambda x: x[0]['id'])
    select['customer_id'] = select['details'].apply(lambda x: x[0]['customer_id'])
    select['lesson_id'] = select['details'].apply(lambda x: x[0]['lesson_id'])
    select['reason_id'] = select['details'].apply(lambda x: x[0]['reason_id'])
    select['is_attend'] = select['details'].apply(lambda x: x[0]['is_attend'])
    select['grade'] = select['details'].apply(lambda x: x[0]['grade'])
    select['bonus'] = select['details'].apply(lambda x: x[0]['bonus'])
    select['note'] = select['details'].apply(lambda x: x[0]['note'])
    select['ctt_id'] = select['details'].apply(lambda x: x[0]['ctt_id'])
    select['commission'] = select['details'].apply(lambda x: x[0]['commission'])
    select['price'] = select['commission'].apply(lambda x: float(x))
    select['LESSON TYPE'] = select['lesson_type_id'].apply(convert_id_to_type)
    select['SUBJECT'] = select['subject_id'].apply(convert_id_to_subject)
    return select


### REGULAR LESSONS REPORT

branch = 4
data = get_report_data(base_url, branch, year)
select = unpack_and_prepare_data(data, year)

# print('DATA')
# print(data)


# select['id_2'] = select['details'].apply(lambda x: x[0]['id'])
# select['customer_id'] = select['details'].apply(lambda x: x[0]['customer_id'])
# select['lesson_id'] = select['details'].apply(lambda x: x[0]['lesson_id'])
# select['reason_id'] = select['details'].apply(lambda x: x[0]['reason_id'])
# select['is_attend'] = select['details'].apply(lambda x: x[0]['is_attend'])
# select['grade'] = select['details'].apply(lambda x: x[0]['grade'])
# select['bonus'] = select['details'].apply(lambda x: x[0]['bonus'])
# select['note'] = select['details'].apply(lambda x: x[0]['note'])
# select['ctt_id'] = select['details'].apply(lambda x: x[0]['ctt_id'])
# select['commission'] = select['details'].apply(lambda x: x[0]['commission'])
# select['price'] = select['commission'].apply(lambda x: float(x))

# print('SELECT')
# print(select)




total_annual_revenue = select['price'].sum()
total_annual_revenue_by_month = select.groupby(by='MONTH', group_keys = False)['price'].sum()
total_annual_paid_lessons = select[select['price'] > 0]['customer_id'].count()
total_annual_paid_lessons_by_month = select[select['price'] > 0].groupby(by='MONTH')['customer_id'].count()


# total_number_of_lessons = select[(select['MONTH'] == year_month) & (select['price'] > 0)].groupby(by='LESSON TYPE')['customer_id'].count()
# lessons_by_subjects = select[(select['MONTH'] == year_month) & (select['price'] > 0)].groupby(by='SUBJECT')['customer_id'].count()
# # paid_lessons_by_type = select[(select['date-month'] == year_month) & (select['price'] > 0)].groupby(by='lesson_type_id')['customer_id'].count()
# lessons_by_type = select[select['MONTH'] == year_month].groupby(by='LESSON TYPE')['customer_id'].count()
# really_attended_lessons = select[(select['MONTH'] == year_month) & (select['price'] > 0) & (select['is_attend'] == 1)].groupby(by='LESSON TYPE')['customer_id'].count()
# number_of_unpaid_by_subject = select[(select['MONTH'] == year_month) & (select['price'] == 0) & (select['is_attend'] == 1)].groupby(by='SUBJECT')['customer_id'].count()
# number_of_unpaid_by_type = select[(select['MONTH'] == year_month) & (select['price'] == 0) & (select['is_attend'] == 1)].groupby(by='LESSON TYPE')['customer_id'].count()

regular_active_clients_by_subject = select[(select['MONTH'] == year_month) & ((select['is_attend'] == 1) | (select['price'] > 0))].groupby(by='SUBJECT')['customer_id'].nunique()
active_clients_by_subject = select[(select['MONTH'] == year_month) & (select['price'] > 0)].groupby(by='SUBJECT')['customer_id'].nunique()
active_clients_by_subject_free = select[(select['MONTH'] == year_month) & (select['price'] == 0) & (select['is_attend'] == 1)].groupby(by='SUBJECT')['customer_id'].nunique()

# print('\nTotal revenue earned this year:\n', total_annual_revenue_by_month.to_string())
# print('TOTAL: ', total_annual_revenue)
# print('\nTotal paid lessons this year:\n', total_annual_paid_lessons_by_month.to_string())
# print('TOTAL: ', total_annual_paid_lessons)
# print('\nTotal number of paid lessons this month:\n', total_number_of_lessons.to_string())
# print('\nIncluding lessons really attended by customers:\n', really_attended_lessons.to_string())
# print('\nNumber of paid lessons by subject:\n', lessons_by_subjects.to_string())
# # print('\nNumber of paid lessons by type:\n', paid_lessons_by_type.to_string())
# print('\nNumber of lessons by type, including missed:\n', lessons_by_type.to_string())
# print('\nNumber of unpaid but attended regular lessons by subject:\n', number_of_unpaid_by_subject.to_string())
# print('\nNumber of unpaid but attended regular lessons by type:\n', number_of_unpaid_by_type.to_string())
# print('\nNumber of regular active clients who attended classes this month by subject:\n', regular_active_clients_by_subject.to_string())
# print('\nNumber of active paid clients by subject this month:\n', active_clients_by_subject.to_string())
# print('\nNumber of active clients who attended free lessons by subject this month:\n', active_clients_by_subject_free.to_string())

revenue_pivot = pd.pivot_table(select[select['MONTH'] == year_month], values = 'price', index = 'SUBJECT', columns = 'LESSON TYPE', aggfunc = np.sum)
paid_lessons_pivot = pd.pivot_table(select[(select['MONTH'] == year_month) & (select['price'] > 0)], values = 'lesson_id', index = 'SUBJECT', columns = 'LESSON TYPE', aggfunc = len)
gift_lessons_pivot = pd.pivot_table(select[(select['MONTH'] == year_month) & ((select['price'] == 0) & (select['is_attend'] == 1))], values = 'lesson_id', index = 'SUBJECT', columns = 'LESSON TYPE', aggfunc = len)
gift_lessons_total = select[(select['MONTH'] == year_month) & ((select['price'] == 0) & (select['is_attend'] == 1))]['lesson_id'].count()
all_lessons_pivot = pd.pivot_table(select[select['MONTH'] == year_month], values = 'lesson_id', index = 'SUBJECT', columns = 'LESSON TYPE', aggfunc = len)
all_lessons_total = select[select['MONTH'] == year_month]['lesson_id'].count()

daily_paid_lessons_count = select[(select['MONTH'] == year_month) & (select['price'] > 0)].groupby(by='date')['lesson_id'].count()


text_to_send += '\n(BETA) SNAPSHOT OF ALFACRM DATA AT {}\n\n'.format(today.strftime('%Y-%m-%d %H:%M'))
text_to_send += '\n\n--- REGULAR LESSONS in {} ---\n\n'.format(year_month)
text_to_send += '\nTotal revenue earned this year (with VAT):\n\n' + total_annual_revenue_by_month.to_string()
text_to_send += '\nTOTAL: ' + str(total_annual_revenue)
text_to_send += '\n\n\nTotal paid lessons this year:\n\n' + total_annual_paid_lessons_by_month.to_string()
text_to_send += '\nTOTAL: ' + str(total_annual_paid_lessons)

text_to_send += '\n\n\nRevenue by subject and lesson type (with VAT):\n\n' + revenue_pivot.to_string()
text_to_send += '\n\n\nPaid lessons by subject and lesson type:\n\n' + paid_lessons_pivot.to_string()
text_to_send += '\n\n\nGift lessons by subject and lesson type:\n\n' + gift_lessons_pivot.to_string()
text_to_send += '\nTOTAL: ' + str(gift_lessons_total)
text_to_send += '\n\n\nTotal lessons (including missed) by subject and lesson type:\n\n' + all_lessons_pivot.to_string()
text_to_send += '\nTOTAL: ' + str(all_lessons_total)

# text_to_send += '\n\n\n\n\n'
# text_to_send += '\n\nTotal number of paid lessons this month:\n' + total_number_of_lessons.to_string()
# text_to_send += '\n\nIncluding lessons really attended by customers:\n' + really_attended_lessons.to_string()
# text_to_send += '\n\nNumber of paid lessons by subject:\n' + lessons_by_subjects.to_string()
# text_to_send += '\n\nNumber of lessons by type, including missed:\n' + lessons_by_type.to_string()
# text_to_send += '\n\nNumber of unpaid but attended regular lessons by subject:\n' + number_of_unpaid_by_subject.to_string()
# text_to_send += '\n\nNumber of unpaid but attended regular lessons by type:\n' + number_of_unpaid_by_type.to_string()


text_to_send += '\n\n\nNumber of regular active clients who attended classes this month by subject:\n\n' + regular_active_clients_by_subject.to_string()
text_to_send += '\n\n\nNumber of active paid clients by subject this month:\n\n' + active_clients_by_subject.to_string()
text_to_send += '\n\n\nNumber of active clients who attended free lessons by subject this month:\n\n' + active_clients_by_subject_free.to_string()
text_to_send += '\n\n\nDaily paid lessons count:\n\n' + daily_paid_lessons_count.to_string()


# print(text_to_send)


### INTRO LESSONS REPORT

branch = 3
data = get_report_data(base_url, branch, year)
select = unpack_and_prepare_data(data, year)


total_annual_revenue = select['price'].sum()
total_annual_revenue_by_month = select.groupby(by='MONTH', group_keys = False)['price'].sum()
total_annual_attended_lessons = select[(select['is_attend'] == 1) | (select['price'] > 0)]['customer_id'].count()
total_annual_attended_lessons_by_month = select[(select['is_attend'] == 1) | (select['price'] > 0)].groupby(by='MONTH')['customer_id'].count()


regular_active_clients_by_subject = select[(select['MONTH'] == year_month) & ((select['is_attend'] == 1) | (select['price'] > 0))].groupby(by='SUBJECT')['customer_id'].nunique()
active_clients_by_subject = select[(select['MONTH'] == year_month) & (select['price'] > 0)].groupby(by='SUBJECT')['customer_id'].nunique()
active_clients_by_subject_free = select[(select['MONTH'] == year_month) & (select['price'] == 0) & (select['is_attend'] == 1)].groupby(by='SUBJECT')['customer_id'].nunique()

revenue_pivot = pd.pivot_table(select[select['MONTH'] == year_month], values = 'price', index = 'SUBJECT', columns = 'LESSON TYPE', aggfunc = np.sum)
paid_lessons_pivot = pd.pivot_table(select[(select['MONTH'] == year_month) & (select['price'] > 0)], values = 'lesson_id', index = 'SUBJECT', columns = 'LESSON TYPE', aggfunc = len)
attended_lessons_pivot = pd.pivot_table(select[(select['MONTH'] == year_month) & ((select['price'] > 0) | (select['is_attend'] == 1))], values = 'lesson_id', index = 'SUBJECT', columns = 'LESSON TYPE', aggfunc = len)
attended_lessons_total = select[(select['MONTH'] == year_month) & ((select['price'] > 0) | (select['is_attend'] == 1))]['lesson_id'].count()
all_lessons_pivot = pd.pivot_table(select[select['MONTH'] == year_month], values = 'lesson_id', index = 'SUBJECT', columns = 'LESSON TYPE', aggfunc = len)
all_lessons_total = select[select['MONTH'] == year_month]['lesson_id'].count()

daily_attended_lessons_count = select[(select['MONTH'] == year_month) & ((select['price'] > 0) | (select['is_attend'] == 1))].groupby(by='date')['lesson_id'].count()


text_to_send += '\n\n\n\n--- INTRO LESSONS in {} ---\n\n'.format(year_month)

text_to_send += '\nTotal revenue earned this year (with VAT):\n\n' + total_annual_revenue_by_month.to_string()
text_to_send += '\nTOTAL: ' + str(total_annual_revenue)
text_to_send += '\n\n\nTotal attended lessons this year:\n\n' + total_annual_attended_lessons_by_month.to_string()
text_to_send += '\nTOTAL: ' + str(total_annual_attended_lessons)

text_to_send += '\n\n\nRevenue by subject and lesson type (with VAT):\n\n' + revenue_pivot.to_string()
text_to_send += '\n\n\nPaid lessons by subject and lesson type:\n\n' + paid_lessons_pivot.to_string()
text_to_send += '\n\n\nAttended lessons by subject and lesson type:\n\n' + attended_lessons_pivot.to_string()
text_to_send += '\nTOTAL: ' + str(attended_lessons_total)
text_to_send += '\n\n\nTotal lessons (including missed) by subject and lesson type:\n\n' + all_lessons_pivot.to_string()
text_to_send += '\nTOTAL: ' + str(all_lessons_total)


text_to_send += '\n\n\nNumber of intro active clients who attended classes this month by subject:\n\n' + regular_active_clients_by_subject.to_string()
text_to_send += '\n\n\nNumber of intro paid active clients by subject this month:\n\n' + active_clients_by_subject.to_string()
text_to_send += '\n\n\nNumber of active clients who attended free lessons by subject this month:\n\n' + active_clients_by_subject_free.to_string()
text_to_send += '\n\n\nDaily attended lessons count:\n\n' + daily_attended_lessons_count.to_string()


print(text_to_send)


print('\n\nSENDING EMAIL...')

### SEND REPORT BY EMAIL ###

email = creds.EMAIL
password = creds.EMAIL_PASSWORD
dest_email = creds.DESTINATION_EMAILS_ARRAY
subject = 'AlfaCRM Daily Data Snapshot for {}'.format(year_month)
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