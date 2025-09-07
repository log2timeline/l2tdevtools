%define name XlsxWriter
%define version {version}
%define unmangled_name xlsxwriter
%define unmangled_version {version}
%define release 1

Summary: A Python module for creating Excel XLSX files.
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: BSD
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: John McNamara <jmcnamara@cpan.org>
Url: https://github.com/jmcnamara/XlsxWriter
BuildRequires: python3-setuptools, python3-devel

%description
XlsxWriter is a Python module for writing files in the Excel
2007+ XLSX file format. XlsxWriter can be used to write text, numbers,
formulas and hyperlinks to multiple worksheets and it supports features
such as formatting and many more.

%package -n python3-%{{unmangled_name}}
Summary: A Python module for creating Excel XLSX files.

%description -n python3-%{{unmangled_name}}
XlsxWriter is a Python module for writing files in the Excel
2007+ XLSX file format. XlsxWriter can be used to write text, numbers,
formulas and hyperlinks to multiple worksheets and it supports features
such as formatting and many more.

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/lib/python*/site-packages/*.egg-info/requires.txt
rm -rf %{{buildroot}}/usr/share/doc/%{{unmangled_name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-%{{unmangled_name}}
%license LICENSE.txt
%{{python3_sitelib}}/xlsxwriter/
%{{python3_sitelib}}/xlsxwriter*.egg-info

%exclude %{{_bindir}}/*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated

