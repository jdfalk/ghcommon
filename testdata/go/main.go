// file: testdata/go/main.go
// version: 2.0.0
// guid: 1d2f3a4b-5c6d-7e8f-9a0b-1c2d3e4f5a6b

package main

import (
	"fmt"
	"math/rand"
	"time"
)

func main() {
	fmt.Println("✅ Go test fixture built and ran.")

	// Demonstrate calculator functionality
	a, b := 42, 7
	fmt.Printf("Calculator Demo:\n")
	fmt.Printf("  %d + %d = %d\n", a, b, Add(a, b))
	fmt.Printf("  %d - %d = %d\n", a, b, Subtract(a, b))
	fmt.Printf("  %d * %d = %d\n", a, b, Multiply(a, b))
	fmt.Printf("  %d / %d = %d\n", a, b, Divide(a, b))

	// Demonstrate data processing
	numbers := GenerateRandomNumbers(10, 100)
	fmt.Printf("\nData Processing:\n")
	fmt.Printf("  Generated %d random numbers\n", len(numbers))
	fmt.Printf("  Sum: %d\n", Sum(numbers))
	fmt.Printf("  Average: %.2f\n", Average(numbers))
	fmt.Printf("  Max: %d\n", Max(numbers))
	fmt.Printf("  Min: %d\n", Min(numbers))

	// Demonstrate string operations
	text := "Hello, World! This is a test."
	fmt.Printf("\nString Operations:\n")
	fmt.Printf("  Original: %s\n", text)
	fmt.Printf("  Reversed: %s\n", ReverseString(text))
	fmt.Printf("  Word count: %d\n", CountWords(text))
}

// GenerateRandomNumbers creates a slice of n random integers up to max.
func GenerateRandomNumbers(n, max int) []int {
	rand.Seed(time.Now().UnixNano())
	numbers := make([]int, n)
	for i := 0; i < n; i++ {
		numbers[i] = rand.Intn(max)
	}
	return numbers
}

// Sum returns the sum of all integers in the slice.
func Sum(numbers []int) int {
	total := 0
	for _, n := range numbers {
		total += n
	}
	return total
}

// Average returns the average of all integers in the slice.
func Average(numbers []int) float64 {
	if len(numbers) == 0 {
		return 0
	}
	return float64(Sum(numbers)) / float64(len(numbers))
}

// Max returns the maximum value in the slice.
func Max(numbers []int) int {
	if len(numbers) == 0 {
		return 0
	}
	max := numbers[0]
	for _, n := range numbers[1:] {
		if n > max {
			max = n
		}
	}
	return max
}

// Min returns the minimum value in the slice.
func Min(numbers []int) int {
	if len(numbers) == 0 {
		return 0
	}
	min := numbers[0]
	for _, n := range numbers[1:] {
		if n < min {
			min = n
		}
	}
	return min
}

// ReverseString returns the reversed version of a string.
func ReverseString(s string) string {
	runes := []rune(s)
	for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
		runes[i], runes[j] = runes[j], runes[i]
	}
	return string(runes)
}

// CountWords returns the number of words in a string.
func CountWords(s string) int {
	if len(s) == 0 {
		return 0
	}
	count := 0
	inWord := false
	for _, r := range s {
		if r == ' ' || r == '\t' || r == '\n' {
			inWord = false
		} else if !inWord {
			count++
			inWord = true
		}
	}
	return count
}
