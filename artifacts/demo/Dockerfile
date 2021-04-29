FROM python:3.9.4
ARG USER="demo-user"
ARG INSTALL_DIR="/home/${USER}/.figgy/installations/first"
ARG FIGGY_MFA_SECRET_OVERRIDE
ARG FIGGY_PASSWORD_OVERRIDE
ARG FIGGY_KEYRING_PASSWORD="KyR1ingP@sS1Word!!D"
ARG OKTA_EMBED_URL

RUN apt update -y && \
    apt upgrade -y && \
    apt install -y curl sudo unzip libusb-1.0-0-dev libxmu-dev libxmu-headers \
                freeglut3-dev libxext-dev libxi-dev libudev1 libudev-dev libc-bin binutils

RUN useradd -ms /bin/bash demo-user
WORKDIR /home/demo-user


RUN mkdir -p ${INSTALL_DIR} && \
    cd ${INSTALL_DIR} && curl -s https://www.figgy.dev/releases/cli/unstable/linux/figgy.zip > figgy.zip && \
    unzip figgy.zip > /dev/null && \
    ln -snf ${INSTALL_DIR}/figgy/figgy /usr/local/bin/figgy && \
    mkdir -p /home/${USER}/.figgy/cache/other && \
    chown -R ${USER}:${USER} "/home/${USER}/.figgy" && \
    mkdir -p "/home/${USER}/source" && chown -R ${USER}:${USER} "/home/${USER}/source"


COPY artifacts/demo/config /home/${USER}/.figgy/config
COPY artifacts/demo/defaults.json /home/${USER}/.figgy/cache/other/defaults.json
RUN sed --in-place 's#\${OKTA_EMBED_URL}#${OKTA_EMBED_URL}#g' /home/${USER}/.figgy/config

USER demo-user

# Inject embed url

#######################################################################
# For local development, does not use Pyinstaller compiled figgy-cli  #
#######################################################################

# Faster builds, copy and install requirements first.
#COPY src/requirements.txt /home/${USER}/source
#COPY src/requirements-linux.txt /home/${USER}/source

#RUN pip install -r source/requirements.txt
#RUN pip install -r source/requirements-linux.txt

## Copy source dir last
#COPY src/ /home/${USER}/source

### Injected overrides to enable one-command execution for demos.
ENV FIGGY_MFA_SECRET_OVERRIDE=$FIGGY_MFA_SECRET_OVERRIDE
ENV FIGGY_PASSWORD_OVERRIDE=$FIGGY_PASSWORD_OVERRIDE
ENV FIGGY_KEYRING_PASSWORD=$FIGGY_KEYRING_PASSWORD

EXPOSE 5000
ENTRYPOINT ["figgy"]
CMD ["ui"]