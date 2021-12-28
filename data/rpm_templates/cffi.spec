%define name cffi
%define version {version}
%define release 1

Summary: Foreign Function Interface for Python calling C code.
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{version}}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
Vendor: Armin Rigo, Maciej Fijalkowski <python-cffi@googlegroups.com>
Url: http://cffi.readthedocs.org
BuildRequires: gcc, python3-devel, python3-setuptools, libffi-devel

%description
Foreign Function Interface for Python calling C code

%package -n python3-%{{name}}
Summary: Python 3 module of Foreign Function Interface for Python calling C code.

%description -n python3-%{{name}}
Foreign Function Interface for Python calling C code

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

%{{_libdir}}/python3*/site-packages/_cffi*.so
%{{_libdir}}/python3*/site-packages/cffi
%{{_libdir}}/python3*/site-packages/cffi*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
