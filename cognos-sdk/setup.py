"""Setup configuration for CognOS SDK."""

from setuptools import setup, find_packages
from pathlib import Path

readme_file = Path(__file__).parent / "README.md"
readme_content = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="cognos-sdk",
    version="0.1.0",
    description="Trust verification SDK for LLM applications",
    long_description=readme_content,
    long_description_content_type="text/markdown",
    author="Base76 Research Lab",
    author_email="hello@base76.se",
    url="https://github.com/base76-research-lab/operational-cognos",
    project_urls={
        "GitHub": "https://github.com/base76-research-lab/operational-cognos",
        "Documentation": "https://docs.cognos.base76.se",
        "Issues": "https://github.com/base76-research-lab/operational-cognos/issues",
    },
    packages=find_packages(),
    install_requires=[
        "httpx>=0.27.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "black>=24.0.0",
            "mypy>=1.0.0",
            "ruff>=0.2.0",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Monitoring",
    ],
    keywords=[
        "ai",
        "llm",
        "trust",
        "verification",
        "compliance",
        "audit",
        "openai",
        "anthropic",
        "google",
    ],
    zip_safe=False,
)
