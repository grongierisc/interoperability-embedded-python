ARG IMAGE=containers.intersystems.com/intersystems/iris-community:2021.2.0.617.0
FROM $IMAGE

#COPY key/iris.key /usr/irissys/mgr/iris.key

USER root   

# Update package and install sudo
RUN apt-get update && apt-get install -y \
	nano \
	python3-pip \
	python3-venv \
	sudo && \
	/bin/echo -e ${ISC_PACKAGE_MGRUSER}\\tALL=\(ALL\)\\tNOPASSWD: ALL >> /etc/sudoers && \
	sudo -u ${ISC_PACKAGE_MGRUSER} sudo echo enabled passwordless sudo-ing for ${ISC_PACKAGE_MGRUSER}

        
WORKDIR /opt/irisapp
RUN chown ${ISC_PACKAGE_MGRUSER}:${ISC_PACKAGE_IRISGROUP} /opt/irisapp
USER ${ISC_PACKAGE_MGRUSER}

## Python stuff
ENV IRISUSERNAME "SuperUser"
ENV IRISPASSWORD "SYS"

ENV PYTHON_PATH=/usr/irissys/bin/

ENV PATH "/usr/irissys/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/irisowner/bin"


COPY  Installer.cls .
COPY  src src
COPY iris.script /tmp/iris.script

## Install grongier-pex wheel
RUN /usr/irissys/bin/irispython -m pip install /opt/irisapp/src/python/dist/grongier_pex-1.0.0-py3-none-any.whl

RUN iris start IRIS \
	&& iris session IRIS < /tmp/iris.script \
    && iris stop IRIS quietly
