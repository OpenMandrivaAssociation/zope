%define realVersion 2.9.6-final

%define version %(echo %{realVersion} | sed -e's/-/./g')
%define sVersion %(echo %{realVersion} | cut -d- -f1)


Summary:        A leading open source application server
Name:           zope
Version:        %{version}
Release:        %mkrel 2
License:        Zope Public License (ZPL)
Group:          System/Servers
URL:            http://www.zope.org/
Source0:        http://zope.org/Products/Zope/%{sVersion}/Zope-%{realVersion}.tar.bz2
Source1:        skel.tar.bz2
Source2:        http://www.zope.org/Members/michel/ZB/ZopeBook.tar.bz2
Source3:        README.install.urpmi.zope
Requires:       python >= 2.3.5
Requires:	python-libxml2
Requires:	xpdf-tools
BuildRequires:  python-devel >= 2.3.5
BuildRoot:      %{_tmppath}/%{name}-%{version}-root-%(id -u -n)
Epoch:          1

%define python /usr/bin/python
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

%prep
%setup -q -n Zope-%{realVersion}


# Add skel
mv skel skel.bak
tar xvjf %{SOURCE1}
mv skel.bak/import/* skel/var/lib/zope/import/
#rm skel/var/log/zope/README.txt skel/var/run/zope/README.txt

# Prepare doc (Zope Book)
tar xjf %{SOURCE2} 

# drop file which should not be there
rm -rf lib/python/Products/BTreeFolder2

%build
./configure \
  --with-python="%{python}" \
  --prefix="%{buildroot}%{zopehome}" \
  --no-compile
make

# process the skel directory into the buildroot
python << EOF
import py_compile, os
files = os.popen("find lib -name '*.py'").readlines()
for file in files:
    file = file.strip()
    py_compile.compile(file, file+"o", "%{zopehome}/"+file)
    py_compile.compile(file, file+"c", "%{zopehome}/"+file)
EOF

# XXX: next release...
#env CFLAGS="$RPM_OPT_FLAGS" /usr/bin/python setup.py build
#/usr/bin/python setup.py install --root=$RPM_BUILD_ROOT \
#    --record=INSTALLED_FILES

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

cp %{SOURCE3} README.install.urpmi

%install
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
rm -rf $RPM_BUILD_ROOT/%{softwarehome}/Products/BTreeFolder2

#rm -rf $RPM_BUILD_ROOT
#install -d $RPM_BUILD_ROOT{%{_bindir},%{_sbindir},%{_libdir}/zope/lib/python} \
#    $RPM_BUILD_ROOT{/etc/rc.d/init.d,/var/log,/var/lib/zope}
#
#cp -a lib/python/* $RPM_BUILD_ROOT%{_libdir}/zope/lib/python
#cp -a ZServer/ utilities/ import/ $RPM_BUILD_ROOT%{_libdir}/zope
#find $RPM_BUILD_ROOT%{_libdir}/zope -type f -name '*.py' -or -name '*.txt' \
#    | xargs -r rm -f
#cp -a ZServer/medusa/test/* $RPM_BUILD_ROOT%{_libdir}/zope/ZServer/medusa/test/
#
#install zpasswd.py $RPM_BUILD_ROOT%{_bindir}/zpasswd
#install z2.py $RPM_BUILD_ROOT%{_libdir}/zope
#install %{SOURCE8} $RPM_BUILD_ROOT%{_sbindir}/zope-zserver
#install %{SOURCE7} $RPM_BUILD_ROOT/etc/rc.d/init.d/zope
#install var/Data.fs $RPM_BUILD_ROOT/var/lib/zope/Data.fs
#
#touch $RPM_BUILD_ROOT/var/log/zope


%clean
rm -rf $RPM_BUILD_ROOT

%pre
%_pre_useradd zope /var/lib/zope /bin/false

%post
%_post_service zope
/sbin/chkconfig --add zope

# disable this feature : it creates problem during update and
# is confusing for somebody who don't care about installation message
# zope display a how to create an administrative user if it doesn't exit
# README.install.urpmi display the rest of the text

# # write a 10 digit random default admin password into acl_users
# passwd=`head -c4 /dev/urandom | od -tu4 -N4 | sed -ne '1s/.* //p'`
# %{zopectl} adduser admin $passwd
# # inform the user of the default username/password combo and port
# echo
# echo A Zope instance has been installed.  Run it via
# echo \"/etc/rc.d/init.d/zope start\".  Log in via a browser on port 9080.
# echo
# echo Zope has default administrative username/password combination.  The
# echo "administrative username is \"admin\" and the password is \"$passwd\"."
# echo Please remember this so you are able to log in for the first time.
# echo

%preun
%_preun_service zope

%postun
%_postun_userdel zope

%files
%defattr(0644,root,root,755)
%dir %{zopehome}
%{zopehome}/doc
%{zopehome}/lib
%{zopehome}/skel

%attr(755,root,root)/usr/bin/runzope
%attr(755,root,root)/usr/bin/zopectl
%attr(755,root,root) %{zopehome}/bin/*
%attr(755,root,root) %config(noreplace) /etc/rc.d/init.d/zope
%config(noreplace) /etc/zope.conf
%config(noreplace) /etc/logrotate.d/zope

%attr(770, %{zopeuser}, %{zopeuser}) %config(noreplace) %verify(not md5 size mtime) %{instancehome}
%attr(770, %{zopeuser}, %{zopeuser}) %dir /var/log/zope
%attr(755, %{zopeuser}, %{zopeuser}) %dir /var/run/zope

%doc README.install.urpmi

#%defattr(644,root,root,755)
#%config(noreplace) %attr(755,root,root) /etc/rc.d/init.d/zope
#%attr(755,root,root) %{_bindir}/*
#%attr(755,root,root) %{_sbindir}/*
#%{_libdir}/zope
#%attr(1771,root,zope) %dir /var/lib/zope
#%attr(660,root,zope) %config(noreplace) %verify(not md5 size mtime) /var/lib/zope/*
##%attr(640,root,root) %ghost /var/log/zope
#%ghost /var/log/zope


##############################################################################

%package docs
Summary:    Documentation for the Zope application server
Group:      Networking/WWW

%description docs
Documentation for the Z Object Programming Environment (Zope), a free, Open
Source Python-based application server for building high-performance, dynamic
web sites, using a powerful and simple scripting object model and
high-performance, integrated object database.

%files docs
%defattr(644, root, root, 755)
%doc ZopeBook doc


##############################################################################



