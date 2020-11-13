#!/usr/bin/env python
# coding: utf-8

# In[28]:


import pandas as pd
import numpy as np
import tabula as wrapper
# from tabula import wrapper
import requests
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


# In[2]:


url = creds.BASE_URL
date = str(datetime.now()).split(' ')[0]

print(date)


# In[3]:


print('Check if /temp_data directory exists...')
print(os.path.exists('./temp_data'))

if not os.path.exists('./temp_data'):
    os.system('mkdir temp_data')


# In[4]:


r = requests.get(url, stream = True)
file_name = './temp_data/romania_files_2018.pdf'

print('Loading file...', end="", flush=True)

with open(file_name, 'wb') as fd:
    for chunk in r.iter_content(102400):
        fd.write(chunk)
        print('...', end="", flush=True)

print('[DONE]')

# In[5]:


# wrapper.convert_into(file_name, (file_name + '.csv'), output_format='csv', pages='all')


# In[6]:


df = wrapper.read_pdf(file_name, pages='1770-1869', pandas_options = {'header': None}, output_format = 'dataframe', guess = False)
df = pd.concat(df)

# In[7]:


df.head()


# In[8]:


# df.columns = ['NR. DOSAR', 'DATA ÎNREGISTRĂRII', 'TERMEN', 'SOLUȚIE']
df.columns = ['NR. DOSAR', 'DATA INREGISTRARII', 'TERMEN', 'SOLUTIE']


# In[9]:


# print(df.shape)
# print(type(df.iloc[0,2]))


# In[10]:


select = ['80190/RD/2018', '80196/RD/2018', '80200/RD/2018', '80864/RD/2018']

we = df[df['NR. DOSAR'].apply(lambda x: x in select)]


# In[11]:

print('Our file numbers:\n')
print(we)
print('\n\n\n')


# In[12]:


# for x in we['TERMEN']:
#     print(type(x))

we_termen = we[we['TERMEN'].apply(lambda x: isinstance(x, str)) | we['SOLUTIE'].apply(lambda x: isinstance(x, str))]
# print(we_termen)


# In[13]:


if not we_termen.empty:
    text_to_send = 'Romania File Checker found the following matches: \n\n\n' + we_termen.to_string()
    match = True
else:
    text_to_send = '\n' + 'No matches found by Romania File Checker for now.'
    match = False
    
print(text_to_send)

# In[16]:

base_url = creds.BASE_URL_ORDERS
# data = requests.get('http://cetatenie.just.ro/index.php/ro/ordine/articol-11')
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
data = requests.get('http://cetatenie.just.ro/ordine/#1578313750617-4f53573c-3c20', headers = headers)
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
clean_hrefs = list(filter(lambda x: ('2019' in x) or ('2020' in x) or ('2021' in x) or ('2022' in x) or ('2023' in x), clean_links))

print('-- links found:')
print(clean_links)

orders_found = []
select_file_numbers = ['80190/RD/2018', '80196/RD/2018', '80200/RD/2018', '80864/RD/2018', '80190/2018', '80196/2018', '80200/2018', '80864/2018']

text_to_send += '\n\n\n'

print('\n\n')

print('Checking issued Orders...', end="", flush=True)

for link in clean_hrefs:
    pdfName = link
    page = requests.get(pdfName, headers = headers)
    pdfPage = io.BytesIO(page.content)
    pdfReader = pdf.PdfFileReader(pdfPage) 
    page_content = ''
    for i in range(0, pdfReader.getNumPages()):
        page = pdfReader.getPage(i)
        page_content += page.extractText()
    for order_number in select_file_numbers:
        if order_number in page_content:
            orders_found.append((order_number, pdfName))
    print('...', end="", flush=True)

print('[DONE]' + '\n\n')

# Keeping unique values...
orders_found_clean = set(orders_found)

if len(orders_found_clean) == 0:
    search_result = 'No matches found in current issued Orders.'
    print(search_result)
    text_to_send = text_to_send + search_result + '\n'
else:
    match = True
    search_result = 'The following match(es) were found in issued Orders:\n'
    print(search_result)
    text_to_send = text_to_send + search_result + '\n'
    for link_tuple in orders_found_clean:
        print(link_tuple[0] + ': ' + link_tuple[1])
        text_to_send = text_to_send + link_tuple[0] + ': ' + link_tuple[1] + '\n'

print('\n\n')
print('Proceding to sending info by email...')
print('\n\n')

# In[17]:


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


# In[ ]:




