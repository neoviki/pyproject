# pyproject

A command-line tool to create, rename, and delete Python projects that are ready to be installed and managed via pipx.

Instead of manually creating pyproject.toml, `__init__.py`, install scripts, and unit test templates, pyproject generates a fully functional, pipx-ready project structure in seconds.

## Features

- Quick Project Creation: Generates a complete, PEP 517-compliant project structure with a fixed `src/app/main.py` layout — no project-name-dependent paths inside the package.
- Pipx-Ready: Includes pre-configured `install.sh` and `uninstall.sh` scripts for the generated projects.
- Smart Renaming: Uninstalls the old pipx package, renames the project, updates all references (`pyproject.toml`, `README.md`, helper scripts), and installs the new name — all in one command. Works from inside or outside the project directory.
- Project Deletion: Uninstalls the pipx package and removes the project directory in a single confirmed step.
- Built-in Testing: Generates a basic unittest suite and a runner script for the new project.
- Interactive Prompts: Guides you through adding a description and license user during creation.

## Installation

This tool itself is designed to be installed via pipx to keep your global environment clean.

### Option 1: Install directly from GitHub (Recommended)
You can install the latest version directly from the repository:
```bash
pipx install git+https://github.com/neoviki/pyproject.git
```

### Option 2: Install from a local clone
If you have cloned this repository to your local machine, you can install it using the included script:
```bash
./install.sh
```

## Uninstallation

To remove the tool from your system, run:
```bash
./uninstall.sh
```

## Usage

Once installed, the `pyproject` command will be available globally in your terminal. Run `pyproject help` to see all commands at any time.

### Create a New Project
Run the command followed by your desired project name:
```bash
pyproject my_awesome_tool
```
You will be prompted interactively for:
1. Project description: A brief summary of what the project does.
2. License user name: Your name or organization for the MIT license.

This will create a directory named `my_awesome_tool` with the complete project structure.

### Rename an Existing Project
Renaming uninstalls the old pipx package, renames the directory, updates all internal references, and installs the new name automatically:
```bash
# Provide both old and new names as arguments
pyproject rename my_awesome_tool my_better_tool

# Or provide just the old name, and it will prompt you for the new one
pyproject rename my_awesome_tool
```
(Note: You can also pass absolute or relative paths to the old project directory.)

Renaming works no matter where you execute it from:
```bash
# From outside the project
pyproject rename my_awesome_tool my_better_tool

# From inside the project directory
cd my_awesome_tool
pyproject rename my_awesome_tool my_better_tool
```

Because the package is always `app` and the entry module always `main.py`, renaming only touches the project folder name and `pyproject.toml` — the code inside `src/app/` never needs to change.

### Delete a Project
Deleting uninstalls the pipx package and removes the project directory, after asking for confirmation:
```bash
# From outside the project
pyproject delete my_awesome_tool

# From inside the project directory
cd my_awesome_tool
pyproject delete my_awesome_tool

# 'rm' and 'remove' are accepted as aliases
pyproject rm my_awesome_tool
```

### Help
Show all commands and the generated layout:
```bash
pyproject help
# or
pyproject --help
# or
pyproject -h
```

## Generated Project Structure

When you run `pyproject <name>`, it creates the following structure:

```text
<project_name>/
├── pyproject.toml              # PEP 517 build configuration
├── README.md                   # Project documentation
├── LICENSE                     # MIT License
├── .gitignore                  # Standard Python gitignore
├── install.sh                  # Script to install/reinstall via pipx
├── uninstall.sh                # Script to remove via pipx
├── commit                      # Quick git add/commit/push script
├── clean.sh                    # Removes build artifacts and caches
├── unit_test                   # Root-level test runner script
├── src/app/                    # The actual Python package (always named 'app')
│       ├── __init__.py         # Contains __version__
│       └── main.py             # Main entry point with main() function
└── tests/                      # Test directory (not shipped with package)
    ├── unit_test               # Executable bash script to run tests
    └── unit_test.py            # Basic unittest template
```

## Development and Testing

To contribute to pyproject or verify your local setup, you can run the built-in unit tests. The tests use Python's tempfile module to safely create and destroy dummy projects without affecting your actual filesystem.

```bash
# From the repository root
./unit_test

# Alternatively, run them directly with Python
cd tests
python3 -m unittest discover -s . -p "unit_test.py" -v
```

If the tool is not on your PATH, the tests locate it via `src/app/main.py` in the repository, or you can point them to it explicitly:
```bash
PYPROJECT_SCRIPT=/path/to/main.py ./unit_test
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.
