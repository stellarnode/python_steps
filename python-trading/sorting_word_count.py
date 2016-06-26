"""Count words."""

import re
from operator import itemgetter, attrgetter

def count_words(s, n):
    """Return the n most frequently occuring words in s."""
    
    # TODO: Count the number of occurences of each word in s
    result = []
    s_arr = s.split(" ")
    
    for el in s_arr:
        count = s_arr.count(el)
        if not (el, count) in result:
            result.append((el, count))
    
    # TODO: Sort the occurences in descending order (alphabetically in case of ties)
    result_sorted = sorted(result, key=itemgetter(0))
    result_sorted = sorted(result_sorted, key=itemgetter(1), reverse=True)
    top_n = result_sorted[0:n]
    
    # TODO: Return the top n words as a list of tuples (<word>, <count>)
    return top_n


def test_run():
    """Test count_words() with some inputs."""
    print count_words("cat bat mat cat bat cat", 3)
    print count_words("betty bought a bit of butter but the butter was bitter", 3)


if __name__ == '__main__':
    test_run()