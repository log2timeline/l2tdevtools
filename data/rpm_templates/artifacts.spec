%define name artifacts
%define version {version}
%define release 1

Summary: ForensicArtifacts.com Artifact Repository.
Name: %{{name}}
Version: %{{version}}
Release: %{{release}}
Source0: %{{name}}-%{{version}}.tar.gz
License: Apache License, Version 2.0
Group: Development/Libraries
BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot
Prefix: %{{_prefix}}
BuildArch: noarch
Vendor: Forensic artifacts <forensicartifacts@googlegroups.com>
Packager: Forensic artifacts <forensicartifacts@googlegroups.com>
Url: https://github.com/ForensicArtifacts/artifacts
BuildRequires: python3-devel, python3-setuptools

%{{?python_disable_dependency_generator}}

%description
A free, community-sourced, machine-readable knowledge base of forensic artifacts that the world can use both as an information source and within other tools.

%package -n %{{name}}-data
Summary: Data files for ForensicArtifacts.com Artifact Repository.

%description -n %{{name}}-data
A free, community-sourced, machine-readable knowledge base of forensic artifacts that the world can use both as an information source and within other tools.

%package -n python3-%{{name}}
Requires: artifacts-data == %{{version}}, {rpm_requires}
Summary: Python 3 module of ForensicArtifacts.com Artifact Repository.

%description -n python3-%{{name}}
A free, community-sourced, machine-readable knowledge base of forensic artifacts that the world can use both as an information source and within other tools.

%package -n %{{name}}-tools
Requires: python3-artifacts >= %{{version}}
Summary: Tools for ForensicArtifacts.com Artifact Repository.

%description -n %{{name}}-tools
A free, community-sourced, machine-readable knowledge base of forensic artifacts that the world can use both as an information source and within other tools.

%prep
%autosetup -n %{{name}}-%{{version}}

%build
%py3_build

%install
%py3_install
rm -rf %{{buildroot}}/usr/lib/python*/site-packages/*.egg-info/requires.txt
rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/
mkdir -p %{{buildroot}}/usr/share/artifacts/
mv %{{buildroot}}/usr/lib/python*/site-packages/artifacts/data/* %{{buildroot}}/usr/share/artifacts/
rmdir %{{buildroot}}/usr/lib/python*/site-packages/artifacts/data
for FILENAME in %{{buildroot}}/usr/bin/*; do mv ${{FILENAME}} ${{FILENAME}}.py; done

%clean
rm -rf %{{buildroot}}

%files -n %{{name}}-data
%license LICENSE
%doc ACKNOWLEDGEMENTS AUTHORS README
%{{_datadir}}/%{{name}}/*

%files -n python3-%{{name}}
%license LICENSE
%doc README
%{{python3_sitelib}}/artifacts
%{{python3_sitelib}}/artifacts*.egg-info

%files -n %{{name}}-tools
%{{_bindir}}/*

%changelog
* {date_time} log2timeline development team <log2timeline-dev@googlegroups.com> {version}-1
- Auto-generated
