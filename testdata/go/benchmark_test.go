// file: testdata/go/benchmark_test.go
// version: 1.0.0
// guid: 5d6f7a8b-9c0d-1e2f-3a4b-5c6d7e8f9a0b

package main

import (
	"testing"
)

// Benchmark calculator operations
func BenchmarkAdd(b *testing.B) {
	for i := 0; i < b.N; i++ {
		Add(42, 7)
	}
}

func BenchmarkSubtract(b *testing.B) {
	for i := 0; i < b.N; i++ {
		Subtract(42, 7)
	}
}

func BenchmarkMultiply(b *testing.B) {
	for i := 0; i < b.N; i++ {
		Multiply(42, 7)
	}
}

func BenchmarkDivide(b *testing.B) {
	for i := 0; i < b.N; i++ {
		Divide(42, 7)
	}
}

// Benchmark data processing operations
func BenchmarkSum(b *testing.B) {
	numbers := GenerateRandomNumbers(1000, 10000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		Sum(numbers)
	}
}

func BenchmarkAverage(b *testing.B) {
	numbers := GenerateRandomNumbers(1000, 10000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		Average(numbers)
	}
}

func BenchmarkMax(b *testing.B) {
	numbers := GenerateRandomNumbers(1000, 10000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		Max(numbers)
	}
}

func BenchmarkMin(b *testing.B) {
	numbers := GenerateRandomNumbers(1000, 10000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		Min(numbers)
	}
}

// Benchmark string operations
func BenchmarkReverseString(b *testing.B) {
	text := "The quick brown fox jumps over the lazy dog"
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ReverseString(text)
	}
}

func BenchmarkReverseStringLong(b *testing.B) {
	text := "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ReverseString(text)
	}
}

func BenchmarkCountWords(b *testing.B) {
	text := "The quick brown fox jumps over the lazy dog"
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		CountWords(text)
	}
}

func BenchmarkCountWordsLong(b *testing.B) {
	text := "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		CountWords(text)
	}
}

// Benchmark combinations
func BenchmarkCalculatorOperations(b *testing.B) {
	for i := 0; i < b.N; i++ {
		a, c := 42, 7
		_ = Add(a, c)
		_ = Subtract(a, c)
		_ = Multiply(a, c)
		_ = Divide(a, c)
	}
}

func BenchmarkDataProcessingPipeline(b *testing.B) {
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		numbers := GenerateRandomNumbers(100, 1000)
		_ = Sum(numbers)
		_ = Average(numbers)
		_ = Max(numbers)
		_ = Min(numbers)
	}
}

func BenchmarkGenerateRandomNumbers(b *testing.B) {
	for i := 0; i < b.N; i++ {
		GenerateRandomNumbers(1000, 10000)
	}
}
