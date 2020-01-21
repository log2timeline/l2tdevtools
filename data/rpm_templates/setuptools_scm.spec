%define name setuptools_scm
%define version {version}
%define unmangled_name setuptools_scm
%define unmangled_version {version}
%define release 1

Summary: the blessed package to manage your versions by scm tags
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Ronny Pfannschmidt <opensource@ronnypfannschmidt.de>
Url: https://github.com/pypa/setuptools_scm/
BuildRequires: python3-setuptools >= 30.3, python3-devel

%description
setuptools_scm handles managing your python package versions
in scm metadata instead of declaring them as the version argument or in
a scm managed file

%package -n python3-%{{name}}
Summary: the blessed package to manage your versions by scm tags

%description -n python3-%{{name}}
setuptools_scm handles managing your python package versions
in scm metadata instead of declaring them as the version argument or in
a scm managed file

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
%{{python3_sitelib}}/setuptools_scm
%{{python3_sitelib}}/setuptools_scm*.egg-info

%exclude %{{_bindir}}/*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
