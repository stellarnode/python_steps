import PyPDF2 as pdf

file_name = '/Users/stellarnode/Desktop/ZoharRussia_copy.pdf.pdf'

delta = 215

table_of_content = [
    ("Пролог", 215),
    ("Берешит А", 248),
    ("Берешит Б", 299),
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
    ("Ваехи", 682),
    ("Шмот", 771),
    ("Ваэра", 815),
    ("Бо", 838),
    ("Бешалах", 865),
    ("Итро", 918),
    ("Мишпатим", 978),
    ("Трума", 1048),
    ("Сафра Децниута", 1156),
    ("Тэцаве", 1163),
    ("Ки Тиса", 1181),
    ("Ваякхель", 1196),
    ("Пекудей", 1251),
    ("Ваикра", 1358),
    ("Цав", 1411),
    ("Шмини", 1434),
    ("Тазриа", 1449),
    ("Мецора", 1471),
    ("Ахарей Мот", 1480),
    ("Кедошим", 1531),
    ("Эмор", 1549),
    ("Бехар", 1592),
    ("Бехукотай", 1603),
    ("Бамидбар", 1612),
    ("Насо", 1622),
    ("Беаалотха", 1684),
    ("Шлах Леха", 1702),
    ("Корах", 1745),
    ("Хукат", 1754),
    ("Балак", 1765),
    ("Пинхас", 1830),
    ("Матот", 1944),
    ("Ваэтханан", 1945),
    ("Экев", 1970),
    ("Шофтим", 1980),
    ("Ки Тецэ", 1983),
    ("Ваелех", 2003),
    ("Хаазину", 2010)
]

print(len(table_of_content))
print(table_of_content)

reader = pdf.PdfFileReader(file_name)
writer = pdf.PdfFileWriter()

print(reader.documentInfo)

num_pages = reader.numPages
table_of_content.append(("End", num_pages + delta))

for i in table_of_content:
    if i[1] - delta < num_pages:
        start_page = i[1] - delta
        end_page = table_of_content[table_of_content.index(i) + 1][1] - delta
        page_range = str(start_page) + ":" + str(end_page)
        merger = pdf.PdfFileMerger()
        merger.append(file_name, pages = pdf.PageRange(page_range))
        section = str(start_page + 1) + "_" + i[0] + "_" + str(table_of_content.index(i) + 1) + '.pdf'
        folder = '/Users/stellarnode/Desktop/sections/'
        print(page_range)
        print(folder + section)
        merger.write(folder + section)
    else:
        print('DONE')