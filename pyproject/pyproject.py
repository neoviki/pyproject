#!/usr/bin/env python3

import re
import sys
import datetime
from pathlib import Path


VERSION = "1.0.0"


def is_valid_project_name(name):
    return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", name) is not None


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
{project_name} = "{project_name}.{project_name}:main"

[tool.setuptools.packages.find]
include = ["{project_name}*"]
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
    file_path = package_dir / f"{project_name}.py"
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
    file_path.write_text(f'''#!/bin/bash\n\npipx uninstall {project_name}\n''')
    file_path.chmod(0o755)


def create_unit_test(package_dir, project_name):
    content = f'''import unittest

import {project_name}


class TestProject(unittest.TestCase):

    def test_version(self):
        self.assertEqual({project_name}.__version__, "1.0.0")


if __name__ == "__main__":
    unittest.main()
'''
    (package_dir / "unit_test.py").write_text(content)


def create_unit_test_script(package_dir):
    file_path = package_dir / "unit_test"
    file_path.write_text('''#!/bin/bash\n\npython3 -m unittest unit_test.py -v\n''')
    file_path.chmod(0o755)


def create_commit_script(project_dir):
    file_path = project_dir / "commit"
    file_path.write_text('''#!/bin/bash\n\ngit add .\ngit commit -m "auto"\ngit push\n''')
    file_path.chmod(0o755)


def create_readme(project_dir, project_name, description):
    # This avoids triple-quote syntax errors entirely by using a list of strings
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
        f"cd {project_name}",
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
build
pyproject.egg-info
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

    project_dir.mkdir()
    package_dir = project_dir / project_name
    package_dir.mkdir()

    create_pyproject_file(project_dir, project_name, description)
    create_init_file(package_dir)
    create_main_file(package_dir, project_name)
    create_install_script(project_dir, project_name)
    create_uninstall_script(project_dir, project_name)
    create_unit_test(package_dir, project_name)
    create_unit_test_script(package_dir)
    create_commit_script(project_dir)
    create_readme(project_dir, project_name, description)
    create_license(project_dir, license_user)
    create_gitignore(project_dir)

    print(f"Project '{project_name}' created successfully at {project_dir}")


def rename_project(old_name, new_name):
    if not is_valid_project_name(new_name):
        print(f"Error: invalid project name '{new_name}'.")
        sys.exit(1)

    old_path = Path(old_name)
    if not old_path.is_absolute():
        old_path = Path.cwd() / old_name

    if not old_path.exists() or not old_path.is_dir():
        print(f"Unable to locate old project '{old_name}'")
        old_path_str = input("Enter path to old project: ").strip()
        old_path = Path(old_path_str).expanduser().resolve()
        if not old_path.exists() or not old_path.is_dir():
            print(f"Error: path '{old_path}' does not exist or is not a directory.")
            sys.exit(1)

    old_project_name = old_path.name
    new_path = old_path.parent / new_name

    if new_path.exists():
        print(f"Error: target project '{new_name}' already exists at {new_path}")
        sys.exit(1)

    old_package_dir = old_path / old_project_name
    if not old_package_dir.exists():
        print(f"Error: could not find package directory '{old_package_dir}'")
        sys.exit(1)

    # Rename directories
    old_path.rename(new_path)
    new_package_dir = new_path / old_project_name
    new_package_dir.rename(new_path / new_name)
    new_package_dir = new_path / new_name

    # Update text files
    files_to_update = [
        new_path / "pyproject.toml",
        new_path / "README.md",
        new_path / "install.sh",
        new_path / "uninstall.sh",
        new_package_dir / "unit_test.py",
    ]

    for file_path in files_to_update:
        if file_path.exists():
            content = file_path.read_text()
            content = content.replace(old_project_name, new_name)
            file_path.write_text(content)

    # Rename and update main script
    old_main_script = new_package_dir / f"{old_project_name}.py"
    if old_main_script.exists():
        new_main_script = new_package_dir / f"{new_name}.py"
        content = old_main_script.read_text()
        content = content.replace(old_project_name, new_name)
        old_main_script.rename(new_main_script)
        new_main_script.write_text(content)

    print(f"Project renamed from '{old_project_name}' to '{new_name}' successfully.")


def main():
    args = sys.argv[1:]

    if not args:
        project_name = input("Enter project name: ").strip()
        if not project_name:
            print("Error: project name cannot be empty.")
            sys.exit(1)
        create_project(project_name)
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
    else:
        project_name = args[0]
        create_project(project_name)


if __name__ == "__main__":
    main()
