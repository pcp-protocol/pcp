"""Bundles the files the suite reads (requirement list, schemas, validator)
into the installed package, laid out as in the repository, so that
`pip install` of this repository gives a suite that runs anywhere."""
import pathlib
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py

HERE = pathlib.Path(__file__).resolve().parent
BUNDLE = [("docs/conformance.md", "docs/conformance.md"),
          ("schemas/0.3", "schemas/0.3"),
          ("scripts/validate_schemas.py", "scripts/validate_schemas.py")]


class BuildPy(build_py):
    def run(self):
        super().run()
        data = pathlib.Path(self.build_lib) / "pcp_conformance" / "data"
        for src, dst in BUNDLE:
            s, d = HERE / src, data / dst
            d.parent.mkdir(parents=True, exist_ok=True)
            if s.is_dir():
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)


setup(cmdclass={"build_py": BuildPy})
