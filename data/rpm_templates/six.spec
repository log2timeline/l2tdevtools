%define name six
%define version {version}
%define unmangled_name six
%define unmangled_version {version}
%define release 1

Summary: Python 2 and 3 compatibility utilities
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Benjamin Peterson <benjamin@python.org>
Url: http://pypi.org/project/six/
BuildRequires: python2-setuptools, python3-setuptools

%description
Six is a Python 2 and 3 compatibility library. It provides
utility functions for smoothing over the differences between the Python
versions with the goal of writing Python code that is compatible on both
Python versions.

%package -n python-%{{name}}
Summary: Python 2 and 3 compatibility utilities

%description -n python-%{{name}}
Six is a Python 2 and 3 compatibility library. It provides
utility functions for smoothing over the differences between the Python
versions with the goal of writing Python code that is compatible on both
Python versions.

%package -n python3-%{{name}}
Summary: Python 2 and 3 compatibility utilities

%description -n python3-%{{name}}
Six is a Python 2 and 3 compatibility library. It provides
utility functions for smoothing over the differences between the Python
versions with the goal of writing Python code that is compatible on both
Python versions.

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
