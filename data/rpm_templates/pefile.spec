%define name pefile
%define version {version}
%define release 1

Summary: Python PE parsing module
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{version}}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Ero Carrera <ero.carrera@gmail.com>
Url: https://github.com/erocarrera/pefile
BuildRequires: python3-setuptools

%description
Python module to read and work with Portable Executable
(aka PE) files. Most of the information in the PE Header is accessible, as
well as all the sections, section's information and data.

%package -n python3-%{{name}}
Summary: Python 3 module of Python PE parsing module

%description -n python3-%{{name}}
Python module to read and work with Portable Executable
(aka PE) files. Most of the information in the PE Header is accessible, as
well as all the sections, section's information and data.

%prep
%autosetup -n %{{name}}-%{{version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-%{{name}}
%license LICENSE
%doc README
%{{python3_sitelib}}/

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
