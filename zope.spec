%define name    zope 
%define version 2.9.8
%define release %mkrel 1

Name:           %{name}
Version:        %{version}
Release:        %{release}
Summary:        A leading open source application server
License:        Zope Public License (ZPL)
Group:          System/Servers
URL:            http://www.zope.org/
Source0:        http://zope.org/Products/Zope/%{version}/Zope-%{version}-final.tgz
Source1:        skel.tar.bz2
Source2:        http://www.zope.org/Members/michel/ZB/ZopeBook.tar.bz2
Requires:       python2.4
Requires:	    python2.4-libxml2
Requires:	    xpdf-tools
BuildRequires:  python2.4-devel
Epoch:          1
BuildRoot:      %{_tmppath}/%{name}-%{version}

%define python /usr/bin/python2.4
%define zopehome /usr/lib/zope
%define softwarehome %{zopehome}/lib/python
%define instancehome /var/lib/zope
%define clienthome %{instancehome}/data
%define statehome /var/run/zope
%define loghome /var/log/zope
%define configfile /etc/zope.conf
%define zopectl /usr/bin/zopectl
%define runzope /usr/bin/runzope
%define zopeuser zope

%description
Zope is an open source application server for building content managements,
intranets, portals, and custom applications. The Zope community consists of
hundreds of companies and thousands of developers all over the world, working
on building the platform and Zope applications. Zope is written in Python, a
highly-productive, object-oriented scripting language.

%package doc
Summary:    Documentation for the Zope application server
Group:      Networking/WWW
Obsoletes:  %{name}-docs

%description doc
Documentation for the Z Object Programming Environment (Zope), a free, Open
Source Python-based application server for building high-performance, dynamic
web sites, using a powerful and simple scripting object model and
high-performance, integrated object database.

%prep
%setup -q -n Zope-%{version}-final
chmod 644 doc/*.txt

# Add skel
mv skel skel.bak
tar xvjf %{SOURCE1}
mv skel.bak/import/* skel/var/lib/zope/import/
#rm skel/var/log/zope/README.txt skel/var/run/zope/README.txt

# drop file which should not be there
rm -rf lib/python/Products/BTreeFolder2

%build
./configure \
  --with-python="%{python}" \
  --prefix="%{buildroot}%{zopehome}" \
  --no-compile
make

# process the skel directory into the buildroot
%{python} << EOF
import py_compile, os
files = os.popen("find lib -name '*.py'").readlines()
for file in files:
    file = file.strip()
    py_compile.compile(file, file+"o", "%{zopehome}/"+file)
    py_compile.compile(file, file+"c", "%{zopehome}/"+file)
EOF

## Clean sources
#find -type d -name "tests" | xargs rm -rf
find lib/python -type f -and \( -name 'Setup' -or -name '.cvsignore' \) \
    -exec rm -f \{\} \;
#find -type f -and \( -name '*.c' -or -name '*.h' -or -name 'Makefile*' \) \
#    -exec rm -f \{\} \;
find -name "Win32" | xargs rm -rf
rm -f ZServer/medusa/monitor_client_win32.py

# Has a bogus #!/usr/local/bin/python1.4 that confuses RPM
rm -f ZServer/medusa/test/asyn_http_bench.py


%install
rm -rf %{buildroot}
%{python} "utilities/copyzopeskel.py" \
         --sourcedir="skel" \
         --targetdir="%{buildroot}" \
         --replace="INSTANCE_HOME:%{instancehome}" \
         --replace="CLIENT_HOME:%{clienthome}" \
         --replace="STATE_DIR:%{statehome}" \
         --replace="LOG_DIR:%{loghome}" \
         --replace="SOFTWARE_HOME:%{softwarehome}" \
         --replace="ZOPE_HOME:%{zopehome}" \
         --replace="CONFIG_FILE:%{configfile}" \
         --replace="PYTHON:%{python}" \
         --replace="ZOPECTL:%{zopectl}" \
         --replace="RUNZOPE:%{runzope}"

#perl -pi -e "s|data_dir\s+=\s+.*?join\(INSTANCE_HOME, 'var'\)|data_dir=INSTANCE_HOME|" lib/python/Globals.py

make install

# will conflict with  zope-BTreeFolder2
rm -rf %{buildroot}/%{softwarehome}/Products/BTreeFolder2

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

%clean
rm -rf %{buildroot}

%pre
%_pre_useradd zope /var/lib/zope /bin/false

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
%{zopehome}

%{_bindir}/runzope
%{_bindir}/zopectl
%{_initrddir}/zope
%config(noreplace) %{_sysconfdir}/zope.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/zope

%attr(-,zope,zope) %config(noreplace) %verify(not md5 size mtime) %{instancehome}
%attr(-,zope,zope) /var/log/zope
%attr(-,zope,zope) /var/run/zope

%files doc
%defattr(-,root,root)
%{_docdir}/%{name}/*
%exclude %{_docdir}/%{name}/README.install.urpmi
