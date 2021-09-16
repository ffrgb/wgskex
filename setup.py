import os
import subprocess

from setuptools import setup, find_packages


# Utility function to determine version using git in a PEP-440 compatible way
def determine_version():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    version = "0.0.0"

    if not os.path.isdir(os.path.join(dir_path, ".git")):
        return version

    try:
        output = subprocess.check_output(["git", "describe", "--tags", "--dirty"], cwd=dir_path) \
            .decode("utf-8").strip().split("-")
        if len(output) == 1:
            return output[0]
        elif len(output) == 2:
            return "{}.dev0".format(output[0])
        else:
            release = "dev" if len(output) == 4 and output[3] == "dirty" else ""
            return "{}.{}{}+{}".format(output[0], release, output[1], output[2])
    except subprocess.CalledProcessError:
        try:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
            status = subprocess.check_output(["git", "status", "-s"]).decode("utf-8").strip()
            return "{}.dev0+{}".format(version, commit) if len(status) > 0 else "{}+{}".format(version, commit)
        except subprocess.CalledProcessError:
            # finding the git version has utterly failed
            return version


setup(
    name="wgskex",
    version=determine_version(),
    author="Markus Hauschild",
    author_email="markus@moepman.eu",
    description="WireGuard Simple Key Exchange",
    license="ISC",
    url="https://github.com/ffrgb/wgskex",
    packages=find_packages(exclude="tests"),
    install_requires=["FastAPI==0.65.1", "pydantic", "pyroute2", "pyzmq", "uvicorn"],
    setup_requires=["wheel"],
    entry_points={
        "console_scripts": [
            "worker=wgskex.worker.main:main",
        ],
    },
)
