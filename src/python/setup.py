import setuptools

setuptools.setup(
    name="grongier_pex",
    version="1.5.3",
    author="Guillaume Rongier",
    author_email="guillaume.rongier@intersystems.com",
    url="https://www.intersystems.com/",
    description="Python Interoperability kit",
    packages=['grongier.pex','grongier.dacite'],
    python_requires='>=3.6.6',
)