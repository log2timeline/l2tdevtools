%define name pytsk3
%define version {version}
%define release 1

Summary: Python bindings for the sleuthkit
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{version}}.tar.gz
License: Apache 2.0
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
Vendor: Michael Cohen and Joachim Metz <scudette@gmail.com, joachim.metz@gmail.com>
Packager: Joachim Metz <joachim.metz@gmail.com>
Url: https://github.com/py4n6/pytsk/
BuildRequires: gcc, python3-devel, python3-setuptools, gcc-c++, libstdc++-devel

%description
Python bindings for the sleuthkit (http://www.sleuthkit.org/)

%package -n python3-%{{name}}
Summary: Python 3 module of Python bindings for the sleuthkit

%description -n python3-%{{name}}
Python bindings for the sleuthkit (http://www.sleuthkit.org/)

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
%doc README
%{{_libdir}}/python3*/site-packages/pytsk3*.so
%{{_libdir}}/python3*/site-packages/pytsk3*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
