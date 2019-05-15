%define name appdirs
%define version {version}
%define unmangled_name appdirs
%define unmangled_version {version}
%define release 1

Summary: A small Python module for determining appropriate platform-specific dirs, e.g. a "user data dir".
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Trent Mick; Sridhar Ratnakumar; Jeff Rouse <trentm@gmail.com; github@srid.name; jr@its.to>
Url: http://github.com/ActiveState/appdirs
BuildRequires: python2-setuptools, python2-devel, python3-setuptools, python3-devel

%description
A small Python module for determining appropriate
platform-specific dirs, e.g. a "user data dir".

%package -n python2-%{{name}}
Obsoletes: python-%{{name}} < %{{version}}
Provides: python-%{{name}} = %{{version}}
Summary: A small Python module for determining appropriate platform-specific dirs, e.g. a "user data dir".

%description -n python2-%{{name}}
A small Python module for determining appropriate
platform-specific dirs, e.g. a "user data dir".

%package -n python3-%{{name}}
Summary: A small Python module for determining appropriate platform-specific dirs, e.g. a "user data dir".

%description -n python3-%{{name}}
A small Python module for determining appropriate
platform-specific dirs, e.g. a "user data dir".

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

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
%license LICENSE.txt
%{{python2_sitelib}}/appdirs.py*
%{{python2_sitelib}}/appdirs*.egg-info

%files -n python3-%{{name}}
%license LICENSE.txt
%{{python3_sitelib}}/__pycache__/
%{{python3_sitelib}}/appdirs.py*
%{{python3_sitelib}}/appdirs*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
