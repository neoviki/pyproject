#!/usr/bin/env python3

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


def is_pyproject_tool(script_path):
    """Sanity-check a candidate: it must respond to 'help' like our tool."""
    try:
        result = subprocess.run(
            ["python3", str(script_path), "help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception:
        return False
    return result.returncode == 0 and "Usage:" in result.stdout


def find_project_script():
    """Locate the scaffolder tool (kept at src/app/main.py).

    Order of resolution:
      1. PYPROJECT_SCRIPT environment variable (absolute path)
      2. a 'pyproject' command on PATH (e.g. pipx-installed)
      3. src/app/main.py in this repo, then main.py next to / above it
      4. src/app/main.py in a parent repository
    Each candidate is verified with a 'help' call so we never pick up a
    generated project template by mistake.
    """
    env_path = os.environ.get("PYPROJECT_SCRIPT")
    if env_path:
        path = Path(env_path).expanduser().resolve()
        if not path.is_file():
            raise RuntimeError(f"PYPROJECT_SCRIPT points to a missing file: {path}")
        return path

    on_path = shutil.which("pyproject")
    if on_path:
        return Path(on_path).resolve()

    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "src" / "app" / "main.py",          # this repo's src layout
        here.parent / "main.py",                          # flat next to tests/
        here.parent.parent / "main.py",
        here.parent.parent / "src" / "app" / "main.py",  # parent repo's src layout
    ]
    for candidate in candidates:
        if candidate.is_file() and is_pyproject_tool(candidate):
            return candidate.resolve()

    raise RuntimeError(
        "Could not locate the scaffolder tool. Expected it at src/app/main.py, "
        "on PATH as 'pyproject', or via PYPROJECT_SCRIPT=/path/to/main.py"
    )


PROJECT_SCRIPT = find_project_script()


class TestPyproject(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def run_pyproject(self, *arguments, input_text=None, cwd=None):
        if cwd is None:
            cwd = self.test_dir

        return subprocess.run(
            ["python3", str(PROJECT_SCRIPT), *arguments],
            cwd=cwd,
            input=input_text,
            text=True,
            capture_output=True,
        )

    def create_test_project(self, name="splitter"):
        result = self.run_pyproject(
            name,
            input_text="A simple test project\nVignesh | Viki\n",
        )

        self.assertEqual(
            result.returncode, 0,
            msg=f"Failed to create project.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_create_project(self):
        self.create_test_project()

        project = self.test_dir / "splitter"
        src_dir = project / "src"
        package = src_dir / "app"
        tests_dir = project / "tests"

        # Check project root
        self.assertTrue(project.is_dir())

        # Check src/app layout
        self.assertTrue(src_dir.is_dir())
        self.assertTrue(package.is_dir())

        # Check package files
        self.assertTrue((package / "__init__.py").exists())
        self.assertTrue((package / "main.py").exists())

        # Check tests directory
        self.assertTrue(tests_dir.is_dir())
        self.assertTrue((tests_dir / "unit_test.py").exists())
        self.assertTrue((tests_dir / "unit_test").exists())

        # Check root-level files
        self.assertTrue((project / "pyproject.toml").exists())
        self.assertTrue((project / "install.sh").exists())
        self.assertTrue((project / "uninstall.sh").exists())
        self.assertTrue((project / "clean.sh").exists())
        self.assertTrue((project / "README.md").exists())
        self.assertTrue((project / "LICENSE").exists())
        self.assertTrue((project / ".gitignore").exists())
        self.assertTrue((project / "commit").exists())

    def test_created_pyproject_content(self):
        self.create_test_project()

        content = (self.test_dir / "splitter" / "pyproject.toml").read_text()

        self.assertIn('name = "splitter"', content)
        self.assertIn('splitter = "app.main:main"', content)
        self.assertIn('where = ["src"]', content)

    def test_create_existing_project_fails(self):
        self.create_test_project()

        result = self.run_pyproject(
            "splitter",
            input_text="Another project\nAnother User\n",
        )

        self.assertNotEqual(result.returncode, 0)

        self.assertIn(
            "project already exists",
            result.stdout,
        )

    def test_help_command(self):
        result = self.run_pyproject("help")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
        self.assertIn("rename", result.stdout)
        self.assertIn("delete", result.stdout)
        self.assertIn("main.py", result.stdout)

    def test_help_short_flags(self):
        for flag in ("-h", "--help"):
            result = self.run_pyproject(flag)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Usage:", result.stdout)

    def test_rename_project(self):
        self.create_test_project()

        result = self.run_pyproject(
            "rename",
            "splitter",
            "mytool",
        )

        self.assertEqual(
            result.returncode, 0,
            msg=f"Failed to rename project.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        old_project = self.test_dir / "splitter"
        new_project = self.test_dir / "mytool"
        new_src_dir = new_project / "src"
        new_package = new_src_dir / "app"
        new_tests_dir = new_project / "tests"

        self.assertFalse(old_project.exists())
        self.assertTrue(new_project.is_dir())

        # Check src/app layout is untouched
        self.assertTrue(new_src_dir.is_dir())
        self.assertTrue(new_package.is_dir())
        self.assertTrue((new_package / "__init__.py").exists())
        self.assertTrue((new_package / "main.py").exists())

        # Check tests directory
        self.assertTrue(new_tests_dir.is_dir())
        self.assertTrue((new_tests_dir / "unit_test.py").exists())
        self.assertTrue((new_tests_dir / "unit_test").exists())

        # Check root-level files
        self.assertTrue((new_project / "pyproject.toml").exists())
        self.assertTrue((new_project / "install.sh").exists())
        self.assertTrue((new_project / "uninstall.sh").exists())
        self.assertTrue((new_project / "clean.sh").exists())
        self.assertTrue((new_project / "README.md").exists())
        self.assertTrue((new_project / "LICENSE").exists())
        self.assertTrue((new_project / ".gitignore").exists())
        self.assertTrue((new_project / "commit").exists())

    def test_rename_updates_pyproject(self):
        self.create_test_project()

        self.run_pyproject(
            "rename",
            "splitter",
            "mytool",
        )

        pyproject_file = self.test_dir / "mytool" / "pyproject.toml"
        content = pyproject_file.read_text()

        self.assertIn('name = "mytool"', content)
        self.assertIn(
            'mytool = "app.main:main"',
            content,
        )
        self.assertIn('where = ["src"]', content)

        self.assertNotIn("splitter", content)

    def test_rename_updates_scripts(self):
        self.create_test_project()

        self.run_pyproject(
            "rename",
            "splitter",
            "mytool",
        )

        install = (self.test_dir / "mytool" / "install.sh").read_text()
        uninstall = (self.test_dir / "mytool" / "uninstall.sh").read_text()

        self.assertIn("mytool", install)
        self.assertNotIn("splitter", install)
        self.assertIn("pipx uninstall mytool", uninstall)
        self.assertNotIn("splitter", uninstall)

    def test_rename_updates_readme(self):
        self.create_test_project()

        self.run_pyproject(
            "rename",
            "splitter",
            "mytool",
        )

        readme = self.test_dir / "mytool" / "README.md"
        content = readme.read_text()

        self.assertIn("# mytool", content)
        self.assertIn("mytool", content)
        self.assertIn("cd tests", content)
        self.assertNotIn("splitter", content)

    def test_rename_reports_pipx_status(self):
        self.create_test_project()

        result = self.run_pyproject(
            "rename",
            "splitter",
            "mytool",
        )

        # pipx package is not installed in the test environment: the tool
        # must note that gracefully instead of failing.
        self.assertTrue(
            "was not installed; skipping uninstall" in result.stdout
            or "pipx is not installed on this system" in result.stdout,
            msg=f"Unexpected stdout: {result.stdout}",
        )

    def test_rename_using_full_path(self):
        self.create_test_project()

        project_path = self.test_dir / "splitter"

        result = self.run_pyproject(
            "rename",
            str(project_path),
            "mytool",
        )

        self.assertEqual(result.returncode, 0)

        self.assertFalse(project_path.exists())
        self.assertTrue((self.test_dir / "mytool").exists())

    def test_rename_from_inside_project_directory(self):
        self.create_test_project()

        project_path = self.test_dir / "splitter"

        # Execute from inside the project directory
        result = self.run_pyproject(
            "rename",
            "splitter",
            "mytool",
            cwd=project_path,
        )

        self.assertEqual(
            result.returncode, 0,
            msg=f"Failed to rename from inside project.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        self.assertFalse(project_path.exists())
        self.assertTrue((self.test_dir / "mytool").exists())

    def test_rename_from_inside_without_name_argument(self):
        self.create_test_project()

        project_path = self.test_dir / "splitter"

        # Passing "." or the absolute path also works from inside
        result = self.run_pyproject(
            "rename",
            str(project_path),
            "mytool",
            cwd=project_path,
        )

        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.test_dir / "mytool").exists())

    def test_rename_from_different_directory(self):
        self.create_test_project()

        other_dir = self.test_dir / "sample"
        other_dir.mkdir()

        project_path = self.test_dir / "splitter"

        result = self.run_pyproject(
            "rename",
            "splitter",
            "mytool",
            input_text=f"{project_path}\n",
            cwd=other_dir,
        )

        self.assertEqual(result.returncode, 0)

        self.assertFalse(project_path.exists())
        self.assertTrue((self.test_dir / "mytool").exists())

        self.assertIn(
            "Unable to locate project 'splitter'",
            result.stdout,
        )

    def test_rename_existing_target_fails(self):
        self.create_test_project()

        (self.test_dir / "mytool").mkdir()

        result = self.run_pyproject(
            "rename",
            "splitter",
            "mytool",
        )

        self.assertNotEqual(result.returncode, 0)

        self.assertTrue((self.test_dir / "splitter").exists())
        self.assertTrue((self.test_dir / "mytool").exists())

    def test_rename_invalid_new_name_fails(self):
        self.create_test_project()

        result = self.run_pyproject(
            "rename",
            "splitter",
            "invalid name",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid project name", result.stdout)
        self.assertTrue((self.test_dir / "splitter").exists())

    def test_delete_project(self):
        self.create_test_project()

        project_path = self.test_dir / "splitter"

        result = self.run_pyproject(
            "delete",
            "splitter",
            input_text="y\n",
        )

        self.assertEqual(
            result.returncode, 0,
            msg=f"Failed to delete project.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        self.assertFalse(project_path.exists())

    def test_delete_project_cancelled(self):
        self.create_test_project()

        project_path = self.test_dir / "splitter"

        result = self.run_pyproject(
            "delete",
            "splitter",
            input_text="n\n",
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Deletion cancelled", result.stdout)
        self.assertTrue(project_path.exists())

    def test_delete_project_from_inside(self):
        self.create_test_project()

        project_path = self.test_dir / "splitter"

        result = self.run_pyproject(
            "delete",
            "splitter",
            input_text="y\n",
            cwd=project_path,
        )

        self.assertEqual(result.returncode, 0)
        self.assertFalse(project_path.exists())

    def test_delete_project_not_found(self):
        result = self.run_pyproject(
            "delete",
            "splitter",
            input_text="\n",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unable to locate project 'splitter'", result.stdout)

    def test_invalid_project_name(self):
        result = self.run_pyproject(
            "invalid name",
            input_text="Test project\nVignesh | Viki\n",
        )

        self.assertNotEqual(result.returncode, 0)

        self.assertIn(
            "invalid project name",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
