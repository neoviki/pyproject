#!/usr/bin/env python3

import re
import sys
import shutil
import subprocess
import datetime
from pathlib import Path


VERSION = "1.2.0"
PACKAGE_DIR_NAME = "app"
ENTRY_MODULE = "main"


def is_valid_project_name(name):
    return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", name) is not None


def print_help():
    print(f"pyproject {VERSION}")
    print()
    print("Scaffold a Python project in pipx format (src/app/main.py layout).")
    print()
    print("Usage:")
    print("  main.py                          Interactive: create a new project")
    print("  main.py <project_name>           Create a new project")
    print("  main.py rename <old> <new>       Uninstall old pipx package, rename, install new")
    print("                                     (works from inside or outside the project dir)")
    print("  main.py delete <name>            Uninstall pipx package and delete the directory")
    print("                                     (works from inside or outside the project dir)")
    print("  main.py help                     Show this help")
    print()
    print("Project layout created:")
    print("  <project_name>/")
    print("    src/app/main.py                 <- all your code lives here")
    print("    tests/unit_test.py")
    print("    pyproject.toml                  <- entry point: <name> = \"app.main:main\"")
    print()
    print("Because the package is always 'app' and the module always 'main.py',")
    print("renaming only touches the project folder name and pyproject.toml.")


def ask_project_description():
    while True:
        description = input("What is this project all about? ").strip()
        if description:
            return description
        print("Error: project description cannot be empty.")


def ask_license_user():
    while True:
        user = input("License user name: ").strip()
        if user:
            return user
        print("Error: license user name cannot be empty.")


def create_pyproject_file(project_dir, project_name, description):
    content = f'''[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "1.0.0"
description = "{description}"
readme = "README.md"
requires-python = ">=3.9"
license = {{text = "MIT"}}

[project.scripts]
{project_name} = "{PACKAGE_DIR_NAME}.{ENTRY_MODULE}:main"

[tool.setuptools.packages.find]
where = ["src"]
'''
    (project_dir / "pyproject.toml").write_text(content)


def create_init_file(package_dir):
    (package_dir / "__init__.py").write_text('__version__ = "1.0.0"\n')


def create_main_file(package_dir, project_name):
    content = f'''#!/usr/bin/env python3


def main():
    print("{project_name}")


if __name__ == "__main__":
    main()
'''
    file_path = package_dir / f"{ENTRY_MODULE}.py"
    file_path.write_text(content)
    file_path.chmod(0o755)


def create_install_script(project_dir, project_name):
    content = f'''#!/bin/bash

if pipx list | grep -q "package {project_name}"; then
    read -r -p "A previous installation of {project_name} exists and will be removed. Do you wish to continue? [y/n]: " answer

    if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
        echo "Installation cancelled."
        exit 0
    fi

    pipx uninstall {project_name} 2>/dev/null 1>/dev/null
fi

pipx install .
'''
    file_path = project_dir / "install.sh"
    file_path.write_text(content)
    file_path.chmod(0o755)


def create_uninstall_script(project_dir, project_name):
    file_path = project_dir / "uninstall.sh"
    file_path.write_text(f'#!/bin/bash\n\npipx uninstall {project_name}\n')
    file_path.chmod(0o755)


def create_unit_test(tests_dir, project_name):
    content = f'''import sys
import unittest
from pathlib import Path

# Add src directory to Python path so we can import the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import {PACKAGE_DIR_NAME}


class TestProject(unittest.TestCase):

    def test_version(self):
        self.assertEqual({PACKAGE_DIR_NAME}.__version__, "1.0.0")


if __name__ == "__main__":
    unittest.main()
'''
    (tests_dir / "unit_test.py").write_text(content)


def create_unit_test_script(tests_dir):
    file_path = tests_dir / "unit_test"
    file_path.write_text('#!/bin/bash\n\npython3 -m unittest discover -s . -p "unit_test.py" -v\n')
    file_path.chmod(0o755)


def create_unit_test_script2(project_dir):
    file_path = project_dir / "unit_test"
    file_path.write_text('''#!/bin/bash

cd "$(dirname "$0")"

# unittest discover inserts the tests dir into sys.path, so the test
# module imports as top-level 'unit_test' without needing __init__.py.
python3 -m unittest discover -s tests -p "unit_test.py" -v
''')
    file_path.chmod(0o755)


def create_commit_script(project_dir):
    file_path = project_dir / "commit"
    file_path.write_text('#!/bin/bash\n\ngit add .\ngit commit -m "auto"\ngit push\n')
    file_path.chmod(0o755)


def create_clean_script(project_dir):
    content = f'''#!/bin/bash

rm -rf src/{PACKAGE_DIR_NAME}/__pycache__
rm -rf build src/*.egg-info __pycache__ tests/__pycache__

echo "Cleaned build artifacts and cache files."
'''
    file_path = project_dir / "clean.sh"
    file_path.write_text(content)
    file_path.chmod(0o755)


def create_readme(project_dir, project_name, description):
    lines = [
        f"# {project_name}",
        "",
        description,
        "",
        "## Installation",
        "",
        "```bash",
        "./install.sh",
        "```",
        "",
        "## Usage",
        "",
        "```bash",
        project_name,
        "```",
        "",
        "## Testing",
        "",
        "```bash",
        "cd tests",
        "./unit_test",
        "```",
        ""
    ]
    content = "\n".join(lines)
    (project_dir / "README.md").write_text(content)


def create_license(project_dir, user):
    year = datetime.datetime.now().year
    content = f"""MIT License

Copyright (c) {year} {user}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    (project_dir / "LICENSE").write_text(content)


def create_gitignore(project_dir):
    content = """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.venv/
venv/
ENV/
pyproject.egg-info/
"""
    (project_dir / ".gitignore").write_text(content)


def create_project(project_name):
    if not is_valid_project_name(project_name):
        print(f"Error: invalid project name '{project_name}'.")
        sys.exit(1)

    project_dir = Path.cwd() / project_name
    if project_dir.exists():
        print(f"Error: project already exists at {project_dir}")
        sys.exit(1)

    description = ask_project_description()
    license_user = ask_license_user()

    # Create directory structure: src/app/main.py
    project_dir.mkdir()
    src_dir = project_dir / "src"
    src_dir.mkdir()
    package_dir = src_dir / PACKAGE_DIR_NAME
    package_dir.mkdir()
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()

    create_pyproject_file(project_dir, project_name, description)
    create_init_file(package_dir)
    create_main_file(package_dir, project_name)
    create_install_script(project_dir, project_name)
    create_uninstall_script(project_dir, project_name)
    create_unit_test(tests_dir, project_name)
    create_unit_test_script(tests_dir)
    create_unit_test_script2(project_dir)
    create_commit_script(project_dir)
    create_clean_script(project_dir)
    create_readme(project_dir, project_name, description)
    create_license(project_dir, license_user)
    create_gitignore(project_dir)

    print(f"Project '{project_name}' created successfully at {project_dir}")


def pipx_uninstall(project_name):
    try:
        result = subprocess.run(
            ["pipx", "uninstall", project_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("Note: pipx is not installed on this system; skipping uninstall.")
        return False
    return result.returncode == 0


def pipx_install(project_path):
    try:
        result = subprocess.run(
            ["pipx", "install", str(project_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("Warning: pipx is not installed on this system; skipping install.")
        return False
    return result.returncode == 0


def resolve_project_path(name):
    """Locate a project whether the name given is a path, we are inside
    the project directory, or we are outside next to it."""
    cwd = Path.cwd()
    candidate = Path(name)
    if candidate.is_absolute():
        if (candidate / "pyproject.toml").exists():
            return candidate.resolve()
        return None

    # Direct path relative to cwd (inside or outside the project)
    if (candidate / "pyproject.toml").exists():
        return candidate.resolve()

    # We are INSIDE the project directory (cwd is the project root)
    if (cwd / "pyproject.toml").exists() and cwd.name == name:
        return cwd.resolve()

    # cwd is a parent directory containing the project
    if (cwd / name / "pyproject.toml").exists():
        return (cwd / name).resolve()

    # Deep inside the project dir: walk up looking for the named project root
    for parent in [cwd, *cwd.parents]:
        if parent.name == name and (parent / "pyproject.toml").exists():
            return parent.resolve()

    return None


def rename_project(old_name, new_name):
    if not is_valid_project_name(new_name):
        print(f"Error: invalid project name '{new_name}'.")
        sys.exit(1)

    old_path = resolve_project_path(old_name)

    if old_path is None:
        print(f"Unable to locate project '{old_name}'.")
        old_path_str = input("Enter path to project: ").strip()
        candidate = Path(old_path_str).expanduser()
        if (candidate / "pyproject.toml").exists():
            old_path = candidate.resolve()
        else:
            print(f"Error: path '{candidate}' does not contain a valid project (no pyproject.toml).")
            sys.exit(1)

    old_project_name = old_path.name
    new_path = old_path.parent / new_name

    if new_path.exists():
        print(f"Error: target project '{new_name}' already exists at {new_path}")
        sys.exit(1)

    if new_path.parent == Path.cwd().resolve():
        # renaming the directory we are sitting in is fine, nothing to do
        pass

    # 1. Uninstall the old pipx package
    if pipx_uninstall(old_project_name):
        print(f"Uninstalled pipx package '{old_project_name}'.")
    else:
        print(f"Note: pipx package '{old_project_name}' was not installed; skipping uninstall.")

    # 2. Rename the project folder
    old_path.rename(new_path)

    # 3. Update pyproject.toml (project name + console script entry point)
    pyproject_new = new_path / "pyproject.toml"
    lines = []
    for line in pyproject_new.read_text().splitlines():
        stripped = line.strip()
        if stripped == f'name = "{old_project_name}"':
            line = f'name = "{new_name}"'
        elif stripped == f'{old_project_name} = "{PACKAGE_DIR_NAME}.{ENTRY_MODULE}:main"':
            line = f'{new_name} = "{PACKAGE_DIR_NAME}.{ENTRY_MODULE}:main"'
        lines.append(line)
    pyproject_new.write_text("\n".join(lines) + "\n")

    # 4. Update helper scripts that reference the pipx package name
    for script_name in ("install.sh", "uninstall.sh"):
        script_path = new_path / script_name
        if script_path.exists():
            text = script_path.read_text()
            text = text.replace(old_project_name, new_name)
            script_path.write_text(text)

    # 5. Update README
    readme_path = new_path / "README.md"
    if readme_path.exists():
        text = readme_path.read_text()
        text = text.replace(old_project_name, new_name)
        readme_path.write_text(text)

    print(f"Project renamed from '{old_project_name}' to '{new_name}' successfully.")

    # 6. Install the new pipx package
    if pipx_install(new_path):
        print(f"Installed pipx package '{new_name}'.")
    else:
        print(f"Warning: 'pipx install' failed. Run './install.sh' inside '{new_name}' manually.")


def delete_project(project_name):
    project_path = resolve_project_path(project_name)

    if project_path is None:
        print(f"Unable to locate project '{project_name}'.")
        project_path_str = input("Enter path to project: ").strip()
        candidate = Path(project_path_str).expanduser()
        if (candidate / "pyproject.toml").exists():
            project_path = candidate.resolve()
        else:
            print(f"Error: path '{candidate}' does not contain a valid project (no pyproject.toml).")
            sys.exit(1)

    name = project_path.name

    confirm = input(f"This will uninstall '{name}' from pipx and permanently delete '{project_path}'. Continue? [y/n]: ").strip()
    if confirm not in ("y", "Y"):
        print("Deletion cancelled.")
        return

    # 1. Uninstall the pipx package
    if pipx_uninstall(name):
        print(f"Uninstalled pipx package '{name}'.")
    else:
        print(f"Note: pipx package '{name}' was not installed; skipping uninstall.")

    # 2. Delete the project directory
    shutil.rmtree(project_path)
    print(f"Project '{name}' deleted ({project_path} removed).")


def main():
    args = sys.argv[1:]

    if not args:
        project_name = input("Enter project name: ").strip()
        if not project_name:
            print("Error: project name cannot be empty.")
            sys.exit(1)
        create_project(project_name)
    elif args[0] in ("help", "-h", "--help"):
        print_help()
    elif args[0] == "rename":
        if len(args) >= 3:
            old_name = args[1]
            new_name = args[2]
        elif len(args) == 2:
            old_name = args[1]
            new_name = input("Enter new project name: ").strip()
            if not new_name:
                print("Error: new project name cannot be empty.")
                sys.exit(1)
        else:
            old_name = input("Enter old project name or path: ").strip()
            if not old_name:
                print("Error: old project name cannot be empty.")
                sys.exit(1)
            new_name = input("Enter new project name: ").strip()
            if not new_name:
                print("Error: new project name cannot be empty.")
                sys.exit(1)

        rename_project(old_name, new_name)
    elif args[0] in ("delete", "rm", "remove"):
        if len(args) >= 2:
            project_name = args[1]
        else:
            project_name = input("Enter project name or path to delete: ").strip()
            if not project_name:
                print("Error: project name cannot be empty.")
                sys.exit(1)

        delete_project(project_name)
    else:
        project_name = args[0]
        create_project(project_name)


if __name__ == "__main__":
    main()
