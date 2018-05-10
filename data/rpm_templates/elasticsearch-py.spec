%define name elasticsearch-py
%define version {version}
%define unmangled_name elasticsearch-py
%define unmangled_version {version}
%define release 1

Summary: Python client for Elasticsearch
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{unmangled_version}}.tar.gz
License: Apache License, Version 2.0
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Honza Král <honza.kral@gmail.com>
Url: https://github.com/elastic/elasticsearch-py
BuildRequires: python2-setuptools, python3-setuptools

%description
Python client for Elasticsearch.

%package -n python-elasticsearch
Summary: Python client for Elasticsearch
Requires: python-urllib3

%description -n python-elasticsearch
Python client for Elasticsearch.

%package -n python3-elasticsearch
Summary: Python client for Elasticsearch
Requires: python3-urllib3

%description -n python3-elasticsearch
Python client for Elasticsearch.

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

%files -n python-elasticsearch
/usr/lib/python2*/site-packages/elasticsearch/
/usr/lib/python2*/site-packages/elasticsearch*.egg-info

%files -n python3-elasticsearch
/usr/lib/python3*/site-packages/elasticsearch/
/usr/lib/python3*/site-packages/elasticsearch*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
