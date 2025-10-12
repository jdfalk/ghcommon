// file: .github/test-files/test.go
// version: 1.0.0
// guid: c8d9e0f1-a2b3-4c5d-6e7f-8a9b0c1d2e3f

package testfiles

import (
	"errors"
	"fmt"
	"strings"
)

// TestStruct represents a test structure
type TestStruct struct {
	Name  string
	Value int
	Tags  []string
}

// NewTestStruct creates a new TestStruct instance
func NewTestStruct(name string, value int) *TestStruct {
	return &TestStruct{
		Name:  name,
		Value: value,
		Tags:  make([]string, 0),
	}
}

// GetName returns the name field
func (t *TestStruct) GetName() string {
	return t.Name
}

// GetValue returns the value field
func (t *TestStruct) GetValue() int {
	return t.Value
}

// AddTag adds a tag to the Tags slice
func (t *TestStruct) AddTag(tag string) error {
	if tag == "" {
		return errors.New("tag cannot be empty")
	}
	t.Tags = append(t.Tags, tag)
	return nil
}

// GetTags returns all tags
func (t *TestStruct) GetTags() []string {
	return t.Tags
}

// ProcessStrings processes a slice of strings
func ProcessStrings(input []string, toUpper bool) []string {
	result := make([]string, 0, len(input))
	for _, s := range input {
		trimmed := strings.TrimSpace(s)
		if trimmed == "" {
			continue
		}
		if toUpper {
			result = append(result, strings.ToUpper(trimmed))
		} else {
			result = append(result, trimmed)
		}
	}
	return result
}

// FindString finds a string in a slice
func FindString(haystack []string, needle string) (int, error) {
	for i, s := range haystack {
		if s == needle {
			return i, nil
		}
	}
	return -1, fmt.Errorf("string %q not found", needle)
}

// ExampleFunction demonstrates proper Go formatting
func ExampleFunction() {
	test := NewTestStruct("example", 42)
	fmt.Printf("Name: %s\n", test.GetName())
	fmt.Printf("Value: %d\n", test.GetValue())

	err := test.AddTag("test")
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	tags := test.GetTags()
	fmt.Printf("Tags: %v\n", tags)

	input := []string{"  hello  ", "", "  world  "}
	processed := ProcessStrings(input, true)
	fmt.Printf("Processed: %v\n", processed)

	idx, err := FindString(processed, "HELLO")
	if err != nil {
		fmt.Printf("Not found: %v\n", err)
	} else {
		fmt.Printf("Found at index: %d\n", idx)
	}
}
