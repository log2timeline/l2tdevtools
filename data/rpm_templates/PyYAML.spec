%define name PyYAML
%define version {version}
%define unmangled_name PyYAML
%define unmangled_version {version}
%define release 1

Summary: YAML parser and emitter for Python
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
Vendor: Kirill Simonov <xi@resolvent.net>
Url: http://pyyaml.org/wiki/PyYAML
BuildRequires: python2-setuptools, python-devel, python3-setuptools, python3-devel

%description
Python-yaml is a complete YAML 1.1 parser and emitter
for Python. It can parse all examples from the specification. The parsing
algorithm is simple enough to be a reference for YAML parser implementors.
A simple extension API is also provided. The package is built using libyaml
for improved speed.

%package -n python3-%{{name}}
Summary: YAML parser and emitter for Python

%description -n python3-%{{name}}
Python-yaml is a complete YAML 1.1 parser and emitter
for Python. It can parse all examples from the specification. The parsing
algorithm is simple enough to be a reference for YAML parser implementors.
A simple extension API is also provided. The package is built using libyaml
for improved speed.

%global debug_package %{{nil}}

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
env CFLAGS="$RPM_OPT_FLAGS" python setup.py build

%install
python2 setup.py install -O1 --root=%{{buildroot}}
python3 setup.py install -O1 --root=%{{buildroot}}
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n %{{name}}
%license LICENSE
%doc CHANGES README
%{{_libdir}}/python2*/site-packages/yaml/
%{{_libdir}}/python2*/site-packages/PyYAML*.egg-info

%files -n python3-%{{name}}
%license LICENSE
%doc CHANGES README
%{{_libdir}}/python3*/site-packages/yaml/
%{{_libdir}}/python3*/site-packages/PyYAML*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
