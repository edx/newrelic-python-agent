import sys
import os

from distutils.core import setup

copyright = '(C) Copyright 2010-2011 New Relic Inc. All rights reserved.'

import newrelic

build_number = os.environ.get('HUDSON_BUILD_NUMBER', '0')
package_version = "%s.%s" % (newrelic.version, build_number)

packages = [
  "newrelic",
  "newrelic.api",
  "newrelic.core",
  "newrelic.hooks",
  "newrelic.lib",
  "newrelic.lib.sqlparse",
  "newrelic.lib.sqlparse.engine",
  "newrelic.scripts",
]

setup(
  name = "newrelic",
  version = package_version,
  description = "Python agent for New Relic",
  author = "New Relic",
  author_email = "support@newrelic.com",
  license = copyright,
  url = "http://www.newrelic.com",
  packages = packages,
  extra_path = ("newrelic", "newrelic-%s" % package_version),
)