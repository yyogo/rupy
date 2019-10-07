from rupy import __version__
from setuptools import setup

setup(
    name='rupy',
    version=__version__,
    packages=['rupy'],
    url='https://gitlab.com/rekodah/rupy',
    license='MIT License',
    author='Jonathan Goren',
    author_email='jonagn@gmail.com',
    description='Random Useful Python utilities and stuff (Definitely not a backronym)',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Topic :: Security"
    )
)
