from setuptools import setup, find_packages

setup(
    name="wgskex",
    version="0.2.0",
    author="Markus Hauschild",
    author_email="markus@moepman.eu",
    description="WireGuard Simple Key Exchange",
    license="ISC",
    url="https://github.com/ffrgb/wgskex",
    packages=find_packages(exclude="tests"),
    install_requires=["FastAPI", "pydantic", "pyroute2", "pyzmq", "uvicorn"],
    setup_requires=["wheel"],
    entry_points={
        "console_scripts": [
            "worker=wgskex.worker.main:main",
        ],
    },
)
