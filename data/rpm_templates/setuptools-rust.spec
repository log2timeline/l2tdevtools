%define name setuptools-rust
%define version 0.12.1
%define unmangled_version 0.12.1
%define unmangled_version 0.12.1
%define release 1

Summary: Setuptools Rust extension plugin
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{unmangled_version}}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{{_tmppath}}%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Nikolay Kim <fafhrd91@gmail.com>
Url: https://github.com/PyO3/setuptools-rust
BuildRequires: python3-devel, python3-setuptools, python3-setuptools_scm, python3-toml
Requires: python3-semantic_version, python3-setuptools

%description
setuptools-rust is a plugin for setuptools to build Rust Python extensions
implemented with PyO3 or rust-cpython.

%package -n python3-%{{name}}
Summary: Setuptools Rust extension plugin

%description -n python3-%{{name}}
setuptools-rust is a plugin for setuptools to build Rust Python extensions
implemented with PyO3 or rust-cpython.

%prep
%autosetup -n %{{name}}-%{{unmangled_version}}

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
%{{python3_sitelib}}/setuptools_rust
%{{python3_sitelib}}/setuptools_rust*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
