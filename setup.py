# Licensed under the MIT License
# https://github.com/grongierisc/iris_pex_embedded_python/blob/main/LICENSE

import os

from setuptools import setup, find_packages

def main():
    # Read the readme for use as the long description
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'README.md'), encoding='utf-8') as readme_file:
        long_description = readme_file.read()

    # Do the setup
    setup(
        name='iris_pex_embedded_python',
        description='iris_pex_embedded_python',
        long_description=long_description,
        long_description_content_type='text/markdown',
        version='2.3.18',
        author='grongier',
        author_email='guillaume.rongier@intersystems.com',
        keywords='iris_pex_embedded_python',
        url='https://github.com/grongierisc/interoperability-embedded-python',
        license='MIT',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Topic :: Utilities'
        ],
        package_dir={'': 'src'},
        packages=find_packages(where='src'),
        package_data={'grongier.cls': ['**/*.cls']},
        python_requires='>=3.6',
        install_requires=[
            "dacite>=1.6.0",
            "xmltodict>=0.12.0",
        ],
        entry_points={
            'console_scripts': [
                # create an iop command that point to the main of the grongier.pex package
                'iop = grongier.pex._cli:main',
            ],
        }
    )


if __name__ == '__main__':
    main()
