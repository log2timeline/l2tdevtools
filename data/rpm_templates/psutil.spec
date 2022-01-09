%define name psutil
%define version {version}
%define release 1

Summary: Cross-platform lib for process and system monitoring in Python.
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{version}}.tar.gz
License: BSD
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
Vendor: Giampaolo Rodola <g.rodola@gmail.com>
Url: https://github.com/giampaolo/psutil
BuildRequires: gcc, python3-devel, python3-setuptools

%description
psutil is a cross-platform library for retrieving information
on running processes and system utilization (CPU, memory, disks, network)
in Python.

%package -n python3-%{{name}}
Summary: Python 3 module of Cross-platform lib for process and system monitoring in Python.

%description -n python3-%{{name}}
psutil is a cross-platform library for retrieving information
on running processes and system utilization (CPU, memory, disks, network)
in Python.

%prep
%autosetup -n %{{name}}-%{{version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/lib/python*/site-packages/*.egg-info/requires.txt
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-%{{name}}
%license LICENSE

%{{_libdir}}/python3*/site-packages/psutil
%{{_libdir}}/python3*/site-packages/psutil*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
