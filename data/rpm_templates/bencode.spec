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
BuildRequires: python2-setuptools >= 17.0 , python2-devel, python2-pbr, python3-setuptools >= 17.0 , python3-devel, python3-pbr

%description
Simple bencode parser, forked from the bencode package
by Thomas Rampelberg.

%package -n python2-%{{name}}
Obsoletes: python-bencode <= %{{version}}
Provides: python-bencode = %{{version}}
Summary: Simple bencode parser for Python 2

%description -n python2-%{{name}}
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
%py2_build
%py3_build

%install
%py2_install
%py3_install
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python2-%{{name}}
%{{python2_sitelib}}/bencode/
%{{python2_sitelib}}/bencode.py*.egg-info

%files -n python3-%{{name}}
%{{python3_sitelib}}/bencode/
%{{python3_sitelib}}/bencode.py*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
