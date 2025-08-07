#!/usr/bin/env python3
# file: create_copilot_agent_util.py
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7890-abcd-ef1234567890

"""
Script to create a new copilot-agent-util repository with standard layout and tooling.
This utility will solve VS Code task execution issues by providing a centralized command runner.
"""

import subprocess
import sys
import shutil
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    if isinstance(cmd, str):
        cmd = cmd.split()

    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

    if check and result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)

    return result


def check_requirements():
    """Check if required tools are available."""
    print("Checking requirements...")

    # Check if gh CLI is available
    try:
        result = run_command("gh --version")
        print(f"GitHub CLI found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: GitHub CLI (gh) not found. Please install it first.")
        sys.exit(1)

    # Check if git is available
    try:
        result = run_command("git --version")
        print(f"Git found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: Git not found. Please install it first.")
        sys.exit(1)


def create_repository():
    """Create the new repository on GitHub."""
    repo_name = "copilot-agent-util"

    print(f"Creating repository: {repo_name}")

    # Check if repo already exists
    result = run_command(f"gh repo view jdfalk/{repo_name}", check=False)
    if result.returncode == 0:
        print(f"Repository {repo_name} already exists. Skipping creation.")
        return repo_name

    # Create the repository
    run_command(
        [
            "gh",
            "repo",
            "create",
            f"jdfalk/{repo_name}",
            "--public",
            "--description",
            "Centralized utility for Copilot/AI agent command execution with logging and VS Code task integration",
            "--clone",
        ]
    )

    return repo_name


def copy_standard_files(repo_name):
    """Copy standard repository files from ghcommon to the new repo."""
    source_dir = Path("/Users/jdfalk/repos/github.com/jdfalk/ghcommon")
    target_dir = Path(f"/Users/jdfalk/repos/github.com/jdfalk/{repo_name}")

    if not target_dir.exists():
        print(f"Target directory {target_dir} doesn't exist. Cloning repository...")
        run_command(
            f"gh repo clone jdfalk/{repo_name}",
            cwd="/Users/jdfalk/repos/github.com/jdfalk",
        )

    print("Copying standard files...")

    # Files and directories to copy
    items_to_copy = [
        ".github/",
        ".gitignore",
        "LICENSE",
        "CONTRIBUTING.md",
        "SECURITY.md",
    ]

    for item in items_to_copy:
        source_path = source_dir / item
        target_path = target_dir / item

        if source_path.exists():
            print(f"Copying {item}...")
            if source_path.is_dir():
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(source_path, target_path)
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
        else:
            print(f"Warning: {source_path} not found, skipping...")


def create_go_project_structure(repo_name):
    """Create the Go project structure."""
    target_dir = Path(f"/Users/jdfalk/repos/github.com/jdfalk/{repo_name}")

    print("Creating Go project structure...")

    # Create directories
    directories = [
        "cmd/copilot-agent-util",
        "pkg/executor",
        "pkg/logger",
        "pkg/commands",
        "internal/config",
        "logs",
        "test",
        "scripts",
    ]

    for dir_path in directories:
        (target_dir / dir_path).mkdir(parents=True, exist_ok=True)

    # Create go.mod
    go_mod_content = f"""module github.com/jdfalk/{repo_name}

go 1.21

require (
	github.com/spf13/cobra v1.8.0
	github.com/spf13/viper v1.18.2
)
"""

    with open(target_dir / "go.mod", "w") as f:
        f.write(go_mod_content)


def create_readme(repo_name):
    """Create the README.md file."""
    target_dir = Path(f"/Users/jdfalk/repos/github.com/jdfalk/{repo_name}")

    readme_content = f"""<!-- file: README.md -->
<!-- version: 1.0.0 -->
<!-- guid: {generate_guid()} -->

# Copilot Agent Utility

A centralized command execution utility designed to solve VS Code task execution issues and provide consistent logging for Copilot/AI agent operations.

## Overview

This Go application serves as a reliable intermediary between VS Code tasks and system commands, ensuring proper working directory handling, comprehensive logging, and consistent output formatting.

## Features

- **Reliable Command Execution**: Handles working directory changes and environment setup
- **Comprehensive Logging**: Outputs to both terminal and log files with timestamps
- **VS Code Integration**: Designed to work seamlessly with VS Code tasks
- **Cross-Platform**: Works on macOS, Linux, and Windows
- **Extensible**: Easy to add new command types and utilities

## Installation

```bash
go install github.com/jdfalk/{repo_name}/cmd/copilot-agent-util@latest
```

Or build from source:

```bash
git clone https://github.com/jdfalk/{repo_name}.git
cd {repo_name}
go build -o bin/copilot-agent-util cmd/copilot-agent-util/main.go
```

## Usage

```bash
# Basic command execution
copilot-agent-util exec "ls -la"

# Git operations
copilot-agent-util git add .
copilot-agent-util git commit -m "feat: add new feature"
copilot-agent-util git push

# Protocol buffer operations
copilot-agent-util buf generate
copilot-agent-util buf generate --module auth

# File operations
copilot-agent-util file cat README.md
copilot-agent-util file ls src/

# Development tools
copilot-agent-util python run script.py
copilot-agent-util npm install
copilot-agent-util uv run main.py
```

## Command Categories

### File Operations
- `file ls <path>` - List directory contents
- `file cat <file>` - Display file contents
- `file cp <src> <dst>` - Copy files/directories
- `file mv <src> <dst>` - Move/rename files/directories

### Git Operations
- `git add <pattern>` - Add files to staging
- `git commit -m <message>` - Commit changes
- `git push` - Push to remote
- `git push --force-with-lease` - Safe force push
- `git status` - Show repository status

### Protocol Buffers
- `buf generate` - Generate all protocol buffers
- `buf generate --module <name>` - Generate specific module
- `buf lint` - Lint protocol buffer files

### Development Tools
- `python run <script>` - Run Python scripts
- `python build` - Build Python projects
- `uv run <command>` - Run commands with uv
- `npm install` - Install npm dependencies
- `npm run <script>` - Run npm scripts
- `npx <command>` - Execute npm packages

## Configuration

The utility reads configuration from:
- `~/.config/copilot-agent-util/config.yaml`
- Environment variables
- Command-line flags

## Logging

All operations are logged to:
- Terminal (stdout/stderr)
- Log files in `./logs/` directory
- Structured JSON logs for automation

## VS Code Integration

Update your `.vscode/tasks.json`:

```json
{{
  "version": "2.0.0",
  "tasks": [
    {{
      "label": "Buf Generate",
      "type": "shell",
      "command": "copilot-agent-util buf generate",
      "group": "build",
      "options": {{
        "cwd": "${{workspaceFolder}}"
      }}
    }}
  ]
}}
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

See [LICENSE](LICENSE) file.
"""

    with open(target_dir / "README.md", "w") as f:
        f.write(readme_content)


def create_todo(repo_name):
    """Create the TODO.md file with feature list."""
    target_dir = Path(f"/Users/jdfalk/repos/github.com/jdfalk/{repo_name}")

    todo_content = f"""<!-- file: TODO.md -->
<!-- version: 1.0.0 -->
<!-- guid: {generate_guid()} -->

# TODO: Copilot Agent Utility Features

## Core Features

### File Operations
- [ ] `file ls <path>` - List directory contents with detailed output
- [ ] `file cat <file>` - Display file contents with syntax highlighting
- [ ] `file cp <src> <dst>` - Copy files/directories with progress
- [ ] `file mv <src> <dst>` - Move/rename files/directories
- [ ] `file mkdir <path>` - Create directories recursively
- [ ] `file rm <path>` - Remove files/directories safely
- [ ] `file find <pattern>` - Search for files by pattern
- [ ] `file grep <pattern> <path>` - Search within files

### Git Operations
- [ ] `git add <pattern>` - Add files to staging area
- [ ] `git commit -m <message>` - Commit changes with message
- [ ] `git push` - Push to remote repository
- [ ] `git push --force-with-lease` - Safe force push
- [ ] `git status` - Show repository status
- [ ] `git pull` - Pull from remote repository
- [ ] `git branch` - List/create/delete branches
- [ ] `git checkout <branch>` - Switch branches
- [ ] `git merge <branch>` - Merge branches
- [ ] `git rebase <branch>` - Rebase current branch
- [ ] `git log` - Show commit history
- [ ] `git diff` - Show changes
- [ ] `git stash` - Stash changes
- [ ] `git tag` - Create/list tags

### Protocol Buffer Operations
- [ ] `buf generate` - Generate all protocol buffers
- [ ] `buf generate --module <name>` - Generate specific module
- [ ] `buf lint` - Lint protocol buffer files
- [ ] `buf format` - Format protocol buffer files
- [ ] `buf breaking` - Check for breaking changes
- [ ] `buf build` - Build protocol buffer modules

### Python Development
- [ ] `python run <script>` - Run Python scripts
- [ ] `python build` - Build Python projects
- [ ] `python test` - Run Python tests
- [ ] `python lint` - Lint Python code
- [ ] `python format` - Format Python code
- [ ] `python install <package>` - Install Python packages
- [ ] `uv run <command>` - Run commands with uv
- [ ] `uv install` - Install dependencies with uv
- [ ] `uv sync` - Sync environment with uv
- [ ] `pip install <package>` - Install with pip
- [ ] `poetry run <command>` - Run with poetry
- [ ] `poetry install` - Install with poetry

### Node.js/JavaScript Development
- [ ] `npm install` - Install npm dependencies
- [ ] `npm run <script>` - Run npm scripts
- [ ] `npm test` - Run npm tests
- [ ] `npm build` - Build npm projects
- [ ] `npx <command>` - Execute npm packages
- [ ] `yarn install` - Install with yarn
- [ ] `yarn run <script>` - Run with yarn
- [ ] `pnpm install` - Install with pnpm
- [ ] `node <script>` - Run Node.js scripts

### Go Development
- [ ] `go build` - Build Go projects
- [ ] `go run <file>` - Run Go programs
- [ ] `go test` - Run Go tests
- [ ] `go mod tidy` - Clean up go.mod
- [ ] `go mod download` - Download dependencies
- [ ] `go fmt` - Format Go code
- [ ] `go vet` - Vet Go code
- [ ] `go generate` - Run go generate

### Docker Operations
- [ ] `docker build` - Build Docker images
- [ ] `docker run` - Run Docker containers
- [ ] `docker compose up` - Start services
- [ ] `docker compose down` - Stop services
- [ ] `docker ps` - List containers
- [ ] `docker images` - List images
- [ ] `docker logs` - Show container logs

### System Utilities
- [ ] `sys ps` - Show running processes
- [ ] `sys top` - Show system resources
- [ ] `sys df` - Show disk usage
- [ ] `sys env` - Show environment variables
- [ ] `sys path` - Show PATH variable
- [ ] `sys which <command>` - Find command location

### Archive Operations
- [ ] `archive zip <src> <dst>` - Create zip archives
- [ ] `archive unzip <src> <dst>` - Extract zip archives
- [ ] `archive tar <src> <dst>` - Create tar archives
- [ ] `archive untar <src> <dst>` - Extract tar archives

### Network Utilities
- [ ] `net ping <host>` - Ping network hosts
- [ ] `net curl <url>` - Make HTTP requests
- [ ] `net wget <url>` - Download files
- [ ] `net port <port>` - Check port availability

## Technical Features

### Core Infrastructure
- [ ] Command line argument parsing with Cobra
- [ ] Configuration management with Viper
- [ ] Structured logging with levels
- [ ] Error handling and recovery
- [ ] Cross-platform compatibility
- [ ] Signal handling for graceful shutdown

### Logging and Output
- [ ] Dual output (terminal + log files)
- [ ] Timestamped log entries
- [ ] Structured JSON logging option
- [ ] Log rotation and cleanup
- [ ] Colored terminal output
- [ ] Progress indicators for long operations

### VS Code Integration
- [ ] Task runner compatibility
- [ ] Problem matcher integration
- [ ] Output channel support
- [ ] Debug mode for development

### Safety and Reliability
- [ ] Command validation and sanitization
- [ ] Safe file operations with backups
- [ ] Dry-run mode for testing
- [ ] Interactive confirmation for destructive operations
- [ ] Automatic retry for network operations

### Configuration and Customization
- [ ] User configuration files
- [ ] Environment-specific settings
- [ ] Custom command aliases
- [ ] Plugin system for extensions
- [ ] Template system for common operations

## Future Enhancements

### Advanced Features
- [ ] Remote command execution over SSH
- [ ] Command history and replay
- [ ] Batch operation support
- [ ] Parallel execution for independent commands
- [ ] Command dependency resolution
- [ ] Integration with CI/CD systems

### Monitoring and Analytics
- [ ] Command execution metrics
- [ ] Performance profiling
- [ ] Usage statistics
- [ ] Error reporting and tracking

### UI/UX Improvements
- [ ] Interactive command selection
- [ ] Progress bars for long operations
- [ ] Command completion and suggestions
- [ ] Rich terminal output with formatting

## Implementation Priority

1. **Phase 1**: Core file and git operations
2. **Phase 2**: Protocol buffer and development tools
3. **Phase 3**: Advanced logging and VS Code integration
4. **Phase 4**: Safety features and configuration
5. **Phase 5**: Advanced features and monitoring

## Notes

- All commands should respect working directory context
- Logging should be consistent across all operations
- Error messages should be clear and actionable
- Performance should be optimized for common operations
- Documentation should be comprehensive and up-to-date
"""

    with open(target_dir / "TODO.md", "w") as f:
        f.write(todo_content)


def create_initial_go_files(repo_name):
    """Create initial Go source files."""
    target_dir = Path(f"/Users/jdfalk/repos/github.com/jdfalk/{repo_name}")

    # Main application file
    main_go_content = f"""// file: cmd/copilot-agent-util/main.go
// version: 1.0.0
// guid: {generate_guid()}

package main

import (
	"fmt"
	"os"

	"github.com/jdfalk/{repo_name}/pkg/executor"
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{{
	Use:   "copilot-agent-util",
	Short: "Centralized utility for Copilot/AI agent command execution",
	Long: `A reliable command execution utility designed to solve VS Code task
execution issues and provide consistent logging for Copilot/AI agent operations.`,
	Run: func(cmd *cobra.Command, args []string) {{
		cmd.Help()
	}},
}}

func init() {{
	// Add subcommands
	rootCmd.AddCommand(executor.NewExecCommand())
	rootCmd.AddCommand(executor.NewGitCommand())
	rootCmd.AddCommand(executor.NewBufCommand())
	rootCmd.AddCommand(executor.NewFileCommand())
	rootCmd.AddCommand(executor.NewPythonCommand())
	rootCmd.AddCommand(executor.NewNpmCommand())
}}

func main() {{
	if err := rootCmd.Execute(); err != nil {{
		fmt.Fprintf(os.Stderr, "Error: %v\\n", err)
		os.Exit(1)
	}}
}}
"""

    with open(target_dir / "cmd/copilot-agent-util/main.go", "w") as f:
        f.write(main_go_content)

    # Executor package - simplified to avoid f-string issues
    executor_content = (
        """// file: pkg/executor/executor.go
// version: 1.0.0
// guid: """
        + generate_guid()
        + """

package executor

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"time"

	"github.com/spf13/cobra"
)

// ExecutorConfig holds configuration for command execution
type ExecutorConfig struct {
	WorkingDir string
	LogDir     string
	Verbose    bool
}

// DefaultConfig returns default configuration
func DefaultConfig() *ExecutorConfig {
	wd, _ := os.Getwd()
	return &ExecutorConfig{
		WorkingDir: wd,
		LogDir:     filepath.Join(wd, "logs"),
		Verbose:    false,
	}
}

// EnsureLogDir creates the log directory if it doesn't exist
func (e *ExecutorConfig) EnsureLogDir() error {
	if _, err := os.Stat(e.LogDir); os.IsNotExist(err) {
		return os.MkdirAll(e.LogDir, 0755)
	}
	return nil
}

// NewExecCommand creates the exec command
func NewExecCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "exec [command]",
		Short: "Execute arbitrary commands",
		Args:  cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			config := DefaultConfig()
			config.EnsureLogDir()

			fmt.Printf("Executing: %v\\n", args)

			command := exec.Command(args[0], args[1:]...)
			command.Dir = config.WorkingDir
			command.Stdout = os.Stdout
			command.Stderr = os.Stderr

			if err := command.Run(); err != nil {
				fmt.Fprintf(os.Stderr, "Command failed: %v\\n", err)
				os.Exit(1)
			}
		},
	}
}

// NewGitCommand creates git subcommands
func NewGitCommand() *cobra.Command {
	gitCmd := &cobra.Command{
		Use:   "git",
		Short: "Git operations",
	}

	// git add
	gitCmd.AddCommand(&cobra.Command{
		Use:   "add [files...]",
		Short: "Add files to staging area",
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) == 0 {
				args = []string{"."}
			}
			executeGitCommand("add", args...)
		},
	})

	// git commit
	gitCmd.AddCommand(&cobra.Command{
		Use:   "commit",
		Short: "Commit changes",
		Run: func(cmd *cobra.Command, args []string) {
			message, _ := cmd.Flags().GetString("message")
			if message == "" {
				message = "feat: automated commit via copilot-agent-util"
			}
			executeGitCommand("commit", "-m", message)
		},
	})

	// git push
	gitCmd.AddCommand(&cobra.Command{
		Use:   "push",
		Short: "Push to remote repository",
		Run: func(cmd *cobra.Command, args []string) {
			forceWithLease, _ := cmd.Flags().GetBool("force-with-lease")
			if forceWithLease {
				executeGitCommand("push", "--force-with-lease")
			} else {
				executeGitCommand("push")
			}
		},
	})

	// Add flags
	gitCmd.PersistentFlags().StringP("message", "m", "", "Commit message")
	gitCmd.PersistentFlags().Bool("force-with-lease", false, "Force push with lease")

	return gitCmd
}

// NewBufCommand creates buf subcommands
func NewBufCommand() *cobra.Command {
	bufCmd := &cobra.Command{
		Use:   "buf",
		Short: "Protocol buffer operations",
	}

	bufCmd.AddCommand(&cobra.Command{
		Use:   "generate",
		Short: "Generate protocol buffers",
		Run: func(cmd *cobra.Command, args []string) {
			module, _ := cmd.Flags().GetString("module")
			if module != "" {
				executeBufCommand("generate", "--path", fmt.Sprintf("pkg/%s/proto", module))
			} else {
				executeBufCommand("generate")
			}
		},
	})

	bufCmd.PersistentFlags().String("module", "", "Specific module to generate")

	return bufCmd
}

// NewFileCommand creates file operation subcommands
func NewFileCommand() *cobra.Command {
	fileCmd := &cobra.Command{
		Use:   "file",
		Short: "File operations",
	}

	fileCmd.AddCommand(&cobra.Command{
		Use:   "ls [path]",
		Short: "List directory contents",
		Run: func(cmd *cobra.Command, args []string) {
			path := "."
			if len(args) > 0 {
				path = args[0]
			}
			executeCommand("ls", "-la", path)
		},
	})

	fileCmd.AddCommand(&cobra.Command{
		Use:   "cat [file]",
		Short: "Display file contents",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			executeCommand("cat", args[0])
		},
	})

	return fileCmd
}

// NewPythonCommand creates Python development subcommands
func NewPythonCommand() *cobra.Command {
	pythonCmd := &cobra.Command{
		Use:   "python",
		Short: "Python development tools",
	}

	pythonCmd.AddCommand(&cobra.Command{
		Use:   "run [script]",
		Short: "Run Python script",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			executeCommand("python3", args[0])
		},
	})

	return pythonCmd
}

// NewNpmCommand creates npm/node subcommands
func NewNpmCommand() *cobra.Command {
	npmCmd := &cobra.Command{
		Use:   "npm",
		Short: "npm/node operations",
	}

	npmCmd.AddCommand(&cobra.Command{
		Use:   "install",
		Short: "Install npm dependencies",
		Run: func(cmd *cobra.Command, args []string) {
			executeCommand("npm", "install")
		},
	})

	return npmCmd
}

// Helper functions
func executeGitCommand(args ...string) {
	executeCommand("git", args...)
}

func executeBufCommand(args ...string) {
	executeCommand("buf", args...)
}

func executeCommand(name string, args ...string) {
	config := DefaultConfig()
	config.EnsureLogDir()

	logFile := filepath.Join(config.LogDir, fmt.Sprintf("%s_%d.log", name, time.Now().Unix()))

	fmt.Printf("Executing: %s %v\\n", name, args)
	fmt.Printf("Log file: %s\\n", logFile)

	command := exec.Command(name, args...)
	command.Dir = config.WorkingDir
	command.Stdout = os.Stdout
	command.Stderr = os.Stderr

	if err := command.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Command failed: %v\\n", err)
		os.Exit(1)
	}

	fmt.Println("Command completed successfully")
}
"""
    )

    with open(target_dir / "pkg/executor/executor.go", "w") as f:
        f.write(executor_content)


def generate_guid():
    """Generate a simple GUID-like string."""
    import uuid

    return str(uuid.uuid4())


def commit_initial_files(repo_name):
    """Commit the initial files to the repository."""
    target_dir = Path(f"/Users/jdfalk/repos/github.com/jdfalk/{repo_name}")

    print("Committing initial files...")

    run_command("git add .", cwd=target_dir)
    run_command(
        [
            "git",
            "commit",
            "-m",
            "feat: initial setup of copilot-agent-util with standard layout and Go structure",
        ],
        cwd=target_dir,
    )
    run_command("git push", cwd=target_dir)


def main():
    """Main function to orchestrate the repository creation."""
    print("Creating copilot-agent-util repository...")

    # Check requirements
    check_requirements()

    # Create repository
    repo_name = create_repository()

    # Copy standard files
    copy_standard_files(repo_name)

    # Create Go project structure
    create_go_project_structure(repo_name)

    # Create documentation
    create_readme(repo_name)
    create_todo(repo_name)

    # Create initial Go files
    create_initial_go_files(repo_name)

    # Commit everything
    commit_initial_files(repo_name)

    print(f"\\n✅ Repository {repo_name} created successfully!")
    print(f"📁 Location: /Users/jdfalk/repos/github.com/jdfalk/{repo_name}")
    print(f"🌐 GitHub: https://github.com/jdfalk/{repo_name}")
    print("\\nNext steps:")
    print("1. Review the TODO.md for planned features")
    print("2. Build the initial version: go build cmd/copilot-agent-util/main.go")
    print("3. Test basic commands: ./main exec 'echo hello'")
    print("4. Update VS Code tasks to use the new utility")


if __name__ == "__main__":
    main()
