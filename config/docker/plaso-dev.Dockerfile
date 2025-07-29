FROM ubuntu:noble
MAINTAINER Log2Timeline <log2timeline-dev@googlegroups.com>

# Create container with:
# docker build --no-cache --build-arg GITHUB_USERNAME="username" \
#   --force-rm -t log2timeline/plaso-dev .

ARG GITHUB_USERNAME="log2timeline"

ENV DEBIAN_FRONTEND=noninteractive

# Install essential dependencies
RUN apt-get -y clean
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install --no-install-recommends \
  automake \
  autotools-dev \
  build-essential \
  debhelper \
  devscripts \
  fakeroot \
  git \
  libtool \
  libyaml-dev \
  locales \
  mercurial \
  python3-build \
  python3-dev \
  python3-distutils \
  python3-setuptools \
  quilt \
  software-properties-common \
  sudo \
  wget

# Install Plaso dependencies from the GIFT PPA dev track
RUN add-apt-repository -y ppa:gift/dev
RUN apt-get -y update
RUN apt-get -y install --no-install-recommends $(apt-cache depends python3-plaso | grep Depends | sed 's/.*ends:\ //' | grep -ve '<.*>' | tr '\n' ' ')

# Install Plaso development dependencies from the GIFT PPA dev track
RUN apt-get -y install --no-install-recommends \
  pylint \
  python3-fakeredis \
  python3-mock \
  python3-sphinx

# Clean up apt-get cache files
# RUN apt-get clean && rm -rf /var/cache/apt/* /var/lib/apt/lists/*

# Set terminal to UTF-8 by default
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

# Set up the Plaso source directory
WORKDIR /root
RUN git clone https://github.com/${GITHUB_USERNAME}/plaso.git
WORKDIR /root/plaso
RUN if test "${GITHUB_USERNAME}" != "log2timeline"; then git remote add upstream https://github.com/log2timeline/plaso.git; fi
