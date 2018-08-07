FROM ubuntu:xenial

ARG PLASO_REVISION

######################
# Install basic deps #
######################
RUN apt-get clean
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y build-essential \
  autotools-dev \
  libsqlite3-dev \
  python-dev \
  debhelper \
  devscripts \
  fakeroot \
  quilt \
  git \
  mercurial \
  python-setuptools \
  libtool \
  automake \
  libyaml-dev \
  software-properties-common \
  wget \
  sudo

####################
# Add GIFT dev PPA #
####################
RUN add-apt-repository ppa:gift/dev
RUN mkdir install
WORKDIR install
RUN wget https://raw.githubusercontent.com/log2timeline/plaso/${PLASO_REVISION}/config/linux/gift_ppa_install.sh
RUN chmod 775 ./gift_ppa_install.sh
RUN ./gift_ppa_install.sh include-development include-test include-debug

####################################
# Set terminal to UTF-8 by default #
####################################
RUN apt-get install -y locales
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

#####################
# Set final workdir #
#####################
WORKDIR /root/plaso
