%define name setuptools
%define version {version}
%define unmangled_name setuptools
%define unmangled_version {version}
%define release 1

Summary: Easily download, build, install, upgrade, and uninstall Python packages
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.zip
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Python Packaging Authority <distutils-sig@python.org>
Url: https://github.com/pypa/setuptools
BuildRequires: python3-setuptools, python3-devel

%description
Easily download, build, install, upgrade, and uninstall
Python packages

%package -n python3-%{{name}}
Summary: Easily download, build, install, upgrade, and uninstall Python packages

%description -n python3-%{{name}}
Easily download, build, install, upgrade, and uninstall
Python packages

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-%{{name}}
%license LICENSE
%{{python3_sitelib}}/__pycache__/
%{{python3_sitelib}}/easy_install.py*
%{{python3_sitelib}}/pkg_resources
%{{python3_sitelib}}/setuptools
%{{python3_sitelib}}/setuptools*.egg-info

%exclude %{{_bindir}}/*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
