%define name xattr
%define version {version}
%define release 1

Summary: Python wrapper for extended filesystem attributes
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{version}}.tar.gz
License: MIT License
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
Vendor: Bob Ippolito <bob@redivi.com>
Url: http://github.com/xattr/xattr
BuildRequires: gcc, python3-devel, python3-setuptools, python3-cffi

%description
Extended attributes extend the basic attributes of files
and directories in the file system. They are stored as name:data pairs
associated with file system objects (files, directories, symlinks, etc).
Extended attributes are currently only available on Darwin 8.0+
(Mac OS X 10.4) and Linux 2.6+. Experimental support is included for
Solaris and FreeBSD.

%package -n python3-py%{{name}}
Summary: Python 3 module of Python wrapper for extended filesystem attributes

%description -n python3-py%{{name}}
Extended attributes extend the basic attributes of files
and directories in the file system. They are stored as name:data pairs
associated with file system objects (files, directories, symlinks, etc).
Extended attributes are currently only available on Darwin 8.0+
(Mac OS X 10.4) and Linux 2.6+. Experimental support is included for
Solaris and FreeBSD.

%prep
%autosetup -n %{{name}}-%{{version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-py%{{name}}
%license LICENSE.txt
%doc CHANGES.txt
%{{_libdir}}/python3*/site-packages/xattr
%{{_libdir}}/python3*/site-packages/xattr*.egg-info

%exclude %{{_bindir}}/xattr

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
