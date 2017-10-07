%define name bencode
%define version {version}
%define unmangled_name bencode.py
%define unmangled_version {version}
%define release 1

Summary: Simple bencode parser (for Python 2, Python 3 and PyPy)
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
BuildRequires: python2-setuptools, python2-pbr, python3-setuptools, python3-pbr

%description
Simple bencode parser, forked from the bencode package
by Thomas Rampelberg.

%package -n python-%{{name}}
Summary: Simple bencode parser (for Python 2, Python 3 and PyPy)

%description -n python-%{{name}}
Simple bencode parser, forked from the bencode package
by Thomas Rampelberg.

%package -n python3-%{{name}}
Summary: Simple bencode parser (for Python 2, Python 3 and PyPy)

%description -n python3-%{{name}}
Simple bencode parser, forked from the bencode package
by Thomas Rampelberg.

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
python2 setup.py build
python3 setup.py build

%install
python2 setup.py install -O1 --root=%{{buildroot}}
python3 setup.py install -O1 --root=%{{buildroot}}
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python-%{{name}}
/usr/lib/python2*/site-packages/bencode/
/usr/lib/python2*/site-packages/bencode.py*.egg-info

%files -n python3-%{{name}}
/usr/lib/python3*/site-packages/bencode/
/usr/lib/python3*/site-packages/bencode.py*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
