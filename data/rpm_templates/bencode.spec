Name: bencode
Version: {version}
Release: 1
Group: Development/Libraries
License: BitTorrent Open Source License
Summary: Simple bencode parser
Url: https://github.com/fuzeman/bencode.py
Vendor: Dean Gardiner <me@dgardiner.net>
Source0: bencode_py-%{{version}}.tar.gz
BuildArch: noarch
BuildRequires: python3-devel, pyproject-rpm-macros, python3-pip, python3-setuptools, python3-wheel

%{{?python_disable_dependency_generator}}

%description
Simple bencode parser, forked from the bencode package
by Thomas Rampelberg.

%package -n python3-%{{name}}
Summary: Python 3 module of Simple bencode parser

%description -n python3-%{{name}}
Simple bencode parser, forked from the bencode package
by Thomas Rampelberg.

%prep
%autosetup -p1 -n bencode_py-%{{version}}

%build
%pyproject_wheel

%install
%pyproject_install
%files -n python3-%{{name}}
%license LICENSE

%{{python3_sitelib}}/bencode
%{{python3_sitelib}}/bencodepy
%{{python3_sitelib}}/bencode_py*.dist-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
