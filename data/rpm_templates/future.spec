%define name future
%define version {version}
%define unmangled_name future
%define unmangled_version {version}
%define release 1

Summary: Clean single-source support for Python 3 and 2
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Ed Schofield <ed@pythoncharmers.com>
Url: https://python-future.org
BuildRequires: python2-setuptools, python3-setuptools

%description
future is the missing compatibility layer between Python 2
and Python 3. It allows you to use a single, clean Python 3.x-compatible
codebase to support both Python 2 and Python 3 with minimal overhead.

%package -n python-%{{name}}
Summary: Clean single-source support for Python 3 and 2

%description -n python-%{{name}}
future is the missing compatibility layer between Python 2
and Python 3. It allows you to use a single, clean Python 3.x-compatible
codebase to support both Python 2 and Python 3 with minimal overhead.

%package -n python3-%{{name}}
Summary: Clean single-source support for Python 3 and 2

%description -n python3-%{{name}}
future is the missing compatibility layer between Python 2
and Python 3. It allows you to use a single, clean Python 3.x-compatible
codebase to support both Python 2 and Python 3 with minimal overhead.

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
python2 setup.py build
rm -rf %{{_builddir}}/%{{unmangled_name}}-%{{unmangled_version}}/build
python3 setup.py build

%install
python2 setup.py install -O1 --root=%{{buildroot}}
rm -rf %{{_builddir}}/%{{unmangled_name}}-%{{unmangled_version}}/build
python3 setup.py install -O1 --root=%{{buildroot}}
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python-%{{name}}
%license LICENSE.txt
/usr/lib/python2*/site-packages/*

%files -n python3-%{{name}}
%license LICENSE.txt
/usr/lib/python3*/site-packages/*

%exclude %{{_bindir}}/*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
