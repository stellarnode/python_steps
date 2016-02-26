import urllib2 as url
import openpyxl as xl
import json

from datetime import date, timedelta

from currency_layer_api import CURRENCY_LAYER_API_KEY, API_ENDPOINT

def main():
    wb = xl.load_workbook("excel/financial status_2016_test.xlsx", read_only=False)
    sheet_names = wb.get_sheet_names()
    if "Currencies" in sheet_names:
        wb_currencies = wb.get_sheet_by_name("Currencies")

        # print type(wb_currencies), " ", wb_currencies.title
        print_previous_rates(wb_currencies)
        data = get_quotes_json()
        update_monthly_quotes(wb_currencies)

        # write data
        write_current_quotes_excel(data["quotes"], wb_currencies)
        print "Writing file..."
        wb.save("excel/financial_status_2016_out_py.xlsx")
        print "Done."
    else:
        print "Cannot find sheet Currencies"
        exit()


def get_quotes_json(period="live", req_date=None):
    my_key = u"?access_key=" + CURRENCY_LAYER_API_KEY
    source = u"&source=USD"
    currencies = u"&currencies=RUB,EUR,GBP,CHF"

    if period == "live" and req_date == None:
        req_link = API_ENDPOINT + u"live" + my_key + source + currencies
    elif req_date != None:
        req_link = API_ENDPOINT + u"historical" + my_key + source + currencies + u"&date=" + req_date
    else:
        print "Parameters missing for request."
        return

    # print "Retrieving data from currencylayer.com ..."

    connection = url.urlopen(req_link)
    response = connection.read()
    connection.close()
    result = json.loads(response)

    if result:
        return result
    else:
        print "Could not fetch currency data."


def update_monthly_quotes(sheet):
    print "Updating historical quotes..."
    i = 8
    curr_cell = "B" + str(i)

    def get_date(curr_cell):
        year = sheet[curr_cell].value.year
        month = sheet[curr_cell].value.month
        day = sheet[curr_cell].value.day
        cell_date = date(year, month, day)
        return cell_date

    def write_hist_quotes(row, quotes):
        if "USDRUB" in quotes:
            sheet["C" + str(i)].value = round(quotes["USDRUB"], 6)
        if "USDEUR" in quotes:
            sheet["D" + str(i)].value = round(1 / quotes["USDEUR"], 6)
        if "USDCHF" in quotes:
            sheet["E" + str(i)].value = round(1 / quotes["USDCHF"], 6)
        if "USDGBP" in quotes:
            sheet["F" + str(i)].value = round(1 / quotes["USDGBP"], 6)

    while (get_date(curr_cell) < date.today()) and (sheet[curr_cell] != None):
        hist_date = get_date(curr_cell)
        rates = get_quotes_json("historical", hist_date.isoformat())
        hist_quotes = rates["quotes"]
        write_hist_quotes(i, hist_quotes)
        print "USDRUB on ", hist_date.isoformat(), " @ ", hist_quotes["USDRUB"]
        i += 1
        curr_cell = "B" + str(i)

    print "Historical quotes updated."

def write_current_quotes_excel(data, sheet):
    print "Updating current quotes..."
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

def print_previous_rates(sheet):
    print "=> previous USDRUB: ", sheet["C4"].value
    print "=> previous EURUSD: ", sheet["D4"].value
    print "=> previous CHFUSD: ", sheet["E4"].value
    print "=> previous GBPUSD: ", sheet["F4"].value


if __name__ == "__main__":
    main()