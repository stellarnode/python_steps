
text_input = raw_input("Enter some text you want to add to a file: ")
text_file = open("/users/filmmaker/desktop/development/python/sample_text.txt", "a")
text_file.write("\n" + text_input + "\n")
text_file.close()

