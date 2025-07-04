# Contributing

## Run the unit tests

To run the unit tests, you must follow the steps below:

### Create a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

### Install the dependencies.

```bash
pip install -r requirements-dev.txt
```

### Have a running IRIS instance.

Here you can choose between:

- Local installation of IRIS
- Docker installation of IRIS

#### Local installation of IRIS

##### Install IRIS locally.
   
- [Local installation of IRIS](https://docs.intersystems.com/irislatest/csp/docbook/Doc.View.cls?KEY=PAGE_deployment_install)
- [Python interpreter compatible with the version of IRIS](https://docs.intersystems.com/iris20243/csp/docbook/Doc.View.cls?KEY=GEPYTHON_prereqs#GEPYTHON_prereqs_version)
- [Iris embedded python wrapper](https://github.com/grongierisc/iris-embedded-python-wrapper)
    - Make sure to follow the [instructions to install the wrapper in your IRIS instance.](https://github.com/grongierisc/iris-embedded-python-wrapper?tab=readme-ov-file#pre-requisites)


##### Set up the IRIS instance.

Then, symbolically link this git repository to the IRIS python directory:

```bash
ln -s <your_git_dir>/src/iop $IRISINSTALLDIR/python/iop
```

##### Run the unit tests.

```bash
pytest
```

#### Docker installation of IRIS

No prerequisites are needed. Just run the following command:

```bash
docker build -t pytest-iris -f dockerfile-ci .
docker run -i --rm pytest-iris
```
