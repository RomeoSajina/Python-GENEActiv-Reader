from setuptools import setup

setup(
    name="Python-GENEActiv-Reader",
    url="https://github.com/RomeoSajina/Python-GENEActiv",
    author="Romeo Sajina",
    author_email="romeo.sajina@gmail.com",
    # Needed to actually package something
    packages=["geneactiv_reader"],
    install_requires=["pandas", "bitstring", "numpy"],
    version="0.1",
    license="MIT",
    description="Simple package for loading .bin files from GENEActiv accelerometers",
    long_description=open("README.md").read(),
)
