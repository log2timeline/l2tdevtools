%define name pytest-runner
%define version {version}
%define unmangled_name pytest-runner
%define unmangled_version {version}
%define release 1

Summary: Invoke py.test as distutils command with dependency resolution
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Jason R. Coombs <jaraco@jaraco.com>
Url: https://github.com/pytest-dev/pytest-runner
BuildRequires: python3-setuptools >= 30.3, python3-devel, python3-setuptools_scm

%description
Setup scripts can use pytest-runner to add setup.py test
support for pytest runner.

%package -n python3-%{{name}}
Summary: Invoke py.test as distutils command with dependency resolution

%description -n python3-%{{name}}
Setup scripts can use pytest-runner to add setup.py test
support for pytest runner.

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
%license LICENSE
%{{python3_sitelib}}/*.py
%{{python3_sitelib}}/__pycache__/*.pyc
%{{python3_sitelib}}/pytest_runner*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
