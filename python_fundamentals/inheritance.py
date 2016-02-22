

class Parent():

	def __init__(self, lname, ecolor):
		print("Parent constructor called.")
		self.last_name = lname
		self.eye_color = ecolor

	def show_info(self):
		print("Last name: " + self.last_name)
		print("Eye color: " + self.eye_color)

class Child(Parent):

	def __init__(self, lname, ecolor, num_of_toys):
		print("Child constructor called")
		Parent.__init__(self, lname, ecolor)
		self.number_of_toys = num_of_toys

	def show_info(self):
		print("Last name: " + self.last_name)
		print("Eye color: " + self.eye_color)
		print("Number of toys: " + str(self.number_of_toys))

billy_cyrus = Parent("Cyrus", "blue")
# print(billy_cyrus.last_name)
billy_cyrus.show_info()

miley_cyrus = Child("Cyrus", "blue", 5)
# print(miley_cyrus.last_name)
# print(miley_cyrus.number_of_toys)
miley_cyrus.show_info()