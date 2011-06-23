from distutils.core import setup

setup(name = "pywapi-dbus",
    version = "0.1a1",
    description = "D-Bus Python Weather API Service is a D-Bus service providing weather information",
    author = "Sasu Karttunen",
    author_email = "sasu.karttunen@tpnet.fi",
    url = "https://github.com/skfin/pywapi-dbus",
    packages = ['pywapi-dbus-data'],
    scripts = ["pywapi-dbus"],
    long_description = """D-Bus Python Weather API Service is intended to provide weather information through D-Bus. It's main goal is to provide same functionality as Python Weather API provides as Python library. D-Bus Python Weather API Service can be used in all programming languages that has working D-Bus libraries available.""", 
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: GNU Lesser General Public License (LGPL)',
      'Programming Language :: Python',
      ]
) 