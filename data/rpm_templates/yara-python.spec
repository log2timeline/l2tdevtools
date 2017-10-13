%define name yara-python
%define version {version}
%define unmangled_name yara-python
%define unmangled_version {version}
%define release 1

Summary: Python interface for YARA
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: Apache 2.0
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
Vendor: Victor M. Alvarez <plusvic@gmail.com;vmalvarez@virustotal.com>
Url: https://github.com/VirusTotal/yara-python
BuildRequires: python2-setuptools, python-devel, python3-setuptools, python3-devel

%description
This is a library for using YARA from Python. You can use
it to compile, save and load YARA rules, and to scan files or data strings.

%package -n python2-yara
Summary: Python interface for YARA

%description -n python2-yara
This is a library for using YARA from Python. You can use
it to compile, save and load YARA rules, and to scan files or data strings.

%package -n python3-yara
Summary: Python interface for YARA

%description -n python3-yara
This is a library for using YARA from Python. You can use
it to compile, save and load YARA rules, and to scan files or data strings.

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

%files -n python2-yara
%license LICENSE
%{{_libdir}}/python2*/site-packages/*.so
%{{_libdir}}/python2*/site-packages/yara_python*.egg-info

%files -n python3-yara
%license LICENSE
%{{_libdir}}/python3*/site-packages/*.so
%{{_libdir}}/python3*/site-packages/yara_python*.egg-info

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
