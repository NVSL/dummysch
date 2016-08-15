from setuptools import setup, find_packages
import os
import sys
from codecs import open

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(os.path.join(here, 'VERSION.txt'), encoding='utf-8') as f:
    version = f.read()


setup(name="dummysch",
      version=version,
      long_description=long_description,
      author="NVSL, University of California San Diego",
      packages = find_packages(),
      #install_requires=["jinja2", "Checkers"],
      #dependency_links = ['ssh+git:git@github.com:NVSL/Checkers.git#egg=Checkers-0.1.0'],
      #dependency_links = ['file://' + os.environ['GADGETRON_ROOT'] + "/Tools/Checkers#egg=Checkers-0.1.0",
      #                ],
      entry_points={
          'console_scripts': [
              "dummysch = dummy_sch.dummy_sch:main",
              "dummysch.py = dummy_sch.dummy_sch:main"
          ]
      }
)
