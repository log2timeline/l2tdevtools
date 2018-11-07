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
BuildRequires: python2-setuptools, python2-devel, python3-setuptools, python3-devel

%description
Backport of the standard library typing module to Python versions older
than 3.5.

%package -n python2-%{{name}}
Obsoletes: python-typing < %{{version}}
Provides: python-typing = %{{version}}
Summary: Type Hints for Python

%description -n python2-%{{name}}
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
%doc CHANGES
%{{python2_sitelib}}/

%files -n python3-%{{name}}
%license LICENSE
%doc CHANGES
%{{python3_sitelib}}/

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
