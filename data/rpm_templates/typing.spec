%define name typing
%define version {version}
%define unmangled_name typing
%define unmangled_version {version}
%define release 1

Summary: Type Hints for Python
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Jukka Lehtosalo <jukka.lehtosalo@iki.fi>
Url: http://pypi.org/project/typing/
BuildRequires: python2-setuptools, python3-setuptools

%description
Backport of the standard library typing module to Python versions older
than 3.5.

%package -n python-%{{name}}
Summary: Type Hints for Python

%description -n python-%{{name}}
Backport of the standard library typing module to Python versions older
than 3.5.

%package -n python3-%{{name}}
Summary: Type Hints for Python

%description -n python3-%{{name}}
Backport of the standard library typing module to Python versions older
than 3.5.

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
python2 setup.py build
python3 setup.py build

%install
python2 setup.py install -O1 --root=%{{buildroot}}
python3 setup.py install -O1 --root=%{{buildroot}}
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python-%{{name}}
%license LICENSE
%doc CHANGES
/usr/lib/python2*/site-packages/

%files -n python3-%{{name}}
%license LICENSE
%doc CHANGES
/usr/lib/python3*/site-packages/

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
