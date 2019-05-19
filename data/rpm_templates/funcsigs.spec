%define name funcsigs
%define version {version}
%define unmangled_name funcsigs
%define unmangled_version {version}
%define release 1

Summary: Python function signatures from PEP362 for Python 2.6, 2.7 and 3.2+
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: ASL
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Testing Cabal <testing-in-python@lists.idyll.org>
Url: http://funcsigs.readthedocs.org
BuildRequires: python2-setuptools >= 17.0, python2-devel

%description
funcsigs is a backport of the PEP 362 function signature
features from Python 3.3's inspect module.

%package -n python2-%{{name}}
Obsoletes: python-%{{name}} < %{{version}}
Provides: python-%{{name}} = %{{version}}
Summary: Python function signatures from PEP362 for Python 2.6, 2.7 and 3.2+

%description -n python2-%{{name}}
funcsigs is a backport of the PEP 362 function signature
features from Python 3.3's inspect module.

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
%py2_build

%install
%py2_install
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python2-%{{name}}
%license LICENSE
%{{python2_sitelib}}/funcsigs
%{{python2_sitelib}}/funcsigs*.egg-info

%exclude %{{_bindir}}/*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
