// file: .commitlintrc.js
// version: 1.0.0
// guid: a1b2c3d4-e5f6-7890-abcd-ef1234567890

/**
 * Commitlint configuration for ghcommon repository
 *
 * This configuration enforces our conventional commit standards as defined in
 * .github/instructions/general-coding.instructions.md and .github/commit-messages.md
 *
 * Based on the validation regex from .github/validate-setup.sh:
 * ^(feat|fix|docs|style|refactor|perf|test|chore|build|ci|revert)(\(.+\))?\!?:
 */

module.exports = {
  extends: ["@commitlint/config-conventional"],

  rules: {
    // Type enum - matches our validation script
    "type-enum": [
      2,
      "always",
      [
        "feat", // A new feature
        "fix", // A bug fix
        "docs", // Documentation only changes
        "style", // Changes that do not affect the meaning of the code
        "refactor", // A code change that neither fixes a bug nor adds a feature
        "perf", // A code change that improves performance
        "test", // Adding missing tests or correcting existing tests
        "chore", // Changes to the build process or auxiliary tools
        "build", // Changes that affect the build system or external dependencies
        "ci", // Changes to our CI configuration files and scripts
        "revert", // Reverts a previous commit
      ],
    ],

    // Subject and body rules
    "subject-case": [
      2,
      "never",
      ["sentence-case", "start-case", "pascal-case", "upper-case"],
    ],
    "subject-empty": [2, "never"],
    "subject-full-stop": [2, "never", "."],
    "subject-max-length": [2, "always", 72],
    "subject-min-length": [2, "always", 10],

    // Type and format rules
    "type-case": [2, "always", "lower-case"],
    "type-empty": [2, "never"],

    // Scope rules (optional but when present must be lowercase)
    "scope-case": [2, "always", "lower-case"],

    // Header rules
    "header-max-length": [2, "always", 100],

    // Body rules
    "body-leading-blank": [2, "always"],
    "body-max-line-length": [2, "always", 100],
  },

  // Custom plugin to enforce "Files changed:" section
  plugins: [
    {
      rules: {
        "files-changed-section": (parsed) => {
          const { body } = parsed;

          // Only check if there's a body
          if (!body) {
            return [
              false,
              'Commit body should include a "Files changed:" section listing all modified files',
            ];
          }

          // Check if "Files changed:" section exists
          if (!body.includes("Files changed:")) {
            return [
              false,
              'Commit body must include a "Files changed:" section listing all modified files',
            ];
          }

          return [true];
        },
      },
    },
  ],

  // Enable the custom rule
  rules: {
    ...module.exports.rules,
    "files-changed-section": [1, "always"], // Warning level, not error
  },
};
