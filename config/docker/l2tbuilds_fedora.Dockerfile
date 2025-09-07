FROM fedora:42

# Create container with:
# docker build -f l2tbuilds_fedora.Dockerfile --force-rm --no-cache -t log2timeline/l2tbuilds_fedora .

RUN dnf install -y @development-tools autoconf automake byacc dnf-plugins-core flex gcc-c++ gettext-devel git langpacks-en libtool pkg-config python3 python3-build python3-devel python3-setuptools python3-wheel

# Set up the l2tdevtools source and build directories
WORKDIR /home/build/
RUN git clone https://github.com/log2timeline/l2tdevtools.git
