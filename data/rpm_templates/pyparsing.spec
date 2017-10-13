%define name pyparsing
%define version {version}
%define unmangled_name pyparsing
%define unmangled_version {version}
%define release 1

Summary: Python parsing module
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: MIT License
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Paul McGuire <ptmcg@users.sourceforge.net>
Url: http://pyparsing.wikispaces.com/
BuildRequires: python2-setuptools, python3-setuptools

%description
The parsing module is an alternative approach to creating
and executing simple grammars, vs. the traditional lex/yacc approach,
or the use of regular expressions. The parsing module provides a library
of classes that client code uses to construct the grammar directly
in Python code.

%package -n python2-%{{name}}
Summary: Python parsing module

%description -n python2-%{{name}}
The parsing module is an alternative approach to creating
and executing simple grammars, vs. the traditional lex/yacc approach,
or the use of regular expressions. The parsing module provides a library
of classes that client code uses to construct the grammar directly
in Python code.

%package -n python3-%{{name}}
Summary: Python parsing module

%description -n python3-%{{name}}
The parsing module is an alternative approach to creating
and executing simple grammars, vs. the traditional lex/yacc approach,
or the use of regular expressions. The parsing module provides a library
of classes that client code uses to construct the grammar directly
in Python code.

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

%files -n python2-%{{name}}
%license LICENSE
%doc CHANGES README
/usr/lib/python2*/site-packages/pyparsing.*
/usr/lib/python2*/site-packages/pyparsing*.egg-info

%files -n python3-%{{name}}
%license LICENSE
%doc CHANGES README
/usr/lib/python3*/site-packages/pyparsing.*
/usr/lib/python3*/site-packages/__pycache__/
/usr/lib/python3*/site-packages/pyparsing*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
