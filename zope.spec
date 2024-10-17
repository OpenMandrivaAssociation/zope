%define name    zope 
%define version 2.11.6
%define release %mkrel 2

%define python          %{_bindir}/python2.4
%define python_sitearch %(%{python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")
%define zope_home       %{_prefix}/lib/zope
%define software_home   %{zope_home}/lib/python
%define instances_base  %{_localstatedir}/lib/zope
%define instance_home   %{instances_base}/default
%define client_home     %{instance_home}/data
%define runzope         %{instance_home}/bin/runzope
%define state_home      %{_localstatedir}/run/zope
%define log_home        %{_localstatedir}/log/zope
%define config_file     %{_sysconfdir}/zope.conf
%define zopectl         %{_bindir}/zopectl

Name:           %{name}
Version:        %{version}
Release:        %{release}
Summary:        A leading open source application server
License:        Zope Public License (ZPL)
Group:          System/Servers
URL:            https://www.zope.org/
Source0:        http://zope.org/Products/Zope/%{version}/Zope-%{version}-final.tgz
Source2:        http://www.zope.org/Members/michel/ZB/ZopeBook.tar.bz2
Patch0:         zope-2.11.2-skel.patch
Requires:       poppler
Requires:       python2.4
Requires:       python2.4-libxml2
BuildRequires:  python2.4-devel
Epoch:          1
BuildRoot:      %{_tmppath}/%{name}-%{version}


%description
Zope is an open source application server for building content
managements, intranets, portals, and custom applications. The Zope
community consists of hundreds of companies and thousands of
developers all over the world, working on building the platform and
Zope applications. Zope is written in Python, a highly-productive,
object-oriented scripting language.

%package doc
Summary:    Documentation for the Zope application server
Group:      Networking/WWW
Obsoletes:  %{name}-docs

%description doc
Documentation for the Z Object Programming Environment (Zope), a free,
Open Source Python-based application server for building
high-performance, dynamic web sites, using a powerful and simple
scripting object model and high-performance, integrated object
database.

%prep
%setup -q -n Zope-%{version}-final
%patch0 -p1
chmod 644 doc/*.txt

# Add skel
chmod 644 skel/import/README.txt
rm -f skel/bin/runzope.bat.in \
      skel/bin/zopeservice.py.in
rm -rf skel/var
mkdir -p skel/run skel/data skel/var/pts

%build
./configure \
  --with-python="%{python}" \
  --prefix="%{buildroot}%{zope_home}" \
  --no-compile
make

# process the skel directory into the buildroot
%{python} << EOF
import py_compile, os
files = os.popen("find lib -name '*.py'").readlines()
for file in files:
    file = file.strip()
    py_compile.compile(file, file+"o", "%{zope_home}/"+file)
    py_compile.compile(file, file+"c", "%{zope_home}/"+file)
EOF

## Clean sources
find lib/python -type f -and \( -name 'Setup' -or -name '.cvsignore' \) \
    -exec rm -f \{\} \;
find -name "Win32" -print0 | xargs -0 rm -rf
find -name '*.bat$' -print0 | xargs -0 rm -f

%install
rm -rf %{buildroot}
%{python} "utilities/copyzopeskel.py" \
         --sourcedir="skel" \
         --targetdir="%{buildroot}%{instance_home}" \
         --replace="INSTANCE_HOME:%{instance_home}" \
         --replace="INSTANCES_BASE:%{instances_base}" \
         --replace="CLIENT_HOME:%{client_home}" \
         --replace="STATE_DIR:%{state_home}" \
         --replace="LOG_DIR:%{log_home}" \
         --replace="SOFTWARE_HOME:%{software_home}" \
         --replace="ZOPE_HOME:%{zope_home}" \
         --replace="CONFIG_FILE:%{config_file}" \
         --replace="PYTHON:%{python}" \
         --replace="ZOPECTL:%{zopectl}" \
         --replace="RUNZOPE:%{runzope}" \
         --replace="ZOPE_USER:zope"

make install
mkdir -p %{buildroot}%{instances_base}/log

# manage documentation manually
install -d -m 755 %{buildroot}%{_docdir}/%{name}
tar xjf %{SOURCE2} -C %{buildroot}%{_docdir}/%{name}
cp -pr doc/* %{buildroot}%{_docdir}/%{name}
cat > %{buildroot}%{_docdir}/%{name}/README.install.urpmi <<EOF
A Zope instance has been installed.  Run it via "/etc/rc.d/init.d/zope start".
Log in via a browser on port 9080.
You can add an administrative user when zope is stopped with the
command "zopectl adduser admin admin_passwd".
EOF

# write zope.pth
install -d %{buildroot}%{python_sitearch}
echo "%{software_home}" > \
    "%{buildroot}%{python_sitearch}/zope.pth"

# Compile .pyc
%{python} -c "import compileall; \
    compileall.compile_dir(\"%{buildroot}%{zope_home}\", \
    ddir=\"%{zope_home}\", force=1)"

mkdir -p %{buildroot}%{_bindir} \
    %{buildroot}%{_sysconfdir}/sysconfig \
    %{buildroot}%{_sysconfdir}/logrotate.d \
    %{buildroot}%{_initrddir}

cat > %{buildroot}/%{_bindir}/zopectl <<EOF
. %{_sysconfdir}/sysconfig/zope
for instance in \$ZOPE_INSTANCES; do
    \$instance/bin/zopectl "\$@"
done
EOF
chmod 744 %{buildroot}/%{_bindir}/zopectl
cat > %{buildroot}%{_sysconfdir}/sysconfig/zope <<EOF
#!/bin/sh
# List here your zope instances, space separated
# (e.g. ZOPE_INSTANCES="/var/lib/zope/default /var/lib/zope/other")
# This file it's used by the global %{_bindir}/zopectl
ZOPE_INSTANCES="%{instance_home}"
EOF

cp -p %{buildroot}%{instance_home}/etc/logrotate.d/zope \
    %{buildroot}%{_sysconfdir}/logrotate.d/

cp -p %{buildroot}%{instance_home}/etc/rc.d/init.d/zope \
    %{buildroot}%{_initrddir}/
chmod 744 %{buildroot}%{_initrddir}/*

rm -rf %{buildroot}%{instance_home}/etc/logrotate.d \
       %{buildroot}%{zope_home}/etc/logrotate.d \
       %{buildroot}%{instance_home}/etc/rc.d \
       %{buildroot}%{zope_home}/etc/rc.d

# fix permissions
find %{buildroot}%{zope_home} -type f \
    \( \
    -name '*.txt' \
    -o -name '*.jpg' \
    -o -name '*.gif' \
    -o -name '*.*tml' \
    \) \
    -print0 | xargs -0 chmod 644 || :
find %{buildroot}%{instance_home} -type f \
    \( \
    -name '*.txt' \
    -o -name '*.jpg' \
    -o -name '*.gif' \
    -o -name '*.*tml' \
    \) \
    -print0 | xargs -0 chmod 644 || :

%clean
rm -rf %{buildroot}

%pre
%_pre_useradd zope %{instance_home} /bin/false

%post
%_post_service zope
/sbin/chkconfig --add zope

%preun
%_preun_service zope

%postun
%_postun_userdel zope

%files
%defattr(-,root,root)
%dir %{_docdir}/%{name}
%{_docdir}/%{name}/README.install.urpmi
%{zope_home}
%{_bindir}/zopectl
%{_initrddir}/zope
%config(noreplace) %{_sysconfdir}/logrotate.d/zope
%config(noreplace) %{_sysconfdir}/sysconfig/zope
%{python_sitearch}/zope.pth

%attr(-,zope,zope) %dir %{instances_base}
%attr(-,zope,zope) %dir %{instance_home}
%attr(-,root,zope) %config(noreplace) %{instance_home}/bin
%attr(-,root,zope) %config(noreplace) %{instance_home}/etc
%attr(-,zope,zope) %config(noreplace) %{instance_home}/data
%attr(-,zope,zope) %config(noreplace) %{instance_home}/Extensions
%attr(-,zope,zope) %config(noreplace) %{instance_home}/import
%attr(-,zope,zope) %config(noreplace) %{instance_home}/lib
%attr(-,zope,zope) %config(noreplace) %{instance_home}/log
%attr(-,zope,zope) %config(noreplace) %{instance_home}/Products
%attr(-,zope,zope) %config(noreplace) %{instance_home}/run
%attr(-,zope,zope) %config(noreplace) %{instance_home}/var
%attr(-,root,zope) %config(noreplace) %{instance_home}/README.txt

%files doc
%defattr(-,root,root)
%{_docdir}/%{name}/*
%exclude %{_docdir}/%{name}/README.install.urpmi

