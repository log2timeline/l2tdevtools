%define name dateutil
%define version {version}
%define unmangled_name dateutil
%define unmangled_version {version}
%define release 1

Summary: Extensions to the standard Python datetime module
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: python-%{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: Simplified BSD
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Paul Ganssle <dateutil@python.org>
Url: https://dateutil.readthedocs.io
BuildRequires: python2-setuptools, python2-setuptools_scm, python2-devel, python3-setuptools, python3-setuptools_scm, python3-devel

%description
The dateutil module provides powerful extensions to the
datetime module available in the Python standard library.

%package -n python2-%{{name}}
Obsoletes: python-dateutil < %{{version}}
Provides: python-dateutil = %{{version}}
Summary: Extensions to the standard Python datetime module

%description -n python2-%{{name}}
The dateutil module provides powerful extensions to the
datetime module available in the Python standard library.

%package -n python3-%{{name}}
Summary: Extensions to the standard Python datetime module

%description -n python3-%{{name}}
The dateutil module provides powerful extensions to the
datetime module available in the Python standard library.

%prep
%autosetup -n python-%{{unmangled_name}}-%{{unmangled_version}}

%build
%py2_build
%py3_build

%install
%py2_install
%py3_install
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python2-%{{name}}
%license LICENSE
%{{python2_sitelib}}/dateutil/
%{{python2_sitelib}}/python_dateutil*.egg-info

%files -n python3-%{{name}}
%license LICENSE
%{{python3_sitelib}}/dateutil/
%{{python3_sitelib}}/python_dateutil*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
