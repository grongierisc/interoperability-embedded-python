# Licensed under the MIT License
# https://github.com/grongierisc/iris_pex_embedded_python/blob/main/LICENSE

import os

from setuptools import setup

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('.', path, filename))
    return paths

extra_files = package_files('src/grongier/iris')

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
        version='2.1.1',
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
        packages=['grongier.pex','grongier.iris'],
        include_package_data=True,
        python_requires='>=3.6',
        install_requires=[
            "dacite>=1.6.0",
        ]
    )


if __name__ == '__main__':
    main()
