# Installation Guide

Welcome to the installation guide for IoP. This guide will walk you through the steps to install the application on your local machine or in a docker container image.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.6 or higher
- IRIS 2021.1 or higher
- Embedded Python configured in IRIS
  - [Configuring Embedded Python](TODO: Add link to the guide)

## With PyPi

To install the application using PyPi, run the following command:

```bash
pip install iris-pex-embedded-python
```

Then you can run the application using the following command:

```bash
iop --init
```

Check the documentation about the command line interface [here](TODO: Add link to the guide) for more information.

## With ZPM/IPM

To install the application using ZPM or IPM, run the following command:

```objectscript
zpm "install iris-pex-embedded-python"
```

