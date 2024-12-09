# Function to print the values
print_values <- function(x, y) {
  for (i in seq_along(x)) {
    cat(sprintf("x: %d, y: %d\n", x[i], y[i]))
  }
}

# Function to perform a mathematical operation and call the print function
calculate_and_print <- function(start, stop, step) {
  x <- seq(start, stop, by = step) # Generate x values
  y <- x^2                        # Square each x value
  print_values(x, y)
}
