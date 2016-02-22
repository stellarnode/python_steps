import turtle

def draw_square(rotate):
    
    brad = turtle.Turtle()
    brad.shape("triangle")
    brad.color("yellow")
    brad.speed(10)
    brad.right(rotate)

    for i in range(0, 4):
        brad.forward(100)
        brad.right(90)
    
    
def draw_circle():

    angie = turtle.Turtle()
    angie.shape("arrow")
    angie.color("green")
    angie.speed(6)
    angie.circle(130, None, None)


def draw_triangle():

    pete = turtle.Turtle()
    pete.shape("turtle")
    pete.color("black")
    pete.speed(4)

    pete.forward(120)
    pete.right(90)
    pete.forward(120)
    pete.home()

        
window = turtle.Screen()
window.bgcolor("red")

for j in range(0, 360, 10):
    draw_square(j)


draw_circle()
draw_triangle()

window.exitonclick()
