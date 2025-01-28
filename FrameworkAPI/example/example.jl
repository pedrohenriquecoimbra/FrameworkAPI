# Function to print the values
function print_values(x, y)
    for (xi, yi) in zip(x, y)
        println("x: $xi, y: $yi")
    end
end

# Function to save file after run
function save_file_before_exit()
    file = open("FrameworkAPI/example/example_jl.txt", "w")
    write(file, "End")
    close(file)
end

# Function to perform a mathematical operation and call the print function
function calculate_and_print(; start, stop, step)
    x = start:step:stop  # Generate x values
    y = x .^ 2           # Square each x value (element-wise operation)
    print_values(x, y)
    #save_file_before_exit()
end
