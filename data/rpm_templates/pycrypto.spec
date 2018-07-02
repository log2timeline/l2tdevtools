%define name pycrypto
%define version {version}
%define unmangled_name pycrypto
%define unmangled_version {version}
%define release 1

%global debug_package %{{nil}}

Summary: Cryptographic modules for Python.
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
Vendor: Dwayne C. Litzenberger <dlitz@dlitz.net>
Url: http://www.pycrypto.org/
BuildRequires: python2-setuptools, python-devel, python3-setuptools, python3-devel

%description
Cryptographic modules for Python

%package -n python-crypto
Summary: Cryptographic modules for Python.

%description -n python-crypto
Cryptographic modules for Python

%package -n python3-crypto
Summary: Cryptographic modules for Python.

%description -n python3-crypto
Cryptographic modules for Python

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
env CFLAGS="$RPM_OPT_FLAGS" python setup.py build

%install
python2 setup.py install -O1 --root=%{{buildroot}}
python3 setup.py install -O1 --root=%{{buildroot}}
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python-crypto
%doc README
%{{_libdir}}/python2*/site-packages/Crypto/
%{{_libdir}}/python2*/site-packages/pycrypto*.egg-info

%files -n python3-crypto
%doc README
%{{_libdir}}/python3*/site-packages/Crypto/
%{{_libdir}}/python3*/site-packages/pycrypto*.egg-info

%exclude %{{_bindir}}/*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
