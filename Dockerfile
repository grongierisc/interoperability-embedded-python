ARG IMAGE=intersystemsdc/iris-community:latest
FROM $IMAGE

#COPY key/iris.key /usr/irissys/mgr/iris.key

USER root   

# Update package and install sudo
RUN apt-get update && apt-get install -y \
	nano \
	sudo && \
	/bin/echo -e ${ISC_PACKAGE_MGRUSER}\\tALL=\(ALL\)\\tNOPASSWD: ALL >> /etc/sudoers && \
	sudo -u ${ISC_PACKAGE_MGRUSER} sudo echo enabled passwordless sudo-ing for ${ISC_PACKAGE_MGRUSER}

        
WORKDIR /irisdev/app
RUN chown ${ISC_PACKAGE_MGRUSER}:${ISC_PACKAGE_IRISGROUP} /irisdev/app
USER ${ISC_PACKAGE_MGRUSER}

## Python stuff
ENV IRISUSERNAME "SuperUser"
ENV IRISPASSWORD "SYS"
ENV IRISNAMESPACE "IRISAPP"

ENV PYTHON_PATH=/usr/irissys/bin/

ENV PATH "/usr/irissys/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/irisowner/bin"

COPY . .
COPY iris.script /tmp/iris.script

RUN pip3 install -r demo/python/requirements.txt

RUN iris start IRIS \
	&& iris session IRIS < /tmp/iris.script \
	&& /usr/irissys/bin/irispython /irisdev/app/demo/python/register.py \
    && iris stop IRIS quietly
