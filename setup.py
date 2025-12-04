"""
Setup script for GeospatialAnalysis tool
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="geospatial-analysis",
    version="1.0.0",
    author="Christopher Tritt",
    description="Geospatial analysis tool for rail corridor flood vulnerability assessment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/christophertritt/GeospatialAnalysis",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "geospatial-analysis=scripts.geospatial_analysis:main",
        ],
    },
)
