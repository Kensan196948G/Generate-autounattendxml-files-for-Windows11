#!/usr/bin/env python3
"""
Windows 11 Sysprep応答ファイル生成システム - セットアップスクリプト
"""

from setuptools import setup, find_packages
import os

# README.mdの内容を読み込む
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# requirements.txtから依存関係を読み込む
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

setup(
    name="windows11-sysprep-generator",
    version="1.0.0",
    author="Windows 11 Sysprep Generator Team",
    author_email="contact@example.com",
    description="Windows 11のSysprep応答ファイル（autounattend.xml）自動生成システム",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/windows11-sysprep-generator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "win11-sysprep-gen=src.core.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src.templates": ["*.xml", "*.json"],
        "src.schemas": ["*.xsd"],
        "src.configs": ["*.yaml", "*.json"],
    },
)