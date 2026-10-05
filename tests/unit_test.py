#!/usr/bin/env python3

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_SCRIPT = Path(__file__).resolve().parent.parent / "src" / "pyproject" / "pyproject.py"


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
        package = src_dir / "splitter"
        tests_dir = project / "tests"

        # Check project root
        self.assertTrue(project.is_dir())
        
        # Check src layout
        self.assertTrue(src_dir.is_dir())
        self.assertTrue(package.is_dir())

        # Check package files
        self.assertTrue((package / "__init__.py").exists())
        self.assertTrue((package / "splitter.py").exists())

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
        new_package = new_src_dir / "mytool"
        new_tests_dir = new_project / "tests"

        self.assertFalse(old_project.exists())
        self.assertTrue(new_project.is_dir())
        
        # Check src layout
        self.assertTrue(new_src_dir.is_dir())
        self.assertTrue(new_package.is_dir())

        # Check package files
        self.assertTrue((new_package / "__init__.py").exists())
        self.assertTrue((new_package / "mytool.py").exists())

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
            'mytool = "mytool.mytool:main"',
            content,
        )
        self.assertIn('where = ["src"]', content)

        self.assertNotIn("splitter", content)

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
            "Unable to locate old project 'splitter'",
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
