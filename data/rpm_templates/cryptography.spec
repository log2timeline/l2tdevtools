%define name cryptography
%define version 3.4.7
%define release 1

Summary: cryptography is a package which provides cryptographic recipes and primitives to Python developers.
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{version}}.tar.gz
License: BSD or Apache License, Version 2.0
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
Vendor: The Python Cryptographic Authority and individual contributors <cryptography-dev@python.org>
Url: https://github.com/pyca/cryptography
BuildRequires: gcc, python3-devel, python3-setuptools, libffi-devel, openssl-devel, python3-cffi, python3-setuptools-rust

%description
cryptography is a package which provides cryptographic
recipes and primitives to Python developers

%package -n python3-%{{name}}
Summary: Python 3 module of cryptography is a package which provides cryptographic recipes and primitives to Python developers.

%description -n python3-%{{name}}
cryptography is a package which provides cryptographic
recipes and primitives to Python developers

%prep
%autosetup -n %{{name}}-%{{version}}

%build
CRYPTOGRAPHY_DONT_BUILD_RUST=1 %py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-%{{name}}
%license LICENSE

%{{_libdir}}/python3*/site-packages/cryptography
%{{_libdir}}/python3*/site-packages/cryptography*.egg-info

%changelog
* {{date_time}} log2timeline development team <log2timeline-dev@googlegroups.com> {{version}}-1
- Auto-generated
