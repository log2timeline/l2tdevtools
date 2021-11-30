%define name opensearch-py
%define version {version}
%define unmangled_name opensearch-py
%define unmangled_version {version}
%define release 1

Summary: Python client for OpenSearch
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: opensearch-py-%{{unmangled_version}}.tar.gz
License: Apache License, Version 2.0
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/opensearch-py-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Honza Král <honza.kral@gmail.com>
Url: https://github.com/open/opensearch-py
BuildRequires: python3-setuptools, python3-devel

%description
Python client for OpenSearch.

%package -n python3-opensearch
Summary: Python client for OpenSearch
Requires: python3-certifi, python3-urllib3

%description -n python3-opensearch
Python client for OpenSearch.

%prep
%autosetup -n opensearch-py-%{{unmangled_version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-opensearch
%{{python3_sitelib}}/opensearchpy/
%{{python3_sitelib}}/opensearch_py*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
