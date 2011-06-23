from distutils.core import Distribution, Command
from distutils.command.install import install
from distutils.command.build import build
from distutils.command.sdist import sdist
from distutils.dep_util import newer
from distutils.util import convert_path
import os

class oms_sdist(sdist):
    def add_defaults(self):
        sdist.add_defaults(self)
        if self.distribution.has_dbus_files():
            plugins = self.get_finalized_command('build_dbus_files')
            self.filelist.extend(plugins.get_dbus_files())

class oms_install(install):
    
    user_options = []
    user_options.extend(install.user_options)
    user_options.append(('install-dbus=', 'd', "installation directory for dbus service files"))

    def initialize_options (self):
        install.initialize_options(self)
        self.dbus_files = None
        self.install_dbus = None

    def finalize_options (self):
        install.finalize_options(self)
        if self.install_dbus is None:
            self.install_dbus = os.path.join(self.install_data, 'share', 'dbus-1',  'services')

    def has_dbus_files(self):
        return self.distribution.has_dbus_files()

    sub_commands = []
    sub_commands.extend(install.sub_commands)
    sub_commands.append(('install_dbus_files', has_dbus_files))


class oms_build(build):
    
    user_options = []
    user_options.extend(build.user_options)
    user_options.append(('build-dbus=', 'd', "build directory for dbus service files"))

    def initialize_options (self):
        build.initialize_options(self)
        self.build_dbus = None

    def finalize_options (self):
        build.finalize_options(self)
        if self.build_dbus is None:
            self.build_dbus = os.path.join(self.build_base, 'dbus')

    def has_dbus_files(self):
        return self.distribution.has_dbus_files()

    sub_commands = []
    sub_commands.extend(build.sub_commands)
    sub_commands.append(('build_dbus_files', has_dbus_files))

class build_dbus_files (Command):

    description = "build D-Bus service files"

    user_options = [
        ('build-base=', 'd', "directory to \"build\" (generate) to"),
        ]

    def initialize_options (self):
        self.build_dir = None
        self.install_dir = None
        self.dbus_files = None
        self.outfiles = None

    def get_dbus_files(self):
        return self.dbus_files

    def finalize_options (self):
        self.set_undefined_options('build',
                                   ('build_dbus', 'build_dir'))
        self.set_undefined_options('install',
                                   ('install_scripts', 'install_dir'))
        self.dbus_files = self.distribution.dbus_files


    def run (self):
        if not self.dbus_files:
            return
        self.copy_dbus_files()


    def copy_dbus_files (self):
        """Copy each service files listed in 'self.dbus_files'.
        """
        self.mkpath(self.build_dir)        
        for service_file in self.dbus_files:
            adjust = 0
            service_file = convert_path(service_file)
            if service_file[-3:] != ".in":
                self.warn("skipping file " + service_file + " because dbus service files need .in as extension")
                continue
            service_filename = os.path.basename(service_file)
            
            out_file = os.path.join("/usr/share/dbus-1/services/", service_filename)[:-3]

            # Always open the file, but ignore failures in dry-run mode --
            # that way, we'll get accurate feedback if we can read the
            # service file.
            try:
                service = open(service_file, "r")
            except IOError:
                if not self.dry_run:
                    raise
                service = None
            else:
                self.mkpath(os.path.dirname(out_file))
                try:
                    out = open(out_file, "w")
                    out.write(service.read().replace("@bindir@",  self.install_dir))
                    out.close()
                    self.announce("copying/editing %s -> %s" % (service_file,  out_file),  2)
                except IOError:
                    if not self.dry_run:
                        raise
                service.close()


class install_dbus_files(Command):

    description = "install D-Bus service files"

    user_options = [
        ('install-dir=', 'd', "directory to install dbus service files to"),
        ('build-base=','b', "build directory (where to install from)"),
        ('force', 'f', "force installation (overwrite existing files)"),
        ('skip-build', None, "skip the build steps"),
    ]

    boolean_options = ['force', 'skip-build']


    def initialize_options (self):
        self.install_dir = None
        self.force = 0
        self.build_dbus = None
        self.skip_build = None

    def finalize_options (self):
        self.set_undefined_options('build',
                                   ('build_dbus', 'build_dbus'))
        self.set_undefined_options('install',
                                   ('install_dbus', 'install_dir'),
                                   ('force', 'force'),
                                   ('skip_build', 'skip_build'),
                                  )

    def run (self):
        if not self.skip_build:
            self.run_command('build_dbus_files')
        self.outfiles = self.copy_tree(self.build_dbus, self.install_dir)

    def get_inputs (self):
        return self.distribution.dbus_files or []

    def get_outputs(self):
        return self.outfiles or []



class OpenMobileSuiteDistribution(Distribution):
    def __init__(self,attrs=None):
        self.dbus_files = None
        Distribution.__init__(self, attrs)
        self.cmdclass = {'install':oms_install,
                         'install_dbus_files':install_dbus_files,
                         'build':oms_build,
                         'build_dbus_files':build_dbus_files,
                         'sdist':oms_sdist,
                         }

    def has_dbus_files(self):
        return self.dbus_files and len(self.dbus_files) > 0


def setup(**attrs):
    from distutils import core
    attrs['distclass'] = OpenMobileSuiteDistribution
    core.setup(**attrs)
