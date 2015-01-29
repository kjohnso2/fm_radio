Name:       agl-plugins
Summary:    A collection of IVI software
Version:    0.0.1
Release:    1
Group:      Applications/Web Applications
License:    ASL 2.0
URL:        http://www.tizen.org2
Source0:    %{name}-%{version}.tar.bz2

# External requirements to build deps
BuildRequires:  python
BuildRequires:  desktop-file-utils
BuildRequires:  cmake

# Actual app/service requirements
BuildRequires:  pkgconfig(eina)
BuildRequires:  pkgconfig(eet)
BuildRequires:  pkgconfig(evas)
BuildRequires:  pkgconfig(ecore)
BuildRequires:  pkgconfig(ecore-evas)
BuildRequires:  pkgconfig(edje)
BuildRequires:  pkgconfig(efreet)
BuildRequires:  pkgconfig(eldbus)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(dbus-glib-1)
BuildRequires:  pkgconfig(systemd)
BuildRequires:  pkgconfig(gstreamer-1.0)
BuildRequires:  pkgconfig(gstreamer-base-1.0)
BuildRequires:  pkgconfig(gstreamer-audio-1.0)
BuildRequires:  pkgconfig(sndfile)
BuildRequires:  pkgconfig(libusb-1.0)

# Run-time dependencies
Requires:       ibus
Requires:       ibus-hangul
Requires:       ibus-libpinyin
Requires:       systemd
Requires:       gstreamer
Requires:       dbus-glib
Requires:       dbus
Requires:       libglib
Requires:       libusb
Requires:       libsndfile

%global plugin_list extension_common BoilerPlateExtension wkb_client_ext FMRadioExtension
%global autogen_list FMRadioService FMRadioService/gst-sdr-j-fm
%global deps_list rtl-sdr fftw-3.3.4 libsamplerate-0.1.8

%description
A collection of IVI software

%package service
Summary: FMRadioService dbus service
Group: System/Audio
%description service
FMRadioService dbus-daemon Service,

%package rtl-sdr
Summary: Library rtl-sdr
Group: System/Audio
%description rtl-sdr
DVB dongle compat library.

%package fftw3
Summary: Library fftw3
Group: System/Audio
%description fftw3
C subroutine library for computing the discrete Fourier transform.

%package samplerate
Summary: Library samplerate
Group: System/Audio
%description samplerate
Sample Rate Converter for audio.

%package gstsdrjfm
Summary: Library samplerate
Group: System/Audio
%description gstsdrjfm
Gstreamer element that demodulates FM radio signal.


%prep
%setup -q -n %{name}-%{version}
echo "HOME : ${HOME} HOME: %{HOME}"

%build
######################################
## Note :
##
## Since dependencies from deps_list
## are not already packaged by tizen
## they are provided here (tarballs)
## and built and installed from source
######################################

# Build rtl-sdr CMAKE project
ROOT_DIR=`pwd`
FMRADIOSERVICE_PATH=${ROOT_DIR}/FMRadioService
RTLSDR_PATH=${FMRADIOSERVICE_PATH}/deps/rtl-sdr
LIBSAMPLERATE_PATH=${FMRADIOSERVICE_PATH}/deps/libsamplerate-0.1.8
FFTW3_PATH=${FMRADIOSERVICE_PATH}/deps/fftw-3.3.4

# First autotool project FMRadioService needs to be autogen'ed
for file in %{autogen_list}; do
	cd ${ROOT_DIR}/${file}
	./autogen.sh
done


# uncompress the deps
cd ${FMRADIOSERVICE_PATH}/deps
for file in %{deps_list}; do
	tar -xvf ${file}.tar.gz
done

# Build RTLSDR dep
cd ${RTLSDR_PATH}
rm -fR build
mkdir build
cd build
cmake .. -DCMAKE_C_FLAGS:STRING="%{optflags}" -DCMAKE_INSTALL_PREFIX=%{_prefix}
make
RTLSDR_LIBS="${RTLSDR_PATH}/src/librtlsdr.so"
RTLSDR_INCLUDES="-I/${RTLSDR_PATH}/include"

# Build FFTW dep
cd ${FFTW3_PATH}
./configure --prefix=%{_prefix} --enable-single --enable-shared
make
FFTW3_LIBS="${FFTW3_PATH}/.libs/libfftw3f.la"
FFTW3_INCLUDES="-I/${FFTW3_PATH}/api"

# Build LIBSAMPLERATE dep
cd ${LIBSAMPLERATE_PATH}
./configure --prefix=%{_prefix}
make
LIBSAMPLERATE_LIBS="${LIBSAMPLERATE_PATH}/src/.libs/libsamplerate.la"
LIBSAMPLERATE_INCLUDES="-I/${LIBSAMPLERATE_PATH}/src"

# Now build autotool-like FMRadioService and gstreamer gstsdrjfm plugin
cd ${FMRADIOSERVICE_PATH}
LD_LIBRARY_PATH=${RTLSDR_LIBPATH} RS_CFLAGS=${RTLSDR_INCLUDES} RS_LIBS=${RTLSDR_LIBS} SR_CFLAGS=${LIBSAMPLERATE_INCLUDES} SR_LIBS=${LIBSAMPLERATE_LIBS} FFTW_CFLAGS=${FFTW3_INCLUDES} FFTW_LIBS=${FFTW3_LIBS} ./configure --prefix=%{_prefix}
make -n &> ~/make.log
make

cd ${ROOT_DIR}
# Build all the xwalk extension plugins
for folder in %{plugin_list}; do
	make -C ${folder}
done


%install
# Build rtl-sdr CMAKE project
ROOT_DIR=`pwd`
FMRADIOSERVICE_PATH=${ROOT_DIR}/FMRadioService
RTLSDR_PATH=${FMRADIOSERVICE_PATH}/deps/rtl-sdr
LIBSAMPLERATE_PATH=${FMRADIOSERVICE_PATH}/deps/libsamplerate-0.1.8
FFTW3_PATH=${FMRADIOSERVICE_PATH}/deps/fftw-3.3.4

# Install RTLSDR dep
cd ${RTLSDR_PATH}/build
make install DESTDIR=%{buildroot} PREFIX=%{_prefix}

# Install FFTW dep
cd ${FFTW3_PATH}
make install DESTDIR=%{buildroot} PREFIX=%{_prefix}

# Install LIBSAMPLERATE dep
cd ${LIBSAMPLERATE_PATH}
make install DESTDIR=%{buildroot} PREFIX=%{_prefix}

# Install FMRadioService
# manually add those paths that we are going to install
mkdir -p %{buildroot}/usr/lib/systemd/user
mkdir -p %{buildroot}/usr/share/dbus-1/services
cd ${FMRADIOSERVICE_PATH}
make install DESTDIR=%{buildroot} PREFIX=%{_prefix}

cd ${FMRADIOSERVICE_PATH}/gst-sdr-j-fm

# Install the the extension plugins
cd ${ROOT_DIR}
for folder in %{plugin_list}; do
    make -C ${folder} install DESTDIR=%{buildroot} PREFIX=%{_prefix}
done

%post -n agl-plugins-rtl-sdr -p /sbin/ldconfig
%post -n agl-plugins-fftw3 -p /sbin/ldconfig
%post -n agl-plugins-samplerate -p /sbin/ldconfig

%postun -n agl-plugins-rtl-sdr -p /sbin/ldconfig
%postun -n agl-plugins-fftw3 -p /sbin/ldconfig
%postun -n agl-plugins-samplerate -p /sbin/ldconfig

%files
%{_prefix}/lib/tizen-extensions-crosswalk/libbp.so
%{_prefix}/lib/tizen-extensions-crosswalk/libwkb_client.so
%{_prefix}/lib/tizen-extensions-crosswalk/lib_fmradio.so
%{_prefix}/share/X11/xkb/symbols/wkb
%{_prefix}/local/sbin/kb_inst
%{_prefix}/share/weekeyboard/blue_1080.edj
%{_prefix}/share/weekeyboard/blue_720.edj
%{_prefix}/share/weekeyboard/blue_600.edj
%{_prefix}/share/weekeyboard/green_1080.edj
%{_prefix}/share/weekeyboard/green_720.edj
%{_prefix}/share/weekeyboard/green_600.edj
%{_prefix}/share/weekeyboard/amber_1080.edj
%{_prefix}/share/weekeyboard/amber_720.edj
%{_prefix}/share/weekeyboard/amber_600.edj

%files rtl-sdr
%{_prefix}/bin/rtl_adsb
%{_prefix}/bin/rtl_eeprom
%{_prefix}/bin/rtl_fm
%{_prefix}/bin/rtl_sdr
%{_prefix}/bin/rtl_tcp
%{_prefix}/bin/rtl_test
%{_prefix}/lib/debug/usr/bin/rtl_adsb.debug
%{_prefix}/lib/debug/usr/bin/rtl_eeprom.debug
%{_prefix}/lib/debug/usr/bin/rtl_fm.debug
%{_prefix}/lib/debug/usr/bin/rtl_sdr.debug
%{_prefix}/lib/debug/usr/bin/rtl_tcp.debug
%{_prefix}/lib/debug/usr/bin/rtl_test.debug
%{_prefix}/lib/debug/usr/lib/librtlsdr.so.0.5.0.debug
%{_prefix}/lib/librtlsdr.a
%{_prefix}/lib/librtlsdr.so
%{_prefix}/lib/librtlsdr.so.0
%{_prefix}/lib/librtlsdr.so.0.5.0
%{_prefix}/lib/pkgconfig/librtlsdr.pc
%{_prefix}/include/rtl-sdr.h
%{_prefix}/include/rtl-sdr_export.h

%files fftw3
%{_prefix}/bin/fftw-wisdom-to-conf
%{_prefix}/bin/fftwf-wisdom
%{_prefix}/include/fftw3.f
%{_prefix}/include/fftw3.f03
%{_prefix}/include/fftw3.h
%{_prefix}/include/fftw3l.f03
%{_prefix}/include/fftw3q.f03
%{_prefix}/lib/debug/usr/bin/fftwf-wisdom.debug
%{_prefix}/lib/debug/usr/lib/libfftw3f.so.3.4.4.debug
%{_prefix}/lib/libfftw3f.a
%{_prefix}/lib/libfftw3f.la
%{_prefix}/lib/libfftw3f.so
%{_prefix}/lib/libfftw3f.so.3
%{_prefix}/lib/libfftw3f.so.3.4.4
%{_prefix}/lib/pkgconfig/fftw3f.pc
%{_prefix}/share/info/fftw3.info-1.gz
%{_prefix}/share/info/fftw3.info-2.gz
%{_prefix}/share/info/fftw3.info.gz
%{_prefix}/share/man/man1/fftw-wisdom-to-conf.1.gz
%{_prefix}/share/man/man1/fftwf-wisdom.1.gz

%files samplerate
%{_prefix}/include/samplerate.h
%{_prefix}/bin/sndfile-resample
%{_prefix}/lib/debug/usr/bin/sndfile-resample.debug
%{_prefix}/lib/debug/usr/lib/libsamplerate.so.0.1.8.debug
%{_prefix}/lib/libsamplerate.a
%{_prefix}/lib/libsamplerate.la
%{_prefix}/lib/libsamplerate.so
%{_prefix}/lib/libsamplerate.so.0
%{_prefix}/lib/libsamplerate.so.0.1.8
%{_prefix}/lib/pkgconfig/samplerate.pc
%{_prefix}/share/doc/libsamplerate0-dev/html/SRC.css
%{_prefix}/share/doc/libsamplerate0-dev/html/SRC.png
%{_prefix}/share/doc/libsamplerate0-dev/html/api.html
%{_prefix}/share/doc/libsamplerate0-dev/html/api_callback.html
%{_prefix}/share/doc/libsamplerate0-dev/html/api_full.html
%{_prefix}/share/doc/libsamplerate0-dev/html/api_misc.html
%{_prefix}/share/doc/libsamplerate0-dev/html/api_simple.html
%{_prefix}/share/doc/libsamplerate0-dev/html/download.html
%{_prefix}/share/doc/libsamplerate0-dev/html/faq.html
%{_prefix}/share/doc/libsamplerate0-dev/html/history.html
%{_prefix}/share/doc/libsamplerate0-dev/html/index.html
%{_prefix}/share/doc/libsamplerate0-dev/html/license.html
%{_prefix}/share/doc/libsamplerate0-dev/html/lists.html
%{_prefix}/share/doc/libsamplerate0-dev/html/quality.html
%{_prefix}/share/doc/libsamplerate0-dev/html/win32.html

%files gstsdrjfm
%{_prefix}/lib/debug/usr/lib/gstreamer-1.0/libgstsdrjfm.so.debug
%{_prefix}/lib/gstreamer-1.0/libgstsdrjfm.a
%{_prefix}/lib/gstreamer-1.0/libgstsdrjfm.la
%{_prefix}/lib/gstreamer-1.0/libgstsdrjfm.so

%files service
%{_prefix}/lib/systemd/user/fmradioservice.service
%{_prefix}/share/dbus-1/services/com.jlr.fmradioservice.service
%{_prefix}/bin/fmradioservice

