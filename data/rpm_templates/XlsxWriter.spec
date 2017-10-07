%define name XlsxWriter
%define version {version}
%define unmangled_name XlsxWriter
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
BuildRequires: python2-setuptools, python3-setuptools

%description
XlsxWriter is a Python module for writing files in the Excel
2007+ XLSX file format. XlsxWriter can be used to write text, numbers,
formulas and hyperlinks to multiple worksheets and it supports features
such as formatting and many more.

%package -n python-%{{name}}
Summary: A Python module for creating Excel XLSX files.

%description -n python-%{{name}}
XlsxWriter is a Python module for writing files in the Excel
2007+ XLSX file format. XlsxWriter can be used to write text, numbers,
formulas and hyperlinks to multiple worksheets and it supports features
such as formatting and many more.

%package -n python3-%{{name}}
Summary: A Python module for creating Excel XLSX files.

%description -n python3-%{{name}}
XlsxWriter is a Python module for writing files in the Excel
2007+ XLSX file format. XlsxWriter can be used to write text, numbers,
formulas and hyperlinks to multiple worksheets and it supports features
such as formatting and many more.

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

%files -n python-%{{name}}
%license LICENSE.txt
/usr/lib/python2*/site-packages/xlsxwriter/
/usr/lib/python2*/site-packages/XlsxWriter*.egg-info

%files -n python3-%{{name}}
%license LICENSE.txt
/usr/lib/python3*/site-packages/xlsxwriter/
/usr/lib/python3*/site-packages/XlsxWriter*.egg-info

%exclude %{{_bindir}}/*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated

