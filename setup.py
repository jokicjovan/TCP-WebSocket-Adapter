from setuptools import setup, find_packages

setup(
    name="TCPWebSocketAdapter",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "websockets>=10.0",
        "asyncio",
    ],
    tests_require=[
        "pytest",
    ],
    test_suite="tests",
    author="Jovan Jokic",
    author_email="<EMAIL>",
    description="A library to bridge TCP and WebSocket connections.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jokicjovan",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
