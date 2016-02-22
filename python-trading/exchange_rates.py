import urllib2 as url
import openpyxl as xl
import json

CURRENCY_LAYER_API_KEY = "96c83b8075825e87ee1b9f9e78209af5"
API_ENDPOINT = "http://apilayer.net/api/"

def main():
    wb = xl.load_workbook("excel/financial status_2016_test.xlsx", read_only=False)
    sheet_names = wb.get_sheet_names()
    if "Currencies" in sheet_names:
        wb_currencies = wb.get_sheet_by_name("Currencies")

        # print type(wb_currencies), " ", wb_currencies.title
        print_current_rates(wb_currencies)
        data = get_json()

        # print data
        write_excel(data["quotes"], wb_currencies)
        print "Writing file..."
        wb.save("excel/financial_status_2016_out_py.xlsx")
        print "Done."
    else:
        print "Cannot find sheet Currencies"
        exit()

def get_json():
    my_key = u"?access_key=" + CURRENCY_LAYER_API_KEY
    source = u"&source=USD"
    currencies = u"&currencies=RUB,EUR,GBP,CHF"
    req_link = API_ENDPOINT + u"live" + my_key + source + currencies

    print "Retrieving data from currencylayer.com ..."

    connection = url.urlopen(req_link)
    response =  connection.read()
    connection.close()
    result = json.loads(response)

    if result:
        return result
    else:
        print "Could not fetch currency data."

def write_excel(data, sheet):
    if "USDRUB" in data:
        sheet["C4"].value = round(data["USDRUB"], 6)
        print "=> updated USDRUB: ", sheet["C4"].value
    if "USDEUR" in data:
        sheet["D4"].value = round(1 / data["USDEUR"], 6)
        print "=> updated EURUSD: ", sheet["D4"].value
    if "USDCHF" in data:
        sheet["E4"].value = round(1 / data["USDCHF"], 6)
        print "=> updated CHFUSD: ", sheet["E4"].value
    if "USDGBP" in data:
        sheet["F4"].value = round(1 / data["USDGBP"], 6)
        print "=> updated GBPUSD: ", sheet["F4"].value

def print_current_rates(sheet):
    print "=> previous USDRUB: ", sheet["C4"].value
    print "=> previous EURUSD: ", sheet["D4"].value
    print "=> previous CHFUSD: ", sheet["E4"].value
    print "=> previous GBPUSD: ", sheet["F4"].value


if __name__ == "__main__":
    main()