#
# Copyright (c) 2017 nexB Inc. and others. All rights reserved.
# http://nexb.com and https://github.com/nexB/scancode-toolkit/
# The ScanCode software is licensed under the Apache License version 2.0.
# Data generated with ScanCode require an acknowledgment.
# ScanCode is a trademark of nexB Inc.
#
# You may not use this software except in compliance with the License.
# You may obtain a copy of the License at: http://apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
# When you publish or redistribute any data created with ScanCode or any ScanCode
# derivative work, you must accompany this data with the following acknowledgment:
#
#  Generated with ScanCode and provided on an "AS IS" BASIS, WITHOUT WARRANTIES
#  OR CONDITIONS OF ANY KIND, either express or implied. No content created from
#  ScanCode should be considered or used as legal advice. Consult an Attorney
#  for any legal advice.
#  ScanCode is a free software code scanning tool from nexB Inc. and others.
#  Visit https://github.com/nexB/scancode-toolkit/ for support and download.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple
import logging
import sys

from schematics.exceptions import StopValidation
from schematics.models import Model
from schematics.transforms import blacklist
from schematics.types import BaseType
from schematics.types import DateTimeType
from schematics.types import EmailType
from schematics.types import LongType
from schematics.types import StringType
from schematics.types import URLType
from schematics.types.compound import DictType
from schematics.types.compound import ListType
from schematics.types.compound import ModelType

"""
Data models for package information and dependencies, abstracting the
differences existing between package formats and tools.

A package is  code that can be consumed and provisioned by a package
manager or can be installed.

It can be a single file such as script; more commonly a package is
stored in an archive or directory.

A package contains:
 - information/metadata,
 - a payload of code, doc, data.

Package metadata are found in multiple places:
- in manifest (such as a Maven POM, NPM package.json and many others)
- in binaries (such as an Elf or LKM, Windows PE or RPM header).
- in code (JavaDoc tags or Python __copyright__ magic)

These metadata provide details such as:
 - package identifier (e.g. name and version).
 - package registry
 - download URLs or information
 - pre-requisite such as OS, runtime, architecture, API/ABI, etc.
 - informative description, keywords, URLs, etc.
 - author, provider, distributor, vendor, etc. collectively ass "parties"
 - contact and support information (emails, mailing lists, ...)
 - checksum or signature to verify integrity
 - version control references (Git, SVN repo)
 - license and copyright
 - dependencies on other packages
 - build/packaging instructions
 - installation directives/scripts
 - corresponding sources download pointers
 - modification or patches applied,changelog docs.
"""


TRACE = False

def logger_debug(*args):
    pass

logger = logging.getLogger(__name__)

if TRACE:
    logging.basicConfig(stream=sys.stdout)
    logger.setLevel(logging.DEBUG)

    def logger_debug(*args):
        return logger.debug(' '.join(isinstance(a, basestring) and a or repr(a) for a in args))


class BaseListType(ListType):
    """
    ListType with a default of an empty list.
    """

    def __init__(self, field, **kwargs):
        super(BaseListType, self).__init__(field=field, default=[], **kwargs)


PackageId = namedtuple('PackageId', 'type name version')


class PackageIndentifierType(BaseType):
    """
    Global identifier for a package
    """

    def __init__(self, **kwargs):
        super(PackageIndentifierType, self).__init__(**kwargs)

    def to_primitive(self, value, context=None):
        """
        Return a package id string, joining segments with a pipe separator.
        """
        if not value:
            return value

        if isinstance(value, PackageId):
            return u'|'.join(v or u'' for v in value)
        else:
            raise TypeError('Invalid package identifier')

    def to_native(self, value):
        return value

    def validate_id(self, value):
        if not isinstance(value, PackageId):
            raise StopValidation(self.messages['Invalid Package ID: must be PackageId named tuple'])


class BaseModel(Model):
    """
    Base class for all schematics models.
    """

    def __init__(self, **kwargs):
        super(BaseModel, self).__init__(raw_data=kwargs)

    def to_dict(self, **kwargs):
        """
        Return a dict of primitive Python types for this model instance.
        This is an OrderedDict because each model has a 'field_order' option.
        """
        return self.to_primitive(**kwargs)


# Party types
#################################
party_person = 'person'
party_project = 'project'  # often loosely defined
party_org = 'organization'  # more formally defined
PARTY_TYPES = (party_person, party_project, party_org,)


class Party(BaseModel):
    metadata = dict(
        label='party',
        description='A party is a person, project or organization related to a package.')

    type = StringType(choices=PARTY_TYPES)
    type.metadata = dict(
        label='party type',
        description='the type of this party: One of: ' + ', '.join(PARTY_TYPES))

    name = StringType()
    name.metadata = dict(
        label='name',
        description='Name of this party.')

    url = URLType()
    name.metadata = dict(
        label='url',
        description='URL to a primary web page for this party.')

    email = EmailType()
    email.metadata = dict(
        label='email',
        description='Email for this party.')

    class Options:
        fields_order = 'type', 'name', 'email', 'url'


# Groupings of package dependencies
###################################
dep_runtime = 'runtime'
dep_dev = 'development'
dep_test = 'test'
dep_build = 'build'
dep_optional = 'optional'
dep_bundled = 'bundled'
dep_ci = 'continuous integration'
DEPENDENCY_GROUPS = (dep_runtime, dep_dev, dep_optional, dep_test, dep_build, dep_ci, dep_bundled,)


# FIXME: this is broken ... OSGi uses "Java packages" deps as an indirection and not directly package deps.
class Dependency(BaseModel):
    metadata = dict(
        label='dependency',
        description='A dependency points to a Package via a package name and a version constraint '
        '(such as ">= 3.4"). The version is the effective version that has been '
        'picked and resolved.')

    name = StringType(required=True)
    name.metadata = dict(
        label='name',
        description='Name of the package for this dependency.')

    version = StringType()
    version.metadata = dict(
        label='version',
        description='Version or versions range or constraints for this dependent package')

    class Options:
        fields_order = 'type', 'name', 'version'


# Types of the payload of a Package
###################################
payload_src = 'source'
# binaries include minified JavaScripts and similar obfuscated texts formats
payload_bin = 'binary'
payload_doc = 'doc'
PAYLOADS = (payload_src, payload_bin, payload_doc)

# Packaging types
#################################
as_archive = 'archive'
as_dir = 'directory'
as_file = 'file'
PACKAGINGS = (as_archive, as_dir, as_file)


class BasePackage(BaseModel):
    """
    A base package object.
    """
    metadata = dict(
        label='package',
        description='A package object.')

    ###############################
    # real class-level attributes
    ###############################
    # content types data to recognize a package
    filetypes = tuple()
    mimetypes = tuple()
    extensions = tuple()
    # list of known metafiles for a package type, to recognize a package
    metafiles = []

    ###############################
    # Field descriptors
    ###############################
    # from here on, these are actual instance attributes, using descriptors

    type = StringType(required=True)
    type.metadata = dict(
        label='package type',
        description='Descriptive name of the type of package: '
        'RubyGem, Python Wheel, Java Jar, Debian package, etc.')

    name = StringType(required=True)
    name.metadata = dict(
        label='package name',
        description='Name of the package.')

    version = StringType()
    version.metadata = dict(
        label='package version',
        description='Version of the package. '
        'Package types may implement specific handling for versions but this is always serialized as a string.')

    payload_type = StringType(choices=PAYLOADS)
    payload_type.metadata = dict(
        label='Payload type',
        description='The type of payload for this package. One of: ' + ', '.join(PAYLOADS))

    class Options:
        # this defines the important serialization order
        fields_order = [
            'type',
            'name',
            'version',
            'payload_type',
        ]


class Package(BasePackage):
    """
    A package object.
    Override for specific package behaviour. The way a
    package is created and serialized should be uniform across all Package
    types.
    """
    metadata = dict(
        label='package',
        description='A package object.')

    primary_language = StringType()
    primary_language.metadata = dict(
        label='Primary programming language',
        description='Primary programming language of the package, such as Java, C, C++. '
        'Derived from the package type: i.e. RubyGems are primarily ruby, etc.')

    packaging = StringType(choices=PACKAGINGS)
    packaging.metadata = dict(
        label='Packaging',
        description='How a package is packaged. One of: ' + ', '.join(PACKAGINGS))

    summary = StringType()
    summary.metadata = dict(
        label='Summary',
        description='Summary for this package i.e. a short description')

    description = StringType()
    description.metadata = dict(
        label='Description',
        description='Description for this package '
        'i.e. a long description, often several pages of text')

    # we useLongType instead of IntType is because
    # IntType 2147483647 is the max size which means we cannot store
    # more than 2GB files
    size = LongType()
    size.metadata = dict(
        label='size',
        description='size of the package download in bytes')

    release_date = DateTimeType()
    release_date.metadata = dict(
        label='release date',
        description='Release date of the package')

    # FIXME: this would be simpler as a list where each Party has also a type
    authors = BaseListType(ModelType(Party))
    authors.metadata = dict(
        label='authors',
        description='A list of party objects. Note: this model schema will change soon.')

    maintainers = BaseListType(ModelType(Party))
    maintainers.metadata = dict(
        label='maintainers',
        description='A list of party objects. Note: this model schema will change soon.')

    contributors = BaseListType(ModelType(Party))
    contributors.metadata = dict(
        label='contributors',
        description='A list of party objects. Note: this model schema will change soon.')

    owners = BaseListType(ModelType(Party))
    owners.metadata = dict(
        label='owners',
        description='A list of party objects. Note: this model schema will change soon.')

    packagers = BaseListType(ModelType(Party))
    packagers.metadata = dict(
        label='owners',
        description='A list of party objects. Note: this model schema will change soon.')

    distributors = BaseListType(ModelType(Party))
    distributors.metadata = dict(
        label='distributors',
        description='A list of party objects. Note: this model schema will change soon.')

    vendors = BaseListType(ModelType(Party))
    vendors.metadata = dict(
        label='vendors',
        description='A list of party objects. Note: this model schema will change soon.')

    keywords = BaseListType(StringType())
    keywords.metadata = dict(
        label='keywords',
        description='A list of keywords or tags.')

    # FIXME: this is a Package-class attribute
    keywords_doc_url = URLType()
    keywords_doc_url.metadata = dict(
        label='keywords documentation URL',
        description='URL to a reference documentation for keywords or '
        'tags (such as a Pypi or SF.net Trove map)')

    homepage_url = StringType()
    homepage_url.metadata = dict(
        label='homepage URL',
        description='URL to the homepage for this package')

    download_urls = BaseListType(StringType())
    download_urls.metadata = dict(
        label='Download URLs',
        description='A list of direct download URLs, possibly in SPDX VCS url form. '
        'The first item is considered to be the primary download URL')

    download_sha1 = StringType()
    download_sha1.metadata = dict(label='Download SHA1', description='Shecksum for the download')
    download_sha256 = StringType()
    download_sha256.metadata = dict(label='Download SHA256', description='Shecksum for the download')
    download_md5 = StringType()
    download_md5.metadata = dict(label='Download MD5', description='Shecksum for the download')

    bug_tracking_url = URLType()
    bug_tracking_url.metadata = dict(
        label='bug tracking URL',
        description='URL to the issue or bug tracker for this package')

    support_contacts = BaseListType(StringType())
    support_contacts.metadata = dict(
        label='Support contacts',
        description='A list of strings (such as email, urls, etc) for support contacts')

    code_view_url = StringType()
    code_view_url.metadata = dict(
        label='code view URL',
        description='a URL where the code can be browsed online')

    VCS_CHOICES = ['git', 'svn', 'hg', 'bzr', 'cvs']
    vcs_tool = StringType(choices=VCS_CHOICES)
    vcs_tool.metadata = dict(
        label='Version control system tool',
        description='The type of VCS tool for this package. One of: ' + ', '.join(VCS_CHOICES))

    vcs_repository = StringType()
    vcs_repository.metadata = dict(
        label='VCS Repository URL',
        description='a URL to the VCS repository in the SPDX form of:'
        'git+https://github.com/nexb/scancode-toolkit.git')

    vcs_revision = StringType()
    vcs_revision.metadata = dict(
        label='VCS revision',
        description='a revision, commit, branch or tag reference, etc. '
        '(can also be included in the URL)')

    copyrights = BaseListType(StringType())
    copyrights.metadata = dict(
        label='Copyrights',
        description='A list of effective copyrights as detected and eventually summarized')

    asserted_license = StringType()
    asserted_license.metadata = dict(
        label='asserted license',
        description='The license as asserted by this package as a text.')

    license_expression = StringType()
    license_expression.metadata = dict(
        label='license expression',
        description='license expression: either resolved or detected license expression')

    license_texts = BaseListType(StringType())
    license_texts.metadata = dict(
        label='license texts',
        description='A list of license texts for this package.')

    notice_text = StringType()
    notice_text.metadata = dict(
        label='notice text',
        description='A notice text for this package.')

    # Map a DEPENDENCY_GROUPS group name to a list of Dependency
    # FIXME: we should instead just have a plain list where each dep contain a group.
    dependencies = DictType(ListType(ModelType(Dependency)), default={})
    dependencies.metadata = dict(
        label='dependencies',
        description='An object mapping a dependency group to a '
        'list of dependency objects for this package. '
        'Note: the schema for this will change soon.'
        'The possible values for dependency grousp are:' + ', '.join(DEPENDENCY_GROUPS)
        )

    related_packages = BaseListType(ModelType(BasePackage))
    related_packages.metadata = dict(
        label='related packages',
        description='A list of related Packages objects for this package. '
        'For instance the SRPM source of a binary RPM.')

    class Options:
        # this defines the important serialization order
        fields_order = [
            'type',
            'name',
            'version',
            'primary_language',
            'packaging',
            'summary',
            'description',
            'payload_type',
            'size',
            'release_date',

            'authors',
            'maintainers',
            'contributors',
            'owners',
            'packagers',
            'distributors',
            'vendors',

            'keywords',
            'keywords_doc_url',

            'homepage_url',
            'download_urls',
            'download_sha1',
            'download_sha256',
            'download_md5',

            'bug_tracking_url',
            'support_contacts',
            'code_view_url',

            'vcs_tool',
            'vcs_repository',
            'vcs_revision',

            'copyrights',

            'asserted_license',
            'license_expression',
            'license_texts',
            'notice_text',

            'dependencies',
            'related_packages'
        ]

        # we use for now a "role" that excludes deps and relationships from the
        # serailization
        roles = {'no_deps': blacklist('dependencies', 'related_packages')}

    def __init__(self, location=None, **kwargs):
        """
        Initialize a new Package.
        Subclass can override but should override the recognize method to populate a package accordingly.
        """
        # path to a file or directory where this Package is found in a scan
        self.location = location
        super(Package, self).__init__(**kwargs)

    @classmethod
    def recognize(cls, location):
        """
        Return a Package object or None given a location to a file or directory
        pointing to a package archive, metafile or similar.

        Sub-classes should override to implement their own package recognition.
        """
        return cls()

    @property
    def component_version(self):
        """
        Return the component-level version representation for this package.
        Subclasses can override.
        """
        return self.version

    def compare_version(self, other, component_level=False):
        """
        Compare the version of this package with another package version.

        Use the same semantics as the builtin cmp function. It returns:
        - a negaitive integer if this version < other version,
        - zero if this version== other.version
        - a positive interger if this version > other version.

        Use the component-level version if `component_level` is True.

        Subclasses can override for package-type specific comparisons.

        For example:
        # >>> q=Package(version='2')
        # >>> p=Package(version='1')
        # >>> p.compare_version(q)
        # -1
        # >>> p.compare_version(p)
        # 0
        # >>> r=Package(version='0')
        # >>> p.compare_version(r)
        # 1
        # >>> s=Package(version='1')
        # >>> p.compare_version(s)
        # 0
        """
        x = component_level and self.component_version() or self.version
        y = component_level and other.component_version() or self.version
        return cmp(x, y)

    def sort_key(self):
        """
        Return some data suiatble to use as a key function when sorting.
        """
        return (self.type, self.name, self.version.sortable(self.version),)

    @property
    def identifier(self):
        """
        Return a PackageId object for this package.
        """
        return PackageId(self.type, self.name, self.version)

#
# Package sub types
# NOTE: this is somewhat redundant with extractcode archive handlers
# yet the purpose and semantics are rather different here


class DebianPackage(Package):
    metafiles = ('*.control',)
    extensions = ('.deb',)
    filetypes = ('debian binary package',)
    mimetypes = ('application/x-archive', 'application/vnd.debian.binary-package',)

    type = StringType(default='Debian package')
    packaging = StringType(default=as_archive)


class JavaJar(Package):
    metafiles = ('META-INF/MANIFEST.MF',)
    extensions = ('.jar',)
    filetypes = ('java archive ', 'zip archive',)
    mimetypes = ('application/java-archive', 'application/zip',)

    type = StringType(default='Java Jar')
    packaging = StringType(default=as_archive)
    primary_language = StringType(default='Java')


class JavaWar(Package):
    metafiles = ('WEB-INF/web.xml',)
    extensions = ('.war',)
    filetypes = ('java archive ', 'zip archive',)
    mimetypes = ('application/java-archive', 'application/zip')

    type = StringType(default='Java Web application')
    packaging = StringType(default=as_archive)
    primary_language = StringType(default='Java')


class JavaEar(Package):
    metafiles = ('META-INF/application.xml', 'META-INF/ejb-jar.xml')
    extensions = ('.ear',)
    filetypes = ('java archive ', 'zip archive',)
    mimetypes = ('application/java-archive', 'application/zip')

    type = StringType(default='Enterprise Java application')
    packaging = StringType(default=as_archive)
    primary_language = StringType(default='Java')


class Axis2Mar(Package):
    metafiles = ('META-INF/module.xml',)
    extensions = ('.mar',)
    filetypes = ('java archive ', 'zip archive',)
    mimetypes = ('application/java-archive', 'application/zip')

    type = StringType(default='Apache Axis2 module')
    packaging = StringType(default=as_archive)
    primary_language = StringType(default='Java')


class JBossSar(Package):
    metafiles = ('META-INF/jboss-service.xml',)
    extensions = ('.sar',)
    filetypes = ('java archive ', 'zip archive',)
    mimetypes = ('application/java-archive', 'application/zip')

    type = StringType(default='JBoss service archive')
    packaging = StringType(default=as_archive)
    primary_language = StringType(default='Java')


class IvyJar(JavaJar):
    metafiles = ('ivy.xml',)

    type = StringType(default='Apache IVY package')


class BowerPackage(Package):
    metafiles = ('bower.json',)

    type = StringType(default='Bower package')
    primary_language = StringType(default='JavaScript')


class MeteorPackage(Package):
    metafiles = ('package.js',)

    type = StringType(default='Meteor package')
    primary_language = 'JavaScript'


class CpanModule(Package):
    metafiles = ('*.pod', '*.pm', 'MANIFEST', 'Makefile.PL', 'META.yml', 'META.json', '*.meta', 'dist.ini')
    # TODO: refine me
    extensions = (
        '.tar.gz',
    )

    type = StringType(default='CPAN Perl module')
    primary_language = 'Perl'


# TODO: refine me
class Godep(Package):
    metafiles = ('Godeps',)

    type = StringType(default='Go package')
    primary_language = 'Go'


class RubyGem(Package):
    metafiles = ('*.control', '*.gemspec', 'Gemfile', 'Gemfile.lock',)
    filetypes = ('.tar', 'tar archive',)
    mimetypes = ('application/x-tar',)
    extensions = ('.gem',)

    type = StringType(default='RubyGem')
    primary_language = 'Ruby'
    packaging = StringType(default=as_archive)


class AndroidApp(Package):
    filetypes = ('zip archive',)
    mimetypes = ('application/zip',)
    extensions = ('.apk',)

    type = StringType(default='Android app')
    primary_language = StringType(default='Java')
    packaging = StringType(default=as_archive)


# see http://tools.android.com/tech-docs/new-build-system/aar-formats
class AndroidLibrary(Package):
    filetypes = ('zip archive',)
    mimetypes = ('application/zip',)
    # note: Apache Axis also uses AAR extensions for plain Jars.
    # this could be decided based on internal structure
    extensions = ('.aar',)

    type = StringType(default='Android library')
    primary_language = StringType(default='Java')
    packaging = StringType(default=as_archive)


class MozillaExtension(Package):
    filetypes = ('zip archive',)
    mimetypes = ('application/zip',)
    extensions = ('.xpi',)

    type = StringType(default='Mozilla extension')
    primary_language = StringType(default='JavaScript')
    packaging = StringType(default=as_archive)


class ChromeExtension(Package):
    filetypes = ('data',)
    mimetypes = ('application/octet-stream',)
    extensions = ('.crx',)

    type = StringType(default='Chrome extension')
    primary_language = StringType(default='JavaScript')
    packaging = StringType(default=as_archive)


class IOSApp(Package):
    filetypes = ('zip archive',)
    mimetypes = ('application/zip',)
    extensions = ('.ipa',)

    type = StringType(default='iOS app')
    primary_language = StringType(default='Objective-C')
    packaging = StringType(default=as_archive)


class PythonPackage(Package):
    filetypes = ('zip archive',)
    mimetypes = ('application/zip',)
    extensions = ('.egg', '.whl', '.pyz', '.pex',)

    type = StringType(default='Python package')
    primary_language = StringType(default='Python')
    packaging = StringType(default=as_archive)


class CabPackage(Package):
    filetypes = ('microsoft cabinet',)
    mimetypes = ('application/vnd.ms-cab-compressed',)
    extensions = ('.cab',)

    type = StringType(default='Microsoft cab')
    packaging = StringType(default=as_archive)


class MsiInstallerPackage(Package):
    filetypes = ('msi installer',)
    mimetypes = ('application/x-msi',)
    extensions = ('.msi',)

    type = StringType(default='Microsoft MSI Installer')
    packaging = StringType(default=as_archive)


class InstallShieldPackage(Package):
    filetypes = ('installshield',)
    mimetypes = ('application/x-dosexec',)
    extensions = ('.exe',)

    type = StringType(default='InstallShield Installer')
    packaging = StringType(default=as_archive)


class NSISInstallerPackage(Package):
    filetypes = ('nullsoft installer',)
    mimetypes = ('application/x-dosexec',)
    extensions = ('.exe',)

    type = StringType(default='Nullsoft Installer')
    packaging = StringType(default=as_archive)


class SharPackage(Package):
    filetypes = ('posix shell script',)
    mimetypes = ('text/x-shellscript',)
    extensions = ('.sha', '.shar', '.bin',)

    type = StringType(default='shar shell archive')
    packaging = StringType(default=as_archive)


class AppleDmgPackage(Package):
    filetypes = ('zlib compressed',)
    mimetypes = ('application/zlib',)
    extensions = ('.dmg', '.sparseimage',)

    type = StringType(default='Apple dmg')
    packaging = StringType(default=as_archive)


class IsoImagePackage(Package):
    filetypes = ('iso 9660 cd-rom', 'high sierra cd-rom',)
    mimetypes = ('application/x-iso9660-image',)
    extensions = ('.iso', '.udf', '.img',)

    type = StringType(default='ISO CD image')
    packaging = StringType(default=as_archive)


class SquashfsPackage(Package):
    filetypes = ('squashfs',)

    type = StringType(default='squashfs image')
    packaging = StringType(default=as_archive)

#
# these very generic archive packages must come last in recogniztion order
#


class RarPackage(Package):
    filetypes = ('rar archive',)
    mimetypes = ('application/x-rar',)
    extensions = ('.rar',)

    type = StringType(default='RAR archive')
    packaging = StringType(default=as_archive)


class TarPackage(Package):
    filetypes = (
        '.tar', 'tar archive',
        'xz compressed', 'lzma compressed',
        'gzip compressed',
        'bzip2 compressed',
        '7-zip archive',
        "compress'd data",
    )
    mimetypes = (
        'application/x-xz',
        'application/x-tar',
        'application/x-lzma',
        'application/x-gzip',
        'application/x-bzip2',
        'application/x-7z-compressed',
        'application/x-compress',
    )
    extensions = (
        '.tar', '.tar.xz', '.txz', '.tarxz',
        'tar.lzma', '.tlz', '.tarlz', '.tarlzma',
        '.tgz', '.tar.gz', '.tar.gzip', '.targz', '.targzip', '.tgzip',
        '.tar.bz2', '.tar.bz', '.tar.bzip', '.tar.bzip2', '.tbz',
        '.tbz2', '.tb2', '.tarbz2',
        '.tar.7z', '.tar.7zip', '.t7z',
        '.tz', '.tar.z', '.tarz',
    )

    type = StringType(default='plain tarball')
    packaging = StringType(default=as_archive)


class PlainZipPackage(Package):
    filetypes = ('zip archive', '7-zip archive',)
    mimetypes = ('application/zip', 'application/x-7z-compressed',)
    extensions = ('.zip', '.zipx', '.7z',)

    packaging = StringType(default=as_archive)
    type = StringType(default='plain zip')

# TODO: Add VM images formats(VMDK, OVA, OVF, VDI, etc) and Docker/other containers
