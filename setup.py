from setuptools import setup, find_packages

setup(
    name="mxpy",
    version="1.2.0",
    packages=find_packages(),
    namespace_packages=['mxpy'],
    python_requires='>=3.6',
    install_requires=[
        'starlette>=0.20.0',
        'uvicorn>=0.15.0',
        'requests>=2.25.0',
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