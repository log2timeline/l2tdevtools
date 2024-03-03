%define name Flor
%define version {version}
%define release 1

Summary: Flor - An efficient Bloom filter implementation in Python
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{version}}.tar.gz
License: BSD3
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Andreas Dewes - DCSO GmbH <andreas.dewes@dcso.de>
Url: https://github.com/DCSO/flor
BuildRequires: python3-devel, python3-setuptools

%description
A Bloom filter implementation in Python

%package -n python3-flor
Summary: Python 3 module of Flor - An efficient Bloom filter implementation in Python

%description -n python3-flor
A Bloom filter implementation in Python

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

%files -n python3-flor
%doc README.md
%{{python3_sitelib}}/flor
%{{python3_sitelib}}/Flor*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
