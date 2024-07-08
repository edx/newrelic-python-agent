This forked version of ``newrelic`` is for temporary use by 2U.

Developing in devstack:

- Branch off of ``2u/no-report`` and make edits
- Build a package with ``python setup.py --quiet sdist``
- ``cp dist/newrelic-*.tar.gz ../src/nr.tgz`` (or to wherever your ``/edx/src`` mounts)
- Install inside lms-shell with ``pip install /edx/src/nr.tgz``

  - The usual ``pip install -e`` against a directory will not work with newrelic.
  - The version that pip sees will not match your version tag, but it should be OK. The important part is that the existing installation of newrelic is overwritten.

Release:

- Update the changelog on your branch
- Submit a PR and get your feature branch merged to ``2u/no-report``
- Tag the merge commit
- Get the commit ID
- In edx-internal ``ansible/vars/stage-edx.yml``, add this to ``EDXAPP_EXTRA_REQUIREMENTS``::

      # Forked version 9.11.0+twou-no-report.0
      - name: 'git+https://github.com/edx/newrelic-python-agent.git@<COMMIT_ID>#egg=newrelic'

  Include the version in the comment, not in the ``version`` field in the URL. (The package's internal version won't match the tag you created.)

To incorporate new NR agent releases, make a PR that merges the most recent official tag into ``2u/no-report`` and updates the changelog, and proceed with release as usual.
