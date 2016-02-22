import urllib

def read_text():
	quotes = open("/users/filmmaker/desktop/development/python/movie_quotes.txt")
	content = quotes.read()
	quotes.close()
	check_profanity(content)

def check_profanity(text_to_check):
	connection = urllib.urlopen("http://www.wdyl.com/profanity?q=" + text_to_check)
	output = connection.read()
	connection.close()
	if "true" in output:
		print("Profanity alert!!!")
	elif "false" in output:
		print("No curse words in this document.")
	else:
		print("Could not scan document properly.")

read_text()
