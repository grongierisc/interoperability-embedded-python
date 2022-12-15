import setuptools

setuptools.setup(
    name="iris_pex_embedded_python",
    version="2.0.0",
    author="Guillaume Rongier",
    author_email="guillaume.rongier@intersystems.com",
    url="https://www.intersystems.com/",
    description="Python Interoperability kit",
    requires=['dacite'],
    python_requires='>=3.6.6',
    include_package_data=True,
    package_dir={'': 'src'},
    packages=['grongier.pex', 'grongier.iris'],
)
