%define debug_package %{nil}

%define mybuildnumber %{?build_number}%{?!build_number:1}

Name:           borg-offsite-backup
Version:        0.1.13
Release:        %{mybuildnumber}%{?dist}
Summary:        A Borg backup helper that helps back up ZFS file systems as well as regular ones
BuildArch:      noarch

License:        GPLv3+
URL:            https://github.com/Rudd-O/%{name}
Source0:        https://github.com/Rudd-O/%{name}/archive/{%version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  make
Requires:       python3
Requires:       python3-dateutil
Requires:       time
Requires:       fuse
Requires:       borgbackup
Requires:       util-linux
Requires:       nmap-ncat

%description
This is a small helper program that uses a configuration file to
setup a Borg backup to a remote server.  It can help back up ZFS
file systems and volumes, and it can also run in a Qubes OS dom0.

%prep
%setup -q

%build
/bin/true

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT BINDIR=%{_bindir}

%files
%attr(0755, root, root) %{_bindir}/%{name}
%attr(0755, root, root) %{_bindir}/%{name}-helper
%doc README.md

%changelog
* Fri May 12 2023 Manuel Amador (Rudd-O) <rudd-o@rudd-o.com>
- First release
