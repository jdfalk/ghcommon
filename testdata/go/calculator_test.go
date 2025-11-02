// file: testdata/go/calculator_test.go
// version: 2.0.0
// guid: 3d4f5a6b-7c8d-9e0f-1a2b-3c4d5e6f7a8b

package main

import "testing"

func TestAdd(t *testing.T) {
	tests := []struct {
		name string
		a    int
		b    int
		want int
	}{
		{"positive numbers", 2, 3, 5},
		{"negative numbers", -2, -3, -5},
		{"mixed signs", -2, 3, 1},
		{"zero", 0, 0, 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Add(tt.a, tt.b); got != tt.want {
				t.Errorf("Add(%d, %d) = %d, want %d", tt.a, tt.b, got, tt.want)
			}
		})
	}
}

func TestSubtract(t *testing.T) {
	tests := []struct {
		name string
		a    int
		b    int
		want int
	}{
		{"positive numbers", 5, 3, 2},
		{"negative numbers", -5, -3, -2},
		{"mixed signs", -2, 3, -5},
		{"zero", 0, 0, 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Subtract(tt.a, tt.b); got != tt.want {
				t.Errorf("Subtract(%d, %d) = %d, want %d", tt.a, tt.b, got, tt.want)
			}
		})
	}
}

func TestMultiply(t *testing.T) {
	tests := []struct {
		name string
		a    int
		b    int
		want int
	}{
		{"positive numbers", 2, 3, 6},
		{"negative numbers", -2, -3, 6},
		{"mixed signs", -2, 3, -6},
		{"zero", 5, 0, 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Multiply(tt.a, tt.b); got != tt.want {
				t.Errorf("Multiply(%d, %d) = %d, want %d", tt.a, tt.b, got, tt.want)
			}
		})
	}
}

func TestDivide(t *testing.T) {
	tests := []struct {
		name string
		a    int
		b    int
		want int
	}{
		{"normal division", 6, 3, 2},
		{"negative numbers", -6, -3, 2},
		{"mixed signs", -6, 3, -2},
		{"divide by zero", 5, 0, 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Divide(tt.a, tt.b); got != tt.want {
				t.Errorf("Divide(%d, %d) = %d, want %d", tt.a, tt.b, got, tt.want)
			}
		})
	}
}

func TestSum(t *testing.T) {
	tests := []struct {
		name    string
		numbers []int
		want    int
	}{
		{"empty slice", []int{}, 0},
		{"single number", []int{5}, 5},
		{"multiple numbers", []int{1, 2, 3, 4, 5}, 15},
		{"negative numbers", []int{-1, -2, -3}, -6},
		{"mixed signs", []int{-5, 10, -3, 8}, 10},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Sum(tt.numbers); got != tt.want {
				t.Errorf("Sum(%v) = %d, want %d", tt.numbers, got, tt.want)
			}
		})
	}
}

func TestAverage(t *testing.T) {
	tests := []struct {
		name    string
		numbers []int
		want    float64
	}{
		{"empty slice", []int{}, 0.0},
		{"single number", []int{10}, 10.0},
		{"multiple numbers", []int{2, 4, 6, 8}, 5.0},
		{"negative numbers", []int{-2, -4, -6}, -4.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Average(tt.numbers); got != tt.want {
				t.Errorf("Average(%v) = %f, want %f", tt.numbers, got, tt.want)
			}
		})
	}
}

func TestMax(t *testing.T) {
	tests := []struct {
		name    string
		numbers []int
		want    int
	}{
		{"empty slice", []int{}, 0},
		{"single number", []int{5}, 5},
		{"multiple numbers", []int{1, 5, 3, 9, 2}, 9},
		{"negative numbers", []int{-5, -2, -10, -1}, -1},
		{"all same", []int{7, 7, 7, 7}, 7},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Max(tt.numbers); got != tt.want {
				t.Errorf("Max(%v) = %d, want %d", tt.numbers, got, tt.want)
			}
		})
	}
}

func TestMin(t *testing.T) {
	tests := []struct {
		name    string
		numbers []int
		want    int
	}{
		{"empty slice", []int{}, 0},
		{"single number", []int{5}, 5},
		{"multiple numbers", []int{1, 5, 3, 9, 2}, 1},
		{"negative numbers", []int{-5, -2, -10, -1}, -10},
		{"all same", []int{7, 7, 7, 7}, 7},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Min(tt.numbers); got != tt.want {
				t.Errorf("Min(%v) = %d, want %d", tt.numbers, got, tt.want)
			}
		})
	}
}

func TestReverseString(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{"empty string", "", ""},
		{"single char", "a", "a"},
		{"simple word", "hello", "olleh"},
		{"with spaces", "hello world", "dlrow olleh"},
		{"unicode", "Hello, 世界", "界世 ,olleH"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := ReverseString(tt.input); got != tt.want {
				t.Errorf("ReverseString(%q) = %q, want %q", tt.input, got, tt.want)
			}
		})
	}
}

func TestCountWords(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  int
	}{
		{"empty string", "", 0},
		{"single word", "hello", 1},
		{"multiple words", "hello world", 2},
		{"extra spaces", "hello  world  test", 3},
		{"with tabs", "hello\tworld", 2},
		{"with newlines", "hello\nworld\ntest", 3},
		{"complex", "The quick brown fox jumps over the lazy dog", 9},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := CountWords(tt.input); got != tt.want {
				t.Errorf("CountWords(%q) = %d, want %d", tt.input, got, tt.want)
			}
		})
	}
}

func TestGenerateRandomNumbers(t *testing.T) {
	t.Run("correct length", func(t *testing.T) {
		n := 100
		numbers := GenerateRandomNumbers(n, 1000)
		if len(numbers) != n {
			t.Errorf("GenerateRandomNumbers(%d, 1000) returned %d elements, want %d", n, len(numbers), n)
		}
	})

	t.Run("values in range", func(t *testing.T) {
		max := 50
		numbers := GenerateRandomNumbers(100, max)
		for i, n := range numbers {
			if n < 0 || n >= max {
				t.Errorf("GenerateRandomNumbers(100, %d)[%d] = %d, out of range [0, %d)", max, i, n, max)
			}
		}
	})
}
