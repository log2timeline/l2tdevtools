%define name efilter
%define version {version}
%define unmangled_name efilter
%define unmangled_version {version}
%define release 1

Summary: EFILTER query language
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: Apache 2.0
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/dotty-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Adam Sindelar <adam.sindelar@gmail.com>
Packager: Adam Sindelar <adam.sindelar@gmail.com>
Url: https://github.com/google/dotty/
BuildRequires: python2-setuptools, python2-devel, python3-setuptools, python3-devel

%description
EFILTER is a general-purpose destructuring and search language implemented in Python, and suitable for integration with any Python project that requires a search function for some of its data.

%package -n python-%{{name}}
Summary: EFILTER query language
Requires: python2-dateutil, python2-six >= 1.4.0, python2-pytz

%description -n python-%{{name}}
EFILTER is a general-purpose destructuring and search language implemented in Python, and suitable for integration with any Python project that requires a search function for some of its data.

%package -n python3-%{{name}}
Summary: EFILTER query language
Requires: python3-dateutil, python3-six >= 1.4.0, python3-pytz

%description -n python3-%{{name}}
EFILTER is a general-purpose destructuring and search language implemented in Python, and suitable for integration with any Python project that requires a search function for some of its data.

%prep
%autosetup -n dotty-%{{unmangled_version}}

%build
%py2_build
%py3_build

%install
%py2_install -O1 --root=%{{buildroot}}
%py3_install -O1 --root=%{{buildroot}}
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python-%{{name}}
%license LICENSE.txt
/usr/lib/python2*/site-packages/efilter/
/usr/lib/python2*/site-packages/efilter*.egg-info

%files -n python3-%{{name}}
%license LICENSE.txt
/usr/lib/python3*/site-packages/efilter/
/usr/lib/python3*/site-packages/efilter*.egg-info

%exclude /usr/lib/python2*/site-packages/sample_projects
%exclude /usr/lib/python3*/site-packages/sample_projects

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
