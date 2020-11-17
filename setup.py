from setuptools import setup, find_packages

setup(
    name="wgskex",
    version="0.1.0",
    author="Markus Hauschild",
    author_email="markus@moepman.eu",
    description="WireGuard Simple Key Exchange",
    license="ISC",
    url="https://github.com/ffrgb/wgskex",
    packages=find_packages(exclude="tests"),
    install_requires=["FastAPI", "pydantic", "pyroute2"],
    setup_requires=["wheel"],
)
