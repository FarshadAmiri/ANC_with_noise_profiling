"""
Setup script for ANC with Noise Profiling package
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="anc-noise-profiling",
    version="1.0.0",
    author="Farshad Amiri",
    description="Active Noise Cancellation with automatic noise profiling for both real-time and file-based processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FarshadAmiri/ANC_with_noise_profiling",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Scientific/Engineering :: Artificial Intelligence", 
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.0.0", 
            "flake8>=3.8.0",
            "mypy>=0.812",
        ],
    },
    entry_points={
        "console_scripts": [
            "anc-noise-profiling=anc_noise_profiling.cli.main:main",
        ],
    },
    keywords="noise reduction, audio processing, active noise cancellation, real-time audio, signal processing",
    project_urls={
        "Bug Reports": "https://github.com/FarshadAmiri/ANC_with_noise_profiling/issues",
        "Source": "https://github.com/FarshadAmiri/ANC_with_noise_profiling",
        "Documentation": "https://github.com/FarshadAmiri/ANC_with_noise_profiling/blob/main/README.md",
    },
    include_package_data=True,
    zip_safe=False,
)