var XLSX = require("/Users/filmmaker/npm-global/lib/node_modules/xlsx");
var http = require("http");

var CURRENCY_LAYER_API_KEY = "96c83b8075825e87ee1b9f9e78209af5";
var API_ENDPOINT = "http://apilayer.net/api/";

var readOptions = {
    cellFormula: true,
    cellHTML: true,
    cellNF: true,
    cellStyles: true,
    cellDates: true,
    sheetStubs: true,
    bookDeps: true,
    bookFiles: true,
    bookVBA: true
};

var wb = XLSX.readFile("excel/financial status_2016_test.xlsx", readOptions);

if (wb.SheetNames.indexOf("Currencies") > -1) {
    var wb_currencies = wb.Sheets["Currencies"];
    printCurrent(wb_currencies);
    getData(updateValues);
} else {
    console.log("Could not open file.");
    process.exit();
}


function getData(next) {
    var my_key = "?access_key=" + CURRENCY_LAYER_API_KEY;
    var source = "&source=USD";
    var currencies = "&currencies=RUB,EUR,GBP,CHF";
    var req_link = API_ENDPOINT + "live" + my_key + source + currencies;
    var body = "";

    console.log("Reading data from currencylayer.com ...");

    http.get(req_link, function(res) {
        res.on('data', function(chunk){
            body += chunk;
        });

        res.on('end', function(){
            var response = JSON.parse(body);
            next(response, wb_currencies, saveFileAs);
        });
    }).on("error", function(err) {
        console.log("Could not fetch data.");
    });
}

function printCurrent(sheet) {
    console.log("=> previous USDRUB: ", sheet["C4"].v);
    console.log("=> previous EURUSD: ", sheet["D4"].v);
    console.log("=> previous CHFUSD: ", sheet["E4"].v);
    console.log("=> previous GBPUSD: ", sheet["F4"].v);
}

function updateValues(data, sheet, next) {
    if ("USDRUB" in data.quotes) {
        sheet["C4"].v = truncateDecimals(data.quotes.USDRUB * 10000) / 10000;
        console.log("=> updated USDRUB: ", sheet["C4"].v);
    }
    if ("USDEUR" in data.quotes) {
        sheet["D4"].v = truncateDecimals(1 / data.quotes.USDEUR * 10000) / 10000;
        console.log("=> updated EURUSD: ", sheet["D4"].v);
    }
    if ("USDCHF" in data.quotes) {
        sheet["E4"].v = truncateDecimals(1 / data.quotes.USDCHF * 10000) / 10000;
        console.log("=> updated CHFUSD: ", sheet["E4"].v);
    }
    if ("USDGBP" in data.quotes) {
        sheet["F4"].v = truncateDecimals(1 / data.quotes.USDGBP * 10000) / 10000;
        console.log("=> updated GBPUSD: ", sheet["F4"].v);
    }
    next();
}

function truncateDecimals(number) {
    return Math[number < 0 ? 'ceil' : 'floor'](number);
};

function saveFileAs() {
    console.log("Writing file to path: excel/financial_status_2016_out.xlsx ...");
    XLSX.writeFile(wb, "excel/financial_status_2016_out_js_broken.xlsx");
    console.log("Done.");
}
