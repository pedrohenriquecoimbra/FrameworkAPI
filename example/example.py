# Function to print the values
def print_values(x, y):
    for xi, yi in zip(x, y):
        print(f"x: {xi}, y: {yi}")


# Function to save file after run
def save_file_before_exit():
    with open("example/example_py.txt", "w") as file:
        file.write("End")


# Function to perform a mathematical operation and call the print function
def calculate_and_print(start, stop, step):
    x = [i for i in range(start, stop, step)]  # Generate x values
    y = [xi**2 for xi in x]  # Square each x value
    print_values(x, y)
    #save_file_before_exit()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start', type=int, default=0)
    parser.add_argument('-p', '--stop', type=int, default=10)
    parser.add_argument('-t', '--step', type=int, default=1)
    args = parser.parse_args()

    calculate_and_print(**vars(args))
