// file: testdata/go/calculator.go
// version: 1.0.0
// guid: 2d3f4a5b-6c7d-8e9f-0a1b-2c3d4e5f6a7b

package main

// Add returns the sum of two integers.
func Add(a, b int) int {
	return a + b
}

// Subtract returns the difference between two integers.
func Subtract(a, b int) int {
	return a - b
}

// Multiply returns the product of two integers.
func Multiply(a, b int) int {
	return a * b
}

// Divide returns the quotient of two integers.
// Returns 0 if dividing by zero.
func Divide(a, b int) int {
	if b == 0 {
		return 0
	}
	return a / b
}
