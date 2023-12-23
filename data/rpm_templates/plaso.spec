%define name plaso
%define version {version}
%define release 1

Summary: Plaso (log2timeline) - Super timeline all the things
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{version}}.tar.gz
License: Apache License, Version 2.0
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Log2Timeline maintainers <log2timeline-maintainers@googlegroups.com>
Packager: Log2Timeline maintainers <log2timeline-maintainers@googlegroups.com>
Url: https://github.com/log2timeline/plaso
BuildRequires: python3-devel, python3-setuptools

%description
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%package -n %{{name}}-data
Summary: Data files for Plaso (log2timeline).

%description -n %{{name}}-data
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%package -n python3-%{{name}}
Requires: plaso-data == %{{version}}, libbde-python3 >= 20220121, libcaes-python3 >= 20221127, libcreg-python3 >= 20200725, libesedb-python3 >= 20220806, libevt-python3 >= 20191104, libevtx-python3 >= 20220724, libewf-python3 >= 20131210, libfsapfs-python3 >= 20220709, libfsext-python3 >= 20220829, libfsfat-python3 >= 20220925, libfshfs-python3 >= 20220831, libfsntfs-python3 >= 20211229, libfsxfs-python3 >= 20220829, libfvde-python3 >= 20220121, libfwnt-python3 >= 20210717, libfwsi-python3 >= 20230710, liblnk-python3 >= 20230716, libluksde-python3 >= 20220121, libmodi-python3 >= 20210405, libmsiecf-python3 >= 20150314, libolecf-python3 >= 20151223, libphdi-python3 >= 20220228, libqcow-python3 >= 20201213, libregf-python3 >= 20201002, libscca-python3 >= 20190605, libsigscan-python3 >= 20230109, libsmdev-python3 >= 20140529, libsmraw-python3 >= 20140612, libvhdi-python3 >= 20201014, libvmdk-python3 >= 20140421, libvsapm-python3 >= 20230506, libvsgpt-python3 >= 20211115, libvshadow-python3 >= 20160109, libvslvm-python3 >= 20160109, python3-XlsxWriter >= 0.9.3, python3-acstore >= 20230519, python3-artifacts >= 20220219, python3-bencode, python3-certifi >= 2016.9.26, python3-cffi >= 1.9.1, python3-chardet >= 2.0.1, python3-cryptography >= 2.0.2, python3-dateutil >= 1.5, python3-defusedxml >= 0.5.0, python3-dfdatetime >= 20221112, python3-dfvfs >= 20230407, python3-dfwinreg >= 20211207, python3-dtfabric >= 20230518, python3-future >= 0.16.0, python3-idna >= 2.5, python3-lz4 >= 0.10.0, python3-opensearch, python3-pefile >= 2021.5.24, python3-psutil >= 5.4.3, python3-pyparsing >= 3.0.0, python3-pytsk3 >= 20210419, python3-pytz, python3-pyxattr >= 0.7.2, python3-pyyaml >= 3.10, python3-redis >= 3.4, python3-requests >= 2.18.0, python3-six >= 1.1.0, python3-urllib3 >= 1.21.1, python3-yara >= 3.4.0, python3-zmq >= 2.1.11, python3-zstd >= 1.3.0.2
Summary: Python 3 module of Plaso (log2timeline) - Super timeline all the things

%description -n python3-%{{name}}
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%package -n %{{name}}-tools
Requires: python3-plaso == %{{version}}
Summary: Tools for Plaso (log2timeline).

%description -n %{{name}}-tools
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%prep
%autosetup -n %{{name}}-%{{version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/lib/python*/site-packages/*.egg-info/requires.txt
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/
mv %{{buildroot}}/usr/lib/python*/site-packages/tools/ %{{buildroot}}/usr/bin
mkdir -p %{{buildroot}}/usr/share/plaso/
cp -rf data/* %{{buildroot}}/usr/share/plaso/

%clean
rm -rf %{{buildroot}}

%files -n %{{name}}-data
%license LICENSE
%doc ACKNOWLEDGEMENTS AUTHORS README
%{{_datadir}}/%{{name}}/*

%files -n python3-%{{name}}
%license LICENSE
%doc README
%{{python3_sitelib}}/plaso
%{{python3_sitelib}}/plaso*.egg-info

%files -n %{{name}}-tools
%{{_bindir}}/*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
