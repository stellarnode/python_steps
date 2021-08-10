#!/usr/bin/env python
# coding: utf-8


import pandas as pd
import numpy as np
import tabula as wrapper
# from tabula import wrapper
import requests
import urllib3
import shutil

from datetime import datetime
import os
import math
import smtplib as smtp
from getpass import getpass

from bs4 import BeautifulSoup as bs

import PyPDF2 as pdf
import io

# creds below should contain: BASE_URL, EMAIL, EMAIL_PASSWORD, DESTINATION_EMAILS_ARRAY, SMTP_SERVER
import romania_file_term_credentials as creds



url = creds.BASE_URL
date = str(datetime.now()).split(' ')[0]

print(date)




print('Check if /temp_data directory exists...')
print(os.path.exists('./temp_data'))

if not os.path.exists('./temp_data'):
    os.system('mkdir temp_data')



file_name = './temp_data/romania_files_2018.pdf'

print('Loading file...', end="", flush=True)

# Using just Urllib3
# http = urllib3.PoolManager()
# with open(file_name, 'wb') as out:
#     r = http.request('GET', url, preload_content = False)
#     shutil.copyfileobj(r, out)

# Using requests... This version wored before
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'}
r = requests.get(url, headers = headers, stream = True)
with open(file_name, 'wb') as fd:
    for chunk in r.iter_content(chunk_size = 102400):
        if chunk:
            fd.write(chunk)
            print('...', end="", flush=True)

# myfile = requests.get(url)
# open(file_name, 'wb').write(myfile.content)

print('[DONE]')



# wrapper.convert_into(file_name, (file_name + '.csv'), output_format='csv', pages='all')




df = wrapper.read_pdf(file_name, pages='2000-2050', pandas_options = {'header': None}, output_format = 'dataframe', guess = False)

# For older versions of Pandas use df = pd.concat([df]) in the following line
df = pd.concat(df)



df.head()




# df.columns = ['NR. DOSAR', 'DATA ÎNREGISTRĂRII', 'TERMEN', 'SOLUȚIE']
df.columns = ['NR. DOSAR', 'DATA INREGISTRARII', 'TERMEN', 'SOLUTIE']




# print(df.shape)
# print(type(df.iloc[0,2]))




select = ['80190/RD/2018', '80196/RD/2018', '80200/RD/2018', '80864/RD/2018']

we = df[df['NR. DOSAR'].apply(lambda x: x in select)]




print('Our file numbers:\n')
print(we)
print('\n\n\n')




# for x in we['TERMEN']:
#     print(type(x))

we_termen = we[we['TERMEN'].apply(lambda x: isinstance(x, str)) | we['SOLUTIE'].apply(lambda x: isinstance(x, str))]
# print(we_termen)




if not we_termen.empty:
    text_to_send = 'Romania File Checker found the following matches: \n\n\n' + we_termen.to_string()
    match = True
else:
    text_to_send = '\n' + 'No matches found by Romania File Checker for now.'
    match = False
    
print(text_to_send)


base_url = creds.BASE_URL_ORDERS
# data = requests.get('http://cetatenie.just.ro/index.php/ro/ordine/articol-11')
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
data = requests.get('http://cetatenie.just.ro/ordine-articolul-11/', headers = headers)
soup = bs(data.text, 'html.parser')
links = soup.findAll('a')

clean_links = []

for x in links:
    try:
        if x.attrs['href']:
            clean_links.append(x.attrs['href'])
    except:
        pass


clean_links = list(filter(lambda x: '.pdf' in x, clean_links))

def filter_links(link):
    split_link = link.split('/')
    file = split_link[-1]
    if ('2021' in file) or ('2022' in file) or ('2023' in file):
        out = True
    else:
        out = False
    return out

clean_hrefs = list(filter(filter_links, clean_links))

print('-- links found:')
print(clean_hrefs)

orders_found = []
files_skipped = []
select_file_numbers = ['80190/RD/2018', '80196/RD/2018', '80200/RD/2018', '80864/RD/2018', '80190/2018', '80196/2018', '80200/2018', '80864/2018', '4226/2018', '24358/2018']

text_to_send += '\n\n\n'

print('\n\n')

print('Checking issued Orders...', end="", flush=True)

# file_name_log = './temp_data/orders_output.txt'

# with open(file_name_log, 'w') as f:
#     f.write('')

# i = 0

for link in clean_hrefs:
    pdfName = link
    try:
        page = requests.get(pdfName, headers = headers)
        pdfPage = io.BytesIO(page.content)
        pdfReader = pdf.PdfFileReader(pdfPage) 
        page_content = ''
        for i in range(0, pdfReader.getNumPages()):
            page = pdfReader.getPage(i)
            page_content += page.extractText()
        
        # if i < 3:
        #     with open(file_name_log, 'a') as f:
        #         f.write(link + ':\n' + page_content + '\n\n')
        #     i += 1
        
        for order_number in select_file_numbers:
            if order_number in page_content:
                orders_found.append((order_number, pdfName))
        print('...', end="", flush=True)
    except:
        files_skipped.append(pdfName)
        pass
    

print('[DONE]' + '\n\n')

# Keeping unique values...
orders_found_clean = set(orders_found)

if len(orders_found_clean) == 0:
    search_result = 'No matches found in current issued Orders.'
    print(search_result)
    text_to_send = text_to_send + search_result + '\n'
else:
    match = True
    search_result = 'The following match(es) were found in issued Orders (some are included for test purposes):\n'
    print(search_result)
    text_to_send = text_to_send + search_result + '\n'
    for link_tuple in orders_found_clean:
        print(link_tuple[0] + ': ' + link_tuple[1])
        text_to_send = text_to_send + link_tuple[0] + ': ' + link_tuple[1] + '\n'

text_to_send = text_to_send + '\n'

if len(files_skipped) > 0:
    skipped_text = 'The following files were skipped due to errors:\n'
    text_to_send = text_to_send + skipped_text + '\n'
    for file in files_skipped:
        print(file)
        text_to_send = text_to_send + file + '\n'

print('\n\n')
print('Proceding to sending info by email...')
print('\n\n')



if match:
    email = creds.EMAIL
    password = creds.EMAIL_PASSWORD
    dest_email = creds.DESTINATION_EMAILS_ARRAY
    subject = 'File Checker Status'
    email_text = text_to_send

    message = 'From: {}\nTo: {}\nSubject: {}\n\n{}'.format('Romania Checker <' + email + '>',
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







