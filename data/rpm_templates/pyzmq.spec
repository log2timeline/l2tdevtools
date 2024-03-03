%define name pyzmq
%define version {version}
%define release 1
%define py_setup_args --zmq=bundled

Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
License: LGPL+BSD
Summary: Python bindings for 0MQ
Url: https://pyzmq.readthedocs.org
Vendor: Brian E. Granger, Min Ragan-Kelley <zeromq-dev@lists.zeromq.org>
Source0: %{{name}}-%{{version}}.tar.gz
BuildRequires: gcc, gcc-c++, python3-devel, python3-packaging, python3-scikit-build-core, python3-setuptools

%description
PyZMQ is the official Python binding for the ZeroMQ
Messaging Library (http://www.zeromq.org).

%package -n python3-zmq
Summary: Python bindings for 0MQ

%description -n python3-zmq
PyZMQ is the official Python binding for the ZeroMQ
Messaging Library (http://www.zeromq.org).

%prep
%autosetup -p1 -n %{{name}}-%{{version}}

%build
%pyproject_wheel

%install
%pyproject_install

%files -n python3-zmq
%license LICENSE.BSD LICENSE.LESSER
%doc AUTHORS.md README.md
%{{_libdir}}/python3*/site-packages/zmq
%{{_libdir}}/python3*/site-packages/pyzmq*.dist-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
