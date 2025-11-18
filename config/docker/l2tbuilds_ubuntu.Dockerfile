FROM ubuntu:noble

# Create container with:
# docker build -f l2tbuilds_ubuntu.Dockerfile --force-rm --no-cache -t log2timeline/l2tbuilds_ubuntu .

ENV DEBIAN_FRONTEND=noninteractive

# Combining the apt-get commands into a single run reduces the size of the resulting image.
# The apt-get installations below are interdependent and need to be done in sequence.
RUN apt-get -y update && \
    apt-get -y install apt-transport-https apt-utils && \
    apt-get -y install libterm-readline-gnu-perl software-properties-common && \
    apt-get -y upgrade && \
    apt-get -y install --no-install-recommends \
        autoconf \
        automake \
        autopoint \
        build-essential \
        byacc \
	cython3 \
        debhelper \
        devscripts \
        dh-autoreconf \
        dh-python \
        dput \
	fakeroot \
        flex \
        flit \
        git \
        gnupg2 \
	libdistro-info-perl \
	libbz2-dev \
	libffi-dev \
	libfuse-dev \
	liblzma-dev \
	libmagic-dev \
	libsqlite3-dev \
	libssl-dev \
        libtool \
	libyaml-dev \
        locales \
        pkg-config \
	pinentry-tty \
	pybuild-plugin-pyproject \
	pyproject-metadata \
        python3-all \
        python3-all-dev \
	python3-cffi \
	python3-build \
	python3-hatchling \
	python3-packaging \
	python3-pbr \
	python3-pkgconfig \
	python3-poetry-core \
	python3-pytest \
	python3-pytest-runner \
	python3-scikit-build-core \
        python3-setuptools \
	python3-setuptools-scm \
	python3-toml \
	python3-wheel \
        quilt \
        tox-current-env && \
    apt-get clean && rm -rf /var/cache/apt/* /var/lib/apt/lists/*

# Set terminal to UTF-8 by default
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Changes pinentry to use TTY
RUN update-alternatives --set pinentry /usr/bin/pinentry-tty

# Set up the l2tdevtools source and build directories
USER ubuntu
WORKDIR /home/ubuntu
RUN git clone https://github.com/log2timeline/l2tdevtools.git
