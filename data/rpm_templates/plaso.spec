%define name plaso
%define version {version}
%define unmangled_name plaso
%define unmangled_version {version}
%define release 1

Summary: Super timeline all the things
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: Apache License, Version 2.0
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Log2Timeline maintainers <log2timeline-maintainers@googlegroups.com>
Packager: Log2Timeline maintainers <log2timeline-maintainers@googlegroups.com>
Url: https://github.com/log2timeline/plaso
BuildRequires: python2-setuptools

%description
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%package -n python-%{{name}}
Summary: Python 2 module of plaso (log2timeline)
Requires: PyYAML >= 3.10, libbde-python >= 20140531, libesedb-python >= 20150409, libevt-python >= 20120410, libevtx-python >= 20141112, libewf-python >= 20131210, libfsntfs-python >= 20151130, libfvde-python >= 20160719, libfwnt-python >= 20180117, libfwsi-python >= 20150606, liblnk-python >= 20150830, libmsiecf-python >= 20150314, libolecf-python >= 20151223, libqcow-python >= 20131204, libregf-python >= 20150315, libscca-python >= 20161031, libsigscan-python >= 20150627, libsmdev-python >= 20140529, libsmraw-python >= 20140612, libvhdi-python >= 20131210, libvmdk-python >= 20140421, libvshadow-python >= 20160109, libvslvm-python >= 20160109, python-XlsxWriter >= 0.9.3, python-artifacts >= 20170818, python2-backports-lzma, python-bencode, python-biplist >= 1.0.3, python-chardet >= 2.0.1, python-construct >= 2.5.2, python-crypto >= 2.6, python2-dateutil >= 1.5, python-dfdatetime >= 20180606, python-dfvfs >= 20180326, python-dfwinreg >= 20170521, python-dpkt >= 1.8, python-dtfabric >= 20180604, python-efilter >= 1.5, python-elasticsearch >= 6.0, python-elasticsearch5 >= 5.4.0, python-hachoir-core >= 1.3.3, python-hachoir-metadata >= 1.3.3, python-hachoir-parser >= 1.3.4, python2-lz4, python2-pefile >= 2018.8.8, python-psutil >= 5.4.3, python-pytsk3 >= 20160721, python-requests >= 2.2.1, python-six >= 1.1.0, python2-certifi >= 2016.9.26, python2-future >= 0.16.0, python2-idna >= 2.5, python2-pyparsing >= 2.0.3, python-pysqlite, python2-pytz, python2-urllib3 >= 1.7.1, python2-yara >= 3.4.0, python2-zmq >= 2.1.11, plaso-data

%description -n python-%{{name}}
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%package -n %{{name}}-data
Summary: Data files for plaso (log2timeline)

%description -n %{{name}}-data
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%package -n %{{name}}-tools
Summary: Tools of plaso (log2timeline)
Requires: python-%{{name}}

%description -n %{{name}}-tools
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
python2 setup.py build

%install
python2 setup.py install -O1 --root=%{{buildroot}}
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python-%{{name}}
%license LICENSE
%doc README
/usr/lib/python2*/site-packages/plaso/
/usr/lib/python2*/site-packages/plaso*.egg-info

%files -n %{{name}}-data
%{{_datadir}}/%{{name}}/*

%files -n %{{name}}-tools
%{{_bindir}}/*.py

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
