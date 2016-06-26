# Draft

import urllib2
import re


def is_not_empty(s):
    return str(s) != ""

def sort_tuples(x, y):
    if x[1] == y[1]:
        if x[0].lower() >= y[0].lower():
            return 1
        else:
            return -1
    else:
        return y[1] - x[1]

def main():
    print("Starting...")
    response = urllib2.urlopen('http://stellarnode.ru')
    data = response.read()
    words = re.split('[\W\s]', data)
    words_filtered = filter(is_not_empty, words)

    word_list = []
    counted = []

    for word in words_filtered:
        if not word in counted:
            count = words_filtered.count(word)
            counted.append(word)
            word_list.append((word, count))

    word_list_sorted = sorted(word_list, cmp=sort_tuples)

    # word_count_sorted = sorted(word_count, key = lambda x: x.value, reverse = True)
    print("Word count: ", word_list_sorted)

if __name__ == "__main__":
    main()
