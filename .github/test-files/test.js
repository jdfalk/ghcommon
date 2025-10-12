// file: .github/test-files/test.js
// version: 1.0.0
// guid: d9e0f1a2-b3c4-5d6e-7f8a-9b0c1d2e3f4a

/**
 * Test JavaScript File
 * Purpose: Test ESLint configuration
 */

/**
 * TestClass for demonstration
 */
class TestClass {
  /**
   * Constructor
   * @param {string} name - The name
   * @param {number} value - The value
   */
  constructor(name, value) {
    this.name = name;
    this.value = value;
  }

  /**
   * Get the name
   * @returns {string} The name
   */
  getName() {
    return this.name;
  }

  /**
   * Get the value
   * @returns {number} The value
   */
  getValue() {
    return this.value;
  }

  /**
   * Increment the value
   * @param {number} amount - Amount to increment
   * @returns {number} New value
   */
  increment(amount = 1) {
    this.value += amount;
    return this.value;
  }
}

/**
 * Process an array of items
 * @param {string[]} items - Items to process
 * @param {boolean} filterEmpty - Whether to filter empty strings
 * @returns {string[]} Processed items
 */
function processArray(items, filterEmpty = true) {
  if (filterEmpty) {
    return items.map(item => item.trim()).filter(item => item.length > 0);
  }
  return items.map(item => item.trim());
}

/**
 * Find an item in an array
 * @param {string[]} items - Array to search
 * @param {string} target - Target to find
 * @returns {number} Index or -1 if not found
 */
function findItem(items, target) {
  return items.indexOf(target);
}

/**
 * Main function
 */
function main() {
  const test = new TestClass('test', 10);
  console.log(`Name: ${test.getName()}`);
  console.log(`Value: ${test.getValue()}`);

  const newValue = test.increment(5);
  console.log(`New value: ${newValue}`);

  const items = ['  item1  ', '', '  item2  ', 'item3'];
  const processed = processArray(items);
  console.log(`Processed items: ${processed}`);

  const index = findItem(processed, 'item2');
  if (index !== -1) {
    console.log(`Found 'item2' at index: ${index}`);
  } else {
    console.log('Item not found');
  }
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    TestClass,
    processArray,
    findItem,
    main,
  };
}
