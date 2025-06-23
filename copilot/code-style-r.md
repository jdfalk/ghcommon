# file: copilot/code-style-r.md

# R Coding Style Guide (Google/Tidyverse Style)

This guide combines the [Google R Style Guide](https://google.github.io/styleguide/Rguide.html) and [Tidyverse Style Guide](https://style.tidyverse.org/) to provide comprehensive guidelines for writing clean, consistent R code.

## Naming Conventions

### Object Names

**Use snake_case for variables and functions**

- Variable and function names: lowercase letters, numbers, and underscores only
- Use underscores to separate words (snake_case)
- Variable names should be nouns, function names should be verbs

```r
# Good
day_one
day_1
user_age
calculate_mean

# Bad
DayOne
dayone
userAge
calculateMean
```

### Function Naming

**Google prefers BigCamelCase for functions**

- Use `BigCamelCase` to distinguish functions from other objects
- Private functions should start with a dot

```r
# Good (Google style)
DoNothing <- function() {
  return(invisible(NULL))
}

.DoNothingPrivately <- function() {
  return(invisible(NULL))
}

# Good (Tidyverse style)
do_nothing <- function() {
  return(invisible(NULL))
}
```

### Avoid Problematic Names

- Don't reuse common function and variable names
- Avoid using `.` in names (reserved for S3 methods)
- Strive for concise and meaningful names

```r
# Bad
T <- FALSE
c <- 10
mean <- function(x) sum(x)
contrib.url()  # Avoid dots except for S3 methods

# Good
is_valid <- FALSE
count <- 10
calculate_mean <- function(x) sum(x)
```

## Syntax and Formatting

### Spacing Rules

**Commas**: Always space after, never before

```r
# Good
x[, 1]
mean(x, na.rm = TRUE)

# Bad
x[,1]
x[ ,1]
mean(x,na.rm=TRUE)
```

**Parentheses**: No spaces inside for function calls

```r
# Good
mean(x, na.rm = TRUE)
if (debug) {
  show(x)
}
function(x) {}

# Bad
mean (x, na.rm = TRUE)
mean( x, na.rm = TRUE )
if(debug){
  show(x)
}
```

**Infix Operators**: Most operators surrounded by spaces

```r
# Good
height <- (feet * 12) + inches
x <- 1:10
df$column

# Bad
height<-feet*12+inches
x <- 1 : 10
df $ column
```

**Exceptions (no spaces)**:

- High precedence operators: `::`, `:::`, `$`, `@`, `[`, `[[`, `^`, `:`
- Single-sided formulas: `~foo`
- Bang-bang operators: `!!`, `!!!`
- Help operator: `?mean`

### Line Length and Breaking

- **Limit lines to 80 characters**
- Break long function calls with one argument per line

```r
# Good
do_something_very_complicated(
  something = "that",
  requires = many,
  arguments = "some of which may be long"
)

# Bad
do_something_very_complicated("that", requires, many, arguments, "some of which may be long")
```

### Vertical Spacing

- Use sparingly to separate "thoughts" in code
- Avoid empty lines at start/end of functions
- Single empty line to separate functions or major sections
- Empty line before comment blocks

## Control Flow and Braces

### Braced Expressions

- `{` should be last character on line
- Contents indented by 2 spaces
- `}` should be first character on line

```r
# Good
if (y < 0 && debug) {
  message("y is negative")
}

if (y == 0) {
  log(x)
} else {
  y^x
}

# Bad
if (y < 0 && debug) {
message("Y is negative")
}

if (y == 0)
{
    log(x)
} else { y^x }
```

### If Statements

- Single line: no braces for simple statements
- Multi-line: must use braces
- `else` on same line as closing `}`
- Use `&&` and `||`, never `&` and `|` in conditions

```r
# Good (single line)
message <- if (x > 10) "big" else "small"

# Good (multi-line)
if (x > 10) {
  x * 2
} else {
  x * 3
}

# Good (logical operators)
if (x > 0 && y > 0) {
  do_something()
}
```

### Loops

- Body must always use braced expressions
- Empty body should be `{}` with no space

```r
# Good
for (i in seq) {
  x[i] <- x[i] + 1
}

while (waiting_for_something()) {
  cat("Still waiting...")
}

# Bad
for (i in seq) x[i] <- x[i] + 1
```

### Control Flow Modifiers

- `return()`, `stop()`, `break`, `next` should be in their own blocks

```r
# Good
if (y < 0) {
  stop("Y is negative")
}

find_abs <- function(x) {
  if (x > 0) {
    return(x)
  }
  x * -1
}

# Bad
if (y < 0) stop("Y is negative")
```

## Assignment and Data

### Assignment Operator

- Use `<-` for assignment, not `=`
- Avoid assignment in function calls

```r
# Good
x <- 5
result <- complicated_function()
if (nzchar(result) < 1) {
  # do something
}

# Bad
x = 5
if (nzchar(x <- complicated_function()) < 1) {
  # do something
}
```

### Character Vectors

- Use double quotes `"` for strings
- Exception: when string contains double quotes

```r
# Good
"Text"
'Text with "quotes"'

# Bad
'Text'
'Text with "double" and \'single\' quotes'
```

### Logical Vectors

- Use `TRUE`/`FALSE`, not `T`/`F`

```r
# Good
debug <- TRUE
valid <- FALSE

# Bad
debug <- T
valid <- F
```

## Function Guidelines

### Function Calls

**Named Arguments**

- Omit names for data arguments
- Use full names when overriding defaults
- Avoid partial matching

```r
# Good
mean(1:10, na.rm = TRUE)
rep(1:2, times = 3)

# Bad
mean(x = 1:10, , FALSE)
rep(1:2, t = 3)
```

**Long Function Calls**

- One line per argument for readability
- Align related arguments

```r
# Good
my_function(
  x = data,
  y = long_argument_name,
  extra_argument_a = 10,
  extra_argument_b = c(1, 43, 390, 210209)
)
```

### Function Definition

- Use explicit returns
- Document parameters and return values

```r
# Good
AddValues <- function(x, y) {
  result <- x + y
  return(result)
}

# Bad
AddValues <- function(x, y) {
  x + y
}
```

## Pipes and Modern R

### Pipe Usage (Google Style)

- **Avoid right-hand assignment** with pipes
- Use explicit returns in functions

```r
# Good
results <- iris %>%
  dplyr::summarize(max_petal = max(Petal.Width))

# Bad
iris %>%
  dplyr::summarize(max_petal = max(Petal.Width)) -> results
```

### Namespace Qualification

- **Explicitly qualify namespaces** for external functions
- Use `package::function()` notation
- Helps understand dependencies and avoid conflicts

```r
# Good
purrr::map(data, function)
dplyr::filter(df, condition)

# Avoid (except for very common functions)
map(data, function)
filter(df, condition)
```

## Comments and Documentation

### Comment Style

- Each comment line starts with `#` and single space
- Use comments to record findings and decisions
- If code needs comments to explain what it does, consider rewriting

```r
# Good
# Calculate the mean excluding outliers
clean_data <- remove_outliers(data)
mean_value <- mean(clean_data$value)

# This is a comment explaining the next section
process_results(mean_value)
```

### Documentation

- All packages should have package-level documentation
- Use roxygen2 for function documentation
- Place `@importFrom` tags above functions using external dependencies

## Best Practices

### Code Organization

1. **Consistency**: Choose one style and stick to it
2. **Readability**: Code should be self-documenting
3. **Modularity**: Break complex operations into smaller functions
4. **Dependencies**: Minimize and clearly document external dependencies

### Performance Considerations

- Use vectorized operations when possible
- Avoid unnecessary loops
- Pre-allocate vectors when size is known
- Use appropriate data structures (data.frame, tibble, etc.)

### Error Handling

- Use informative error messages
- Validate inputs early in functions
- Use `stop()`, `warning()`, and `message()` appropriately

```r
# Good
validate_input <- function(x) {
  if (!is.numeric(x)) {
    stop("Input must be numeric", call. = FALSE)
  }
  if (length(x) == 0) {
    warning("Input vector is empty")
  }
  return(invisible(NULL))
}
```

### Package Development

- Follow tidyverse principles for package APIs
- Use consistent naming conventions throughout package
- Provide comprehensive examples and vignettes
- Include thorough test coverage

## Tools for Style Enforcement

### Automated Formatting

- **styler**: Interactive restyling of code
- **lintr**: Automated style checking
- **formatR**: Code formatting utility

### RStudio Integration

- Use styler RStudio add-in for interactive formatting
- Configure lintr for real-time style checking
- Set up project-level style preferences

This style guide ensures your R code is readable, maintainable, and follows industry best practices combining Google's enterprise focus with tidyverse's modern R approaches.
