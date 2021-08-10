#!/usr/bin/env python
# coding: utf-8


import PyPDF2 as pdf

file_name = '/Users/stellarnode/Desktop/ZoharRussia_copy.pdf.pdf'

delta = 215

table_of_content = [
    ("Пролог", 215),
    ("Берешит А", 248),
    ("Ноа", 345),
    ("Лех Леха", 384),
    ("Ваера", 429),
    ("Хаей Сара", 481),
    ("Толдот", 510),
    ("Ваеце", 537),
    ("Ваишлах", 580),
    ("Ваешев", 610),
    ("Микец", 640),
    ("Ваигаш", 668),
    ("Ваехи", 682)
]


print(table_of_content)

reader = pdf.PdfFileReader(file_name)
writer = pdf.PdfFileWriter()

print(reader.documentInfo)

num_pages = reader.numPages
title_pages = []

page = reader.getPage(0)
text = page.extractText()

print(len(text))
print(text.splitlines()[0])
# print(text.encode('utf-8').decode('utf-8'))
# print(text)


for i in range(0, num_pages):
    page = reader.getPage(i)
    text = page.extractText()
    x = len(text)
    if x < 300 and x > 260:
        title_pages.append(i)
        print('page ' + str(i) + ' ' + text.splitlines()[0])

title_pages.append(num_pages)
print(len(title_pages))

for i in title_pages:
    if i < num_pages:
        start_page = i
        end_page = title_pages[title_pages.index(i) + 1]
        page_range = str(start_page) + ":" + str(end_page)
        merger = pdf.PdfFileMerger()
        merger.append(file_name, pages = pdf.PageRange(page_range))
        section = str(start_page + 1) + '_section_' + str(title_pages.index(i) + 1) + '.pdf'
        folder = '/Users/stellarnode/Desktop/sections/'
        print(page_range)
        print(folder + section)
        # merger.write(folder + section)
    else:
        print('DONE')




