# import fresh_tomatoes
import media

toy_story = media.Movie("Toy Story",
	"A story of a boy and his toys which come to life",
	"https://upload.wikimedia.org/wikipedia/en/1/13/Toy_Story.jpg",
	"http://www.youtube.com/watch?v=KYz2wyBy3kc")

# print(toy_story.storyline)

avatar = media.Movie("Avatar",
	"A marine on a alien planet",
	"https://upload.wikimedia.org/wikipedia/en/b/b0/Avatar-Teaser-Poster.jpg",
	"http://www.youtube.com/watch?v=5PSNL1qE6VY&t=6s")

# print(avatar.storyline)
# avatar.show_trailer()

movies = [toy_story, avatar]
# fresh_tomatoes.open_movies_page(movies)

print(media.Movie.__doc__)
print(media.Movie.__name__)
print(media.Movie.__module__)
print(media.Movie.VALID_RATINGS)