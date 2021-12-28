%define name pyzmq
%define version {version}
%define unmangled_name pyzmq
%define unmangled_version {version}
%define release 1
%define py_setup_args --zmq=bundled

Summary: Python bindings for 0MQ
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: LGPL+BSD
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
Vendor: Brian E. Granger, Min Ragan-Kelley <zeromq-dev@lists.zeromq.org>
Url: https://pyzmq.readthedocs.org
BuildRequires: gcc, gcc-c++, python3-setuptools, python3-devel, python3-packaging

%description
PyZMQ is the official Python binding for the ZeroMQ
Messaging Library (http://www.zeromq.org).

%package -n python3-zmq
Summary: Python bindings for 0MQ

%description -n python3-zmq
PyZMQ is the official Python binding for the ZeroMQ
Messaging Library (http://www.zeromq.org).

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/lib/python*/site-packages/*.egg-info/requires.txt
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-zmq
%{{_libdir}}/python3*/site-packages/zmq/
%{{_libdir}}/python3*/site-packages/pyzmq*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
