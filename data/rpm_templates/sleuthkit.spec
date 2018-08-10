%define name sleuthkit
%define version {version}
%define unmangled_name sleuthkit
%define unmangled_version {version}
%define release 1

Summary: The Sleuth Kit (TSK)
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
License: CPL and IBM and GPLv2+
Source0: %{{unmangled_name}}-%{{unmangled_version}}.tar.gz
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-release-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
URL: http://www.sleuthkit.org
BuildRequires: gcc gcc-c++ sqlite-devel zlib-devel
Requires: sleuthkit-libs = %{{version}}-%{{release}} sqlite zlib

%description
The Sleuth Kit (TSK) is a collection of UNIX-based command line tools that
allow you to investigate a computer. The current focus of the tools is the
file and volume systems and TSK supports FAT, Ext2/3, NTFS, UFS,
and ISO 9660 file systems

%package -n sleuthkit-libs
Summary: Sleuth Kit shared library

%description -n sleuthkit-libs
The Sleuth Kit shared library

%package sleuhtkit-devel
Summary: Development files for the Sleuth Kit library
Requires: sleuthkit-libs = %{{version}}-%{{release}}

%description -n sleuthkit-devel
The %{{name}}-devel package contains libraries and header files for
developing applications that use %{{name}}.

%prep
%setup -q -n %{{name}}-%{{version}}

%build
%configure --prefix=/usr --libdir=%{{_libdir}} --mandir=%{{_mandir}} --disable-java --without-afflib --without-libewf --without-libvhdi --without-libvmdk
make %{{?_smp_mflags}}

%install
rm -rf %{{buildroot}}
%make_install

%clean
rm -rf %{{buildroot}}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files -n sleuthkit-libs
%license licenses/cpl1.0.txt licenses/IBM-LICENSE
%{{_libdir}}/*.so.*

%files -n sleuthkit-devel
%license licenses/cpl1.0.txt licenses/IBM-LICENSE
%{{_includedir}}/tsk/
%{{_libdir}}/*.so

%files -n sleuhtkit
%doc ChangeLog.txt NEWS.txt
%license licenses/*
%{{_bindir}}/*
%{{_mandir}}/man1/*
%dir %{{_datadir}}/tsk
%{{_datadir}}/tsk/sorter/

# fcat conflicts with freeze fcat
%exclude %{{_bindir}}/fcat
%exclude %{{_mandir}}/man1/fcat.1*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated

