%define name plaso
%define version {version}
%define unmangled_name plaso
%define unmangled_version {version}
%define release 1

Summary: Super timeline all the things.
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
BuildRequires: python2-setuptools, python2-devel, python3-setuptools, python3-devel

%description
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%package -n %{{name}}-data
Summary: Data files for plaso (log2timeline)

%description -n %{{name}}-data
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%package -n python2-%{{name}}
Obsoletes: python-plaso < %{{version}}
Provides: python-plaso = %{{version}}
Requires: plaso-data libbde-python2 >= 20140531 libesedb-python2 >= 20150409 libevt-python2 >= 20120410 libevtx-python2 >= 20141112 libewf-python2 >= 20131210 libfsapfs-python2 >= 20181205 libfsntfs-python2 >= 20151130 libfvde-python2 >= 20160719 libfwnt-python2 >= 20180117 libfwsi-python2 >= 20150606 liblnk-python2 >= 20150830 libmsiecf-python2 >= 20150314 libolecf-python2 >= 20151223 libqcow-python2 >= 20131204 libregf-python2 >= 20150315 libscca-python2 >= 20161031 libsigscan-python2 >= 20150627 libsmdev-python2 >= 20140529 libsmraw-python2 >= 20140612 libvhdi-python2 >= 20131210 libvmdk-python2 >= 20140421 libvshadow-python2 >= 20160109 libvslvm-python2 >= 20160109 python2-artifacts >= 20170818 python-biplist >= 1.0.3 python-chardet >= 2.0.1 python-elasticsearch >= 6.0 python-elasticsearch5 >= 5.4.0 python-psutil >= 5.4.3 python2-XlsxWriter >= 0.9.3 python2-backports-lzma python2-bencode python2-certifi >= 2016.9.26 python2-crypto >= 2.6 python2-dateutil >= 1.5 python2-dfdatetime >= 20180704 python2-dfvfs >= 20181209 python2-dfwinreg >= 20180712 python2-dtfabric >= 20181128 python2-future >= 0.16.0 python2-idna >= 2.5 python2-lz4 >= 0.10.0 python2-pefile >= 2018.8.8 python2-pyparsing >= 2.3.0 python2-pysqlite python2-pytsk3 >= 20160721 python2-pytz python2-pyyaml >= 3.10 python2-requests >= 2.18.0 python2-six >= 1.1.0 python2-urllib3 >= 1.21.1 python2-yara >= 3.4.0 python2-zmq >= 2.1.11
Summary: Python 2 module of plaso (log2timeline)

%description -n python2-%{{name}}
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%package -n python3-%{{name}}
Requires: plaso-data libbde-python3 >= 20140531 libesedb-python3 >= 20150409 libevt-python3 >= 20120410 libevtx-python3 >= 20141112 libewf-python3 >= 20131210 libfsapfs-python3 >= 20181205 libfsntfs-python3 >= 20151130 libfvde-python3 >= 20160719 libfwnt-python3 >= 20180117 libfwsi-python3 >= 20150606 liblnk-python3 >= 20150830 libmsiecf-python3 >= 20150314 libolecf-python3 >= 20151223 libqcow-python3 >= 20131204 libregf-python3 >= 20150315 libscca-python3 >= 20161031 libsigscan-python3 >= 20150627 libsmdev-python3 >= 20140529 libsmraw-python3 >= 20140612 libvhdi-python3 >= 20131210 libvmdk-python3 >= 20140421 libvshadow-python3 >= 20160109 libvslvm-python3 >= 20160109 python3-artifacts >= 20170818 python3-biplist >= 1.0.3 python3-chardet >= 2.0.1 python3-dfvfs >= 20181209 python3-dfwinreg >= 20180712 python3-elasticsearch >= 6.0 python3-elasticsearch5 >= 5.4.0 python3-psutil >= 5.4.3 python3-XlsxWriter >= 0.9.3 python3-bencode python3-certifi >= 2016.9.26 python3-crypto >= 2.6 python3-dateutil >= 1.5 python3-dfdatetime >= 20180704 python3-dtfabric >= 20181128 python3-future >= 0.16.0 python3-idna >= 2.5 python3-lz4 >= 0.10.0 python3-pefile >= 2018.8.8 python3-pyparsing >= 2.3.0 python3-pytsk3 >= 20160721 python3-pytz python3-pyyaml >= 3.10 python3-requests >= 2.18.0 python3-six >= 1.1.0 python3-urllib3 >= 1.21.1 python3-yara >= 3.4.0 python3-zmq >= 2.1.11
Summary: Python 3 module of plaso (log2timeline)

%description -n python3-%{{name}}
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%package -n %{{name}}-tools
Requires: python3-plaso
Summary: Tools for plaso (log2timeline)

%description -n %{{name}}-tools
Plaso (log2timeline) is a framework to create super timelines. Its purpose is to extract timestamps from various files found on typical computer systems and aggregate them.

%prep
%setup -n %{{name}}-%{{unmangled_version}}

%build
%py2_build
%py3_build

%install
%py2_install
%py3_install

%clean
rm -rf $RPM_BUILD_ROOT

%files -n %{{name}}-data
%defattr(644,root,root,755)
%license LICENSE
%doc ACKNOWLEDGEMENTS AUTHORS README
%{{_datadir}}/%{{name}}/*

%files -n python2-%{{name}}
%defattr(644,root,root,755)
%license LICENSE
%doc ACKNOWLEDGEMENTS AUTHORS README
%{{python2_sitelib}}/plaso/*.py
%{{python2_sitelib}}/plaso/*/*.py
%{{python2_sitelib}}/plaso/*/*.yaml
%{{python2_sitelib}}/plaso/*/*/*.py
%{{python2_sitelib}}/plaso/*/*/*.yaml
%{{python2_sitelib}}/plaso*.egg-info/*

%files -n python3-%{{name}}
%defattr(644,root,root,755)
%license LICENSE
%doc ACKNOWLEDGEMENTS AUTHORS README
%{{python3_sitelib}}/plaso/*.py
%{{python3_sitelib}}/plaso/*/*.py
%{{python3_sitelib}}/plaso/*/*.yaml
%{{python3_sitelib}}/plaso/*/*/*.py
%{{python3_sitelib}}/plaso/*/*/*.yaml
%{{python3_sitelib}}/plaso*.egg-info/*

%files -n %{{name}}-tools
%{{_bindir}}/*.py

%exclude %{{_prefix}}/share/doc/*
%exclude %{{python2_sitelib}}/plaso/*.pyc
%exclude %{{python2_sitelib}}/plaso/*.pyo
%exclude %{{python2_sitelib}}/plaso/*/*.pyc
%exclude %{{python2_sitelib}}/plaso/*/*.pyo
%exclude %{{python2_sitelib}}/plaso/*/*/*.pyc
%exclude %{{python2_sitelib}}/plaso/*/*/*.pyo
%exclude %{{python3_sitelib}}/plaso/__pycache__/*
%exclude %{{python3_sitelib}}/plaso/*/__pycache__/*
%exclude %{{python3_sitelib}}/plaso/*/*/__pycache__/*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
