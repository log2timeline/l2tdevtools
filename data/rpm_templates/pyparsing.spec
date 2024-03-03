%define name pyparsing
%define version {version}
%define release 1

Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
License: MIT License
Summary: Python parsing module
Url: https://github.com/pyparsing/pyparsing/
Vendor: Paul McGuire <ptmcg.gm+pyparsing@gmail.com>
Source0: %{{name}}-%{{version}}.tar.gz
BuildArch: noarch
BuildRequires: python3-devel, python3-flit-core, python3-setuptools

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
%autosetup -p1 -n %{{name}}-%{{version}}

# This will try to include project.optional-dependencies
# %generate_buildrequires
# %pyproject_buildrequires -t

%build
%pyproject_wheel

%install
%pyproject_install

%files -n python3-%{{name}}
%license LICENSE
%doc CHANGES README.rst
%{{python3_sitelib}}/pyparsing
%{{python3_sitelib}}/pyparsing*.dist-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
