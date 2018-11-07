%define name elasticsearch5-py
%define version {version}
%define unmangled_name elasticsearch5
%define unmangled_version {version}
%define release 1

Summary: Python client for Elasticsearch
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: Apache License, Version 2.0
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Honza Král <honza.kral@gmail.com>
Url: https://github.com/elastic/elasticsearch-py
BuildRequires: python2-setuptools, python2-devel, python3-setuptools, python3-devel

%description
Python client for Elasticsearch5.

%package -n python2-elasticsearch5
Obsoletes: python-elasticsearch5 < %{{version}}
Provides: python-elasticsearch5 = %{{version}}
Summary: Python client for Elasticsearch5
Requires: python2-urllib3

%description -n python2-elasticsearch5
Python client for Elasticsearch.

%package -n python3-elasticsearch5
Summary: Python client for Elasticsearch5
Requires: python3-urllib3

%description -n python3-elasticsearch5
Python client for Elasticsearch5.

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

%files -n python2-elasticsearch5
%{{python2_sitelib}}/elasticsearch5/
%{{python2_sitelib}}/elasticsearch5*.egg-info

%files -n python3-elasticsearch5
%{{python3_sitelib}}/elasticsearch5/
%{{python3_sitelib}}/elasticsearch5*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
