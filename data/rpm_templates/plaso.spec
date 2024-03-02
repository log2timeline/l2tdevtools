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
Requires: plaso-data == %{{version}}, {rpm_requires}
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
mkdir -p %{{buildroot}}/usr/share/plaso/
mv %{{buildroot}}/usr/lib/python*/site-packages/plaso/data/* %{{buildroot}}/usr/share/plaso/
rmdir %{{buildroot}}/usr/lib/python*/site-packages/plaso/data
for FILENAME in %{{buildroot}}/usr/bin/*; do mv ${{FILENAME}} ${{FILENAME}}.py; done

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
