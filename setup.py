from setuptools import setup, find_packages

setup(
    name="pymx",
    version="1.2.2",
    packages=find_packages(),
    namespace_packages=['pymx'],
    python_requires='>=3.11',
    install_requires=[
        'starlette>=0.27.0',
        'uvicorn>=0.23.2',
        'requests>=2.31.0',
        'pythonnet==3.0.5',
        'anyio==4.9.0',
        "pydantic>=2.11.1",
        "typing_extensions==4.13.0",
        "mcp==1.12.2",
        "sse_starlette==1.6.5",
    ],
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'black>=21.0',
            'flake8>=3.9.0',
            'isort>=5.0.0',
        ],
    },
    author="wengao.liu",
    author_email="wengao.liu@mendix.com",
    description="Python API for Mendix Studio Pro",
    long_description="",
    long_description_content_type="text/markdown",
    url="",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
)
