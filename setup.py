from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pytest-gui",
    version="1.0.0",
    author="Pytest GUI Team",
    author_email="contact@pytest-gui.com",
    description="A modern GUI application for running pytest tests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pytest-gui/pytest-gui",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PySide6>=6.5.0",
        "pytest>=7.0.0",
        "python-dotenv>=1.0.0",
        "watchdog>=3.0.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": [
            "pytest-qt>=4.2.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pytest-gui=pytest_gui.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "pytest_gui": ["resources/*", "resources/**/*"],
    },
)