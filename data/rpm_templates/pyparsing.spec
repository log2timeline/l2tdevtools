%define name pyparsing
%define version {version}
%define release 1

Summary: Python parsing module
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{version}}.tar.gz
License: MIT License
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Paul McGuire <ptmcg.gm+pyparsing@gmail.com>
Url: https://github.com/pyparsing/pyparsing/
BuildRequires: python3-devel, python3-setuptools

%description
The parsing module is an alternative approach to creating
and executing simple grammars, vs. the traditional lex/yacc approach,
or the use of regular expressions. The parsing module provides a library
of classes that client code uses to construct the grammar directly
in Python code.

%package -n python3-%{{name}}
Summary: Python 3 module of Python parsing module

%description -n python3-%{{name}}
The parsing module is an alternative approach to creating
and executing simple grammars, vs. the traditional lex/yacc approach,
or the use of regular expressions. The parsing module provides a library
of classes that client code uses to construct the grammar directly
in Python code.

%prep
%autosetup -n %{{name}}-%{{version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/lib/python*/site-packages/*.egg-info/requires.txt
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-%{{name}}
%license LICENSE
%doc CHANGES README.rst
%{{python3_sitelib}}/pyparsing
%{{python3_sitelib}}/pyparsing*.egg-info

%exclude %{{python3_sitelib}}/__pycache__/

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
