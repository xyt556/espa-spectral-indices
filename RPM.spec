
# This spec file can be used to build an RPM package for installation.
# **NOTE**
#     Version, Release, and tagname information should be updated for the
#     particular release to build an RPM for.

# ----------------------------------------------------------------------------
Name:		espa-spectral-indices
Version:	2.3.0
Release:	2%{?dist}
Summary:	ESPA Spectral Indices Software

Group:		ESPA
License:	Nasa Open Source Agreement
URL:		https://github.com/USGS-EROS/espa-spectral-indices.git

BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:	x86_64
Packager:	USGS EROS LSRD

BuildRequires:	espa-common
Requires:	espa-common >= 1.5.0


# ----------------------------------------------------------------------------
%description
Provides science application executables for generating spectral indice products.  This is a C implementation which is statically built.


# ----------------------------------------------------------------------------
# Specify the repository tag/branch to clone and build from
%define tagname dev_v2.3.0
# Specify the name of the directory to clone into
%define clonedname %{name}-%{tagname}


# ----------------------------------------------------------------------------
%prep
# We don't need to perform anything here


# ----------------------------------------------------------------------------
%build

# Start with a clean clone of the repo
rm -rf %{clonedname}
git clone --depth 1 --branch %{tagname} %{url} %{clonedname}
# Build the applications
cd %{clonedname}
make BUILD_STATIC=yes


# ----------------------------------------------------------------------------
%install
# Start with a clean installation location
rm -rf %{buildroot}
# Install the applications for a specific path
cd %{clonedname}
make install PREFIX=%{buildroot}/usr/local

# ----------------------------------------------------------------------------
%clean
# Cleanup our cloned repository
rm -rf %{clonedname}
# Cleanup our installation location
rm -rf %{buildroot}


# ----------------------------------------------------------------------------
%files
%defattr(-,root,root,-)
# All sub-directories are automatically included
/usr/local/bin/*
/usr/local/%{name}


# ----------------------------------------------------------------------------
%changelog
* Wed Dec 02 2015 Ronald D Dilley <rdilley@usgs.gov>
- Changed release number for a recompile against the product formatter for Dec 2015 release

* Wed Nov 04 2015 Ronald D Dilley <rdilley@usgs.gov>
- Build for Dec 2015 release
* Thu Sep 03 2015 Ronald D Dilley <rdilley@usgs.gov>
- Build for Oct 2015 release
* Fri Jun 26 2015 William D Howe <whowe@usgs.gov>
- Now using git hub and cleaned up comments
* Tue Apr 28 2015 Cory Turner <cbturner@usgs.gov>
- Rebuild for espa-common release 1.4.0
* Fri Jan 16 2015 Adam J Dosch <adosch@usgs.gov>
- Rebuild to 1.3.1 to make orrection for Landsat 4-7 QA band descriptions and fill value in ledaps-2.2.1/espa-common-1.3.1
* Mon Dec 22 2014 Adam J Dosch <adosch@usgs.gov>
- Rebuild to build against espa-common 1.3.0
* Wed Dec 10 2014 Adam J Dosch <adosch@usgs.gov>
- Rebuild to fix solar zenith and TOA sizes for December 2014 release
* Mon Dec 07 2014 Adam J Dosch <adosch@usgs.gov>
- Rebuild to capture changes to espa-common for December 2014 release
* Mon Nov 24 2014 Adam J Dosch <adosch@usgs.gov>
- Rebuild of 2.1.0 for Decemeber 2014 release
* Thu Aug 21 2014 Adam J Dosch <adosch@usgs.gov>
- Build for August 2014 release
- Adding svnrelease to go with the new subversion testing/releases structure vs. using tags
- Updated Release conditional macro to expand if exists, if non-exists must be broke?
* Fri Jul 18 2014 Adam J Dosch <adosch@usgs.gov>
- Merging RHEL5 and 6 changes together to maintain one spec file
* Wed Jun 11 2014 Adam J Dosch <adosch@usgs.gov>
- Rebuild for 2.0.0 release for July 2014 release
- Adding LZMALIB, LZMAINC, JBIGLIB, XML2LIB, XML2INC, ESPALIB and ESPAINC for build requirements for raw binary conversion
- Adding 'cotspath' macro for building and references that against all build env-vars
- Adding BuildRequires and Requires requirements for espa-common packages
* Wed Nov 13 2013 Adam J Dosch <adosch@usgs.gov>
- Rebuild of SI to fix versioning incrementation --- had to backout RPM and rebuild
  repo + reinstall across cluster.  Should be ok for production.  From 1.2.2 to 1.2.0
* Thu Nov 07 2013 Adam J Dosch <adosch@usgs.gov>
- Updating cots paths from /data/static-cots to /data/cots
* Wed Nov 06 2013 Adam J Dosch <adosch@usgs.gov>
- Rebuild for version 1.2.2 for November 2013 release
* Mon Jul 22 2013 Adam J Dosch <adosch@usgs.gov>
- Rebuild for version 1.1.2
* Mon Jun 24 2013 Adam J Dosch <adosch@usgs.gov>
- Removing ESPA PATH appending logic in %post.  Going to manage this outside of RPM.
* Tue Jun 18 2013 Adam J Dosch <adosch@usgs.gov>
- Rebuild for version 1.1.1
* Mon Jun 10 2013 Adam J Dosch <adosch@usgs.gov>
- Adding %{dist} macro for Distribution tagging on RPM
* Mon May 20 2013 Adam J Dosch <adosch@usgs.gov>
- Adding removal of codepath's for spec-ind to %clean section
* Fri May 16 2013 Adam J Dosch <adosch@usgs.gov>
- Total build make-over.  Building entire source tree checkout from svn and static build from .spec file.
* Mon Apr 29 2013 Adam J Dosch <adosch@usgs.gov>
- Updating development environment server check in %post to include SCP36. Not updating any build versions.
* Wed Apr 23 2013 Adam J Dosch <adosch@usgs.gov>
- Hacked together RPM to package spectral-indicies into RPM form.  TODO is to build entire set start-to-end.
