// file: .github/test-files/test.rs
// version: 1.0.0
// guid: e0f1a2b3-c4d5-6e7f-8a9b-0c1d2e3f4a5b

//! Test Rust File
//! Purpose: Test Clippy and rustfmt configuration

use std::error::Error;

/// TestStruct for demonstration
#[derive(Debug, Clone)]
pub struct TestStruct {
    name: String,
    value: i32,
}

impl TestStruct {
    /// Create a new TestStruct
    pub fn new(name: String, value: i32) -> Self {
        Self { name, value }
    }

    /// Get the name
    pub fn name(&self) -> &str {
        &self.name
    }

    /// Get the value
    pub fn value(&self) -> i32 {
        self.value
    }

    /// Increment the value
    pub fn increment(&mut self, amount: i32) -> i32 {
        self.value += amount;
        self.value
    }
}

/// Process a vector of strings
pub fn process_strings(items: Vec<String>, filter_empty: bool) -> Vec<String> {
    if filter_empty {
        items
            .into_iter()
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .collect()
    } else {
        items.into_iter().map(|s| s.trim().to_string()).collect()
    }
}

/// Find a string in a vector
pub fn find_string(items: &[String], target: &str) -> Option<usize> {
    items.iter().position(|s| s == target)
}

/// Main entry point
pub fn main() -> Result<(), Box<dyn Error>> {
    let mut test = TestStruct::new("test".to_string(), 10);
    println!("Name: {}", test.name());
    println!("Value: {}", test.value());

    let new_value = test.increment(5);
    println!("New value: {}", new_value);

    let items = vec![
        "  item1  ".to_string(),
        "".to_string(),
        "  item2  ".to_string(),
        "item3".to_string(),
    ];
    let processed = process_strings(items, true);
    println!("Processed items: {:?}", processed);

    if let Some(index) = find_string(&processed, "item2") {
        println!("Found 'item2' at index: {}", index);
    } else {
        println!("Item not found");
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_struct_creation() {
        let test = TestStruct::new("test".to_string(), 42);
        assert_eq!(test.name(), "test");
        assert_eq!(test.value(), 42);
    }

    #[test]
    fn test_increment() {
        let mut test = TestStruct::new("test".to_string(), 10);
        let result = test.increment(5);
        assert_eq!(result, 15);
        assert_eq!(test.value(), 15);
    }

    #[test]
    fn test_process_strings() {
        let items = vec![
            "  hello  ".to_string(),
            "".to_string(),
            "  world  ".to_string(),
        ];
        let result = process_strings(items, true);
        assert_eq!(result, vec!["hello".to_string(), "world".to_string()]);
    }

    #[test]
    fn test_find_string() {
        let items = vec!["hello".to_string(), "world".to_string()];
        assert_eq!(find_string(&items, "world"), Some(1));
        assert_eq!(find_string(&items, "missing"), None);
    }
}
