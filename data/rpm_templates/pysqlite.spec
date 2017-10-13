%define name pysqlite
%define version {version}
%define unmangled_name pysqlite
%define unmangled_version {version}
%define release 1

Summary: DB-API 2.0 interface for SQLite 3.x
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
License: zlib/libpng license
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
Vendor: Gerhard Haering <gh@ghaering.de>
Url: http://github.com/ghaering/pysqlite
BuildRequires: python2-setuptools, python-devel, sqlite-devel

%description
pysqlite is a DB-API 2.0-compliant database interface
for SQLite.

%package -n python-%{{name}}
Summary: DB-API 2.0 interface for SQLite 3.x

%description -n python-%{{name}}
pysqlite is a DB-API 2.0-compliant database interface
for SQLite.

%prep
%autosetup -n %{{unmangled_name}}-%{{unmangled_version}}

%build
env CFLAGS="$RPM_OPT_FLAGS" python setup.py build

%install
python2 setup.py install -O1 --root=%{{buildroot}}
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python-%{{name}}
%license LICENSE
%{{_libdir}}/python2*/site-packages/pysqlite2/
%{{_libdir}}/python2*/site-packages/pysqlite*.egg-info

%exclude %{{_libdir}}/python2*/site-packages/pysqlite2/test/
%exclude /usr/pysqlite2-doc/

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
