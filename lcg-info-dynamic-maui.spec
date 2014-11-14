#
# RPM for lcg-info-dynamic-maui, a alternative version of
# lcg-info-dynamic-pbs, that handles properly MAUI standing
# reservations. This RPM advertizes feature lcg-info-dynamic-pbs and
# must be used as a replacement (both cannot be installed at the same time).
#
# Cedric Duprilot <duprilot@lal.in2p3.fr>
# Michel Jouvin <jouvin@lal.in2p3.fr>
#
#

# Be sure to define 'prodversion' and 'prodrelease' with --define
Summary: GIP plugin for MAUI
Name: lcg-info-dynamic-maui
Vendor: LAL
Version: %{prodversion}
Release: %{prodrelease}
License: http://www.apache.org/licenses
Group: System Environment/Daemons
Source: %{name}.tar.gz
BuildArch: noarch
BuildRoot: /var/tmp/%{name}-build
Packager: Cedric Duprilot <duprilot@lal.in2p3.fr>, Michel Jouvin <jouvin@lal.in2p3.fr>
Provides: lcg-info-dynamic-pbs
Requires: python-pbs
URL: http://svn.lal.in2p3.fr/LCG/QWG/LAL/GIP/maui

%description
Update LDIF static value for LCG CE based on Torque/MAUI status 

%prep
%setup

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/libexec
mkdir -p $RPM_BUILD_ROOT/usr/lib/python
cp $RPM_BUILD_DIR/%{name}-%{version}/lcg-info-dynamic-maui $RPM_BUILD_ROOT/usr/libexec
cp $RPM_BUILD_DIR/%{name}-%{version}/TorqueMauiConfParser.py $RPM_BUILD_ROOT/usr/lib/python
ls $RPM_BUILD_ROOT/usr/lib/python

%files
%defattr(-,root,root)
/usr/libexec/lcg-info-dynamic-maui
/usr/lib/python/TorqueMauiConfParser.py

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Fri Sep 28 2012 change dependency to python_pbs instead of pbs_python
* Fri Jul 27 2007 v2 rewrite by Michel Jouvin <jouvin@lal.in2p3.fr>
* Fri Jul 27 2007 Initial version by Cedric Duprilot <duprilot@lal.in2p3.fr>

--- end of ChangeLog ---
