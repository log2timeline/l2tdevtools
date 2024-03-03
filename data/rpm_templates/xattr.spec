%define name xattr
%define version {version}
%define release 1

Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Summary: Python wrapper for extended filesystem attributes
License: MIT License
Vendor: Bob Ippolito <bob@redivi.com>
Url: http://github.com/xattr/xattr
Source0: %{{name}}-%{{version}}.tar.gz
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
BuildRequires: gcc, python3-cffi, python3-devel, python3-pip, python3-setuptools, python3-tox-current-env, python3-wheel

%description
Extended attributes extend the basic attributes of files
and directories in the file system. They are stored as name:data pairs
associated with file system objects (files, directories, symlinks, etc).
Extended attributes are currently only available on Darwin 8.0+
(Mac OS X 10.4) and Linux 2.6+. Experimental support is included for
Solaris and FreeBSD.

%package -n python3-%{{name}}
Summary: Python 3 module of Python wrapper for extended filesystem attributes

%description -n python3-%{{name}}
Extended attributes extend the basic attributes of files
and directories in the file system. They are stored as name:data pairs
associated with file system objects (files, directories, symlinks, etc).
Extended attributes are currently only available on Darwin 8.0+
(Mac OS X 10.4) and Linux 2.6+. Experimental support is included for
Solaris and FreeBSD.

%prep
%autosetup -p1 -n %{{name}}-%{{version}}

# The requirement versions are too recent for Fedora 39 but don't seem to
# the necessary minimum versions.
# %generate_buildrequires
# %pyproject_buildrequires -t

%build
%pyproject_wheel

%install
%pyproject_install
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/

%clean
rm -rf %{{buildroot}}

%files -n python3-%{{name}}
%license LICENSE.txt
%doc CHANGES.txt
%{{_libdir}}/python3*/site-packages/xattr
%{{_libdir}}/python3*/site-packages/xattr*.dist-info

%exclude %{{_bindir}}/xattr

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
