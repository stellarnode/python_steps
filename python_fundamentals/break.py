import webbrowser
import time

url = "http://www.google.com"
print("Program started at: " + time.ctime())

for i in range(0, 3):
    time.sleep(2)
    webbrowser.open(url)

print("Program ended at: " + time.ctime())
