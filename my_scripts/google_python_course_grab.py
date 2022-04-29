from bs4 import BeautifulSoup as bs
import requests
import os

base_url = 'https://developers.google.com/edu/python'
base_url_google = 'https://developers.google.com'



def extract_html(url, div_class):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    data = requests.get(url, headers = headers)
    soup = bs(data.text, 'html.parser')

    try:
        section = soup.select('div[class*="' + div_class + '"]')[0]
    except:
        print('The div with class ' + div_class + ' not found for url: ' + url)
        return ''

    return section


nav_bar = extract_html(base_url, 'devsite-book-nav-wrapper')

nav_paths = nav_bar.findAll('a')

clean_nav_paths = []

for x in nav_paths:
    try:
        if x.attrs['href']:
            clean_nav_paths.append(x.attrs['href'])
    except:
        pass

print(clean_nav_paths)

print('Check if /temp_data directory exists...')
print(os.path.exists('./temp_data'))

if not os.path.exists('./temp_data'):
    os.system('mkdir temp_data')

print('Check if /temp_data/google directory exists...')
print(os.path.exists('./temp_data/google'))

if not os.path.exists('./temp_data/google'):
    os.system('mkdir ./temp_data/google')

file_name = './temp_data/google/youtube_links.txt'

print('Links to YouTube videos:')

with open(file_name, 'w+') as fd:
    for x in clean_nav_paths:
        if 'youtube.com' in x:
            print(x)
            fd.write(x + '\n')

print('\n' + file_name + ' - ready')
print('\n')
print('Course sections:')

for x in clean_nav_paths:
    if 'youtube.com' not in x:
        parts = x.split('/')
        file_name = './temp_data/google/'
        for elem in parts:
            file_name = file_name + elem + '_'
        file_name += '.html'

        link = base_url_google + x
        print('Checking link: ' + link)

        article = extract_html(link, 'devsite-article-body')

        for img in article.find_all('img'):
            img_url = img['src']
            if "http" not in img_url:
                img['src'] = base_url_google + img_url 

        for a in article.find_all('a'):
            href = a['href']
            if 'http' not in href:
                a['href'] = base_url_google + href

        with open(file_name, 'w+') as fd:
            fd.write(str(article))
        
        with open(file_name + '.txt', 'w+') as fd:
            fd.write(str(article))

        print(file_name + ' - ready')
        print(file_name + '.txt - ready')







