%define name bencode
%define version {version}
%define unmangled_name bencode.py
%define unmangled_version {version}
%define release 1

Summary: Simple bencode parser
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: BitTorrent Open Source License
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Dean Gardiner <me@dgardiner.net>
Url: https://github.com/fuzeman/bencode.py
BuildRequires: python3-setuptools >= 17.0 , python3-devel, python3-pbr

%description
Simple bencode parser, forked from the bencode package
by Thomas Rampelberg.

%package -n python3-%{{name}}
Summary: Simple bencode parser for Python 3

%description -n python3-%{{name}}
Simple bencode parser, forked from the bencode package
by Thomas Rampelberg.

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
%{{python3_sitelib}}/bencode/
%{{python3_sitelib}}/bencode.py*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
