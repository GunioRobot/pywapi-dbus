from distutils.core import setup

setup(name = "pywapi-dbus",
    version = "0.1a1",
    description = "D-Bus Python Weather API Service is a D-Bus service providing weather information",
    author = "Sasu Karttunen",
    author_email = "sasu.karttunen@tpnet.fi",
    url = "https://github.com/skfin/pywapi-dbus",
    scripts = ['pywapidbus/pywapi-dbus'],
    packages = ['pywapidbus'],
    data_files=[('share/dbus-1/services', ['pywapidbus/org.pywapi.Daemon.service'])],
    long_description = """D-Bus Python Weather API Service is intended to provide weather information through D-Bus. It's main goal is to provide same functionality as Python Weather API provides as Python library. D-Bus Python Weather API Service can be used in all programming languages that has working D-Bus libraries available.""", 
    classifiers=[
      'Development Status :: 4 - ',
      'Intended Audience :: Developers',
      'Intended Audience :: System Administrators',
      'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
      'Programming Language :: Python',
      'Environment :: No Input/Output (Daemon)',
      'Operating System :: UNIX',
      'Topic :: Software Development :: Libraries', # Not actually a library. Don't blame us, blame trove classifiers.
      'Topic :: Scientific/Engineering :: Atmospheric Science', # We can provide some athmosperic information :P
      ]
) 
