from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hopper",
    version="3.5.0",
    author="jilani-BLK",
    description="H.O.P.P.E.R: Human Operational Predictive Personal Enhanced Reactor - Phase 3.5 RAG Avancé",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.11",
    install_requires=[
        "pytest>=8.4.2",
        "pytest-asyncio>=0.24.0",
        "neo4j>=5.25.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "black>=24.0.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
    },
)
