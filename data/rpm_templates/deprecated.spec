%define name deprecated
%define version {version}
%define unmangled_name Deprecated
%define unmangled_version {version}
%define release 1

Summary: Python @deprecated decorator to deprecate old python classes, functions or methods.
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Laurent LAPORTE <tantale.solutions@gmail.com>
Url: https://github.com/tantale/deprecated
BuildRequires: python3-devel, python3-setuptools

%description
Mark a function or a method as deprecated.

%package -n python3-%{{name}}
Requires: python3-wrapt
Summary: Python 3 module of Python @deprecated decorator to deprecate old python classes, functions or methods.

%description -n python3-%{{name}}
Mark a function or a method as deprecated.

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/lib/python*/site-packages/*.egg-info/requires.txt
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-%{{name}}


%{{python3_sitelib}}/Deprecated
%{{python3_sitelib}}/Deprecated*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
