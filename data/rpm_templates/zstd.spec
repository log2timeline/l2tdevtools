%define name zstd
%define version 1.5.5.1
%define release 1

Summary: ZSTD Bindings for Python
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{version}}.tar.gz
License: BSD
Group: Development/Libraries
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Sergey Dryabzhinsky <sergey.dryabzhinsky@gmail.com>
Url: https://github.com/sergey-dryabzhinsky/python-zstd
BuildRequires: python3-devel, python3-setuptools

%description
Python bindings to Yann Collet ZSTD compression library.

%package -n python3-%{{name}}
Summary: Python 3 module of ZSTD Bindings for Python

%description -n python3-%{{name}}
Python bindings to Yann Collet ZSTD compression library.

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
%{{_libdir}}/python3*/site-packages/zstd*.so
%{{_libdir}}/python3*/site-packages/zstd*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
