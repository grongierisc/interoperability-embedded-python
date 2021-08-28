import setuptools

setuptools.setup(
    name="grongier_pex",
    version="1.0.0",
    author="Guillaume Rongier",
    author_email="guillaume.rongier@intersystems.com",
    url="https://www.intersystems.com/",
    description="Python InterOperability Kit",
    packages=['grongier.pex'],
    python_requires='>=3.6.6',
)