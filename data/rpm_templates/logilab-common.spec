%define name logilab-common
%define version 1.4.2
%define unmangled_name logilab-common
%define unmangled_version 1.4.2
%define release 1

Summary: collection of low-level Python packages and modules used by Logilab projects
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: LGPL
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Logilab <contact@logilab.fr>
Packager: Sylvain Thenault <sylvain.thenault@logilab.fr>
Provides: logilab.common
Url: http://www.logilab.org/project/logilab-common
BuildRequires: python2-setuptools, python2-devel, python3-setuptools, python3-devel

%description
This package contains some modules used by differents
Logilab's projects.

%package -n python2-%{{name}}
Obsoletes: python-%{{name}} < %{{version}}
Provides: python-%{{name}} = %{{version}}
Summary: collection of low-level Python packages and modules used by Logilab projects

%description -n python2-%{{name}}
This package contains some modules used by differents
Logilab's projects.

%package -n python3-%{{name}}
Summary: collection of low-level Python packages and modules used by Logilab projects

%description -n python3-%{{name}}
This package contains some modules used by differents
Logilab's projects.

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
%doc README
%{{python2_sitelib}}/logilab/common
%{{python2_sitelib}}/logilab_common*.egg-info
%{{python2_sitelib}}/logilab_common*.pth

%files -n python3-%{{name}}
%doc README
%{{python3_sitelib}}/logilab/common
%{{python3_sitelib}}/logilab_common*.egg-info
%{{python3_sitelib}}/logilab_common*.pth

%exclude %{{_bindir}}/*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
