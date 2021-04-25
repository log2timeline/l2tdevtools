%define name elasticsearch-py
%define version {version}
%define unmangled_name elasticsearch-py
%define unmangled_version {version}
%define release 1

Summary: Python client for Elasticsearch
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: elasticsearch-%{{unmangled_version}}.tar.gz
License: Apache License, Version 2.0
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/elasticsearch-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Honza Král <honza.kral@gmail.com>
Url: https://github.com/elastic/elasticsearch-py
BuildRequires: python3-setuptools, python3-devel

%description
Python client for Elasticsearch.

%package -n python3-elasticsearch
Summary: Python client for Elasticsearch
Requires: python3-urllib3

%description -n python3-elasticsearch
Python client for Elasticsearch.

%prep
%autosetup -n elasticsearch-%{{unmangled_version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-elasticsearch
%{{python3_sitelib}}/elasticsearch/
%{{python3_sitelib}}/elasticsearch*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
