%define name fakeredis
%define version {version}
%define release 1

Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Summary: A fake version of a redis-py
License: BSD-3-Clause
URL: https://github.com/cunla/fakeredis-py
Source: %{{name}}-%{{version}}.tar.gz
BuildArch: noarch
BuildRequires: python3-devel, python3-poetry-core, python3-tox-current-env

%description
Fake implementation of redis API (redis-py) for testing purposes

%package -n python3-%{{name}}
Summary: A fake version of a redis-py

%description -n python3-%{{name}}
Fake implementation of redis API (redis-py) for testing purposes

%prep
%autosetup -p1 -n %{{name}}-%{{version}}

%generate_buildrequires
%pyproject_buildrequires -t

%build
%pyproject_wheel

%install
%pyproject_install

%files -n python3-%{{name}}
%license LICENSE
%doc README.md
%{{python3_sitelib}}/fakeredis
%{{python3_sitelib}}/fakeredis*.dist-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
