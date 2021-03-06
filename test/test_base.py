# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os.path
import difflib
import glob
import os.path

from .common import BaseGitReposTest, BaseTmpDirTest, w, cmd
from gitchangelog.gitchangelog import indent


class GitChangelogTest(BaseGitReposTest):
    """Base for all tests needing to start in a new git small repository"""

    REFERENCE = r"""Changelog
=========


%%version%% (unreleased)
------------------------

Changes
~~~~~~~
- Modified ``b`` XXX. [Alice, Charly, Juliet]


0.0.3 (2000-01-05)
------------------

New
~~~
- Add file ``e``, modified ``b`` [Bob]

  This is a message body.

  With multi-line content:
  - one
  - two
- Add file ``c`` [Charly]


0.0.2 (2000-01-02)
------------------
- Add ``b`` with non-ascii chars éèàâ§µ and HTML chars ``&<`` [Alice]


"""

    INCR_REFERENCE_002_003 = r"""0.0.3 (2000-01-05)
------------------

New
~~~
- Add file ``e``, modified ``b`` [Bob]

  This is a message body.

  With multi-line content:
  - one
  - two
- Add file ``c`` [Charly]


"""

    def setUp(self):
        super(GitChangelogTest, self).setUp()

        w(r"""

            ## Adding first file
            echo 'Hello' > a
            git add a
            git commit -m 'new: first commit' \
                --author 'Bob <bob@example.com>' \
                --date '2000-01-01 10:00:00'
            git tag 0.0.1

            ## Adding second file
            echo 'Second file with strange non-ascii char: éèàâ§µ' > b
            git add b

            ## Notice there are no section here.
            git commit -m 'add ``b`` with non-ascii chars éèàâ§µ and HTML chars ``&<``

Change-Id: Ic8aaa0728a43936cd4c6e1ed590e01ba8f0fbf5b' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-02 11:00:00'
            git tag 0.0.2

            ## Adding more files
            echo 'Third file' > c
            git add c
            git commit -m 'new: add file ``c``' \
                --author 'Charly <charly@example.com>' \
                --date '2000-01-03 12:00:00'
            echo 'Fourth file' > d
            echo 'With a modification' >> b
            git add d b
            git commit -m 'new: add file ``e``, modified ``b``

This is a message body.

With multi-line content:
- one
- two

Bug: #42
Change-Id: Ic8aaa0728a43936cd4c6e1ed590e01ba8f0fbf5b
Signed-off-by: A. U. Thor <author@example.com>
CC: R. E. Viewer <reviewer@example.com>
Subject: This is a fake subject spanning to several lines
  as you can see
' \
                --author 'Bob <bob@example.com>' \
                --date '2000-01-04 13:00:00'

            echo 'minor addition 1' >> b
            git commit -am 'chg: modified ``b`` !minor' \
                --author 'Bob <bob@example.com>' \
                --date '2000-01-05 13:00:00'
            git tag 0.0.3

            ## Add untagged commits
            echo 'addition' >> b
            git commit -am 'chg: modified ``b`` XXX

Co-Authored-By: Juliet <juliet@example.com>
Co-Authored-By: Charly <charly@example.com>
' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-06 11:00:00'

            """)

    def test_simple_run_no_args_legacy_call(self):
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "0.0.2",
            msg="At least one of the tags should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            out, self.REFERENCE,
            msg="Should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(out.split("\n"),
                                             self.REFERENCE.split("\n"),
                                             lineterm="")))

    def test_simple_run_show_call_deprecated(self):
        out, err, errlvl = cmd('$tprog show')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertContains(
            err, "deprecated",
            msg="There should be a warning about deprecated calls. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "0.0.2",
            msg="At least one of the tags should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            out, self.REFERENCE,
            msg="Should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(out.split("\n"),
                                             self.REFERENCE.split("\n"),
                                             lineterm="")))

    def test_simple_with_changelog_python_exception(self):
        w("""

            cat <<EOF > .gitchangelog.rc

def raise_exc(data, opts):
    raise Exception('Test Exception XYZ')

output_engine = raise_exc

EOF

        """)

        out, err, errlvl = cmd('$tprog')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertContains(
            err, "--debug",
            msg="Message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should NOT contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_simple_show_with_changelog_python_exception_deprecated(self):
        w("""

            cat <<EOF > .gitchangelog.rc

def raise_exc(data, opts):
    raise Exception('Test Exception XYZ')

output_engine = raise_exc

EOF

        """)

        out, err, errlvl = cmd('$tprog show')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertContains(
            err, "--debug",
            msg="Message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "deprecated",
            msg="Message about show being deprecated... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should NOT contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_with_changelog_python_exc_in_cli_debug_mode(self):
        w("""

            cat <<EOF > .gitchangelog.rc

def raise_exc(data, opts):
    raise Exception('Test Exception XYZ')

output_engine = raise_exc

EOF

        """)

        out, err, errlvl = cmd('$tprog --debug')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_show_with_changelog_python_exc_in_cli_debug_mode_deprecated(self):
        w("""

            cat <<EOF > .gitchangelog.rc

def raise_exc(data, opts):
    raise Exception('Test Exception XYZ')

output_engine = raise_exc

EOF

        """)

        out, err, errlvl = cmd('$tprog --debug show')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "deprecated",
            msg="Should contain message about show being deprecated... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_with_changelog_python_exc_in_cli_debug_mode_after(self):
        w("""

            cat <<EOF > .gitchangelog.rc

def raise_exc(data, opts):
    raise Exception('Test Exception XYZ')

output_engine = raise_exc

EOF

        """)

        out, err, errlvl = cmd('$tprog HEAD --debug')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_show_with_changelog_python_exc_in_cli_debug_mode_after_deprecated(self):
        w("""

            cat <<EOF > .gitchangelog.rc

def raise_exc(data, opts):
    raise Exception('Test Exception XYZ')

output_engine = raise_exc

EOF

        """)

        out, err, errlvl = cmd('$tprog show --debug')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "deprecated",
            msg="Should contain message about show being deprecated... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_with_changelog_python_exc_in_env_debug_mode(self):
        w("""

            cat <<EOF > .gitchangelog.rc

def raise_exc(data, opts):
    raise Exception('Test Exception XYZ')

output_engine = raise_exc

EOF

        """)

        out, err, errlvl = cmd('DEBUG_GITCHANGELOG=1 $tprog')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_show_with_changelog_python_exc_in_env_debug_mode_deprecated(self):
        w("""

            cat <<EOF > .gitchangelog.rc

def raise_exc(data, opts):
    raise Exception('Test Exception XYZ')

output_engine = raise_exc

EOF

        """)

        out, err, errlvl = cmd('DEBUG_GITCHANGELOG=1 $tprog show')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "deprecated",
            msg="Should contain message about show being deprecated... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_incremental_call(self):
        out, err, errlvl = cmd('$tprog 0.0.2..0.0.3')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "0.0.3",
            msg="The tag 0.0.3 should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            out, self.INCR_REFERENCE_002_003,
            msg="Should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(
                out.split("\n"),
                self.INCR_REFERENCE_002_003.split("\n"),
                lineterm="")))

    def test_incremental_call_multirev(self):
        out, err, errlvl = cmd('$tprog ^0.0.2 0.0.3 0.0.3')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "0.0.3",
            msg="The tag 0.0.3 should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            out, self.INCR_REFERENCE_002_003,
            msg="Should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(
                out.split("\n"),
                self.INCR_REFERENCE_002_003.split("\n"),
                lineterm="")))

    def test_incremental_show_call_deprecated(self):
        out, err, errlvl = cmd('$tprog show 0.0.2..0.0.3')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertContains(
            err, "deprecated",
            msg="There should be a deprecated warning. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "0.0.3",
            msg="The tag 0.0.3 should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            out, self.INCR_REFERENCE_002_003,
            msg="Should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(
                out.split("\n"),
                self.INCR_REFERENCE_002_003.split("\n"),
                lineterm="")))

    def test_overriding_options(self):
        """We must be able to define a small gitchangelog.rc that adjust only
        one variable of all the builtin defaults."""

        w("""

            cat <<EOF > .gitchangelog.rc

tag_filter_regexp = r'^v[0-9]+\\.[0.9]$'

EOF
            git tag 'v7.0' HEAD^
            git tag 'v8.0' HEAD

        """)
        changelog = w('$tprog')
        self.assertContains(
            changelog, "v8.0",
            msg="At least one of the tags should be displayed in changelog... "
            "content of changelog:\n%s" % changelog)

    def test_reuse_options(self):
        """We must be able to define a small gitchangelog.rc that adjust only
        one variable of all the builtin defaults."""

        w("""cat <<EOF > .gitchangelog.rc

ignore_regexps += [r'XXX', ]

EOF
        """)
        changelog = w('$tprog')
        self.assertNotContains(
            changelog, "XXX",
            msg="Should not contain commit with XXX in it... "
            "content of changelog:\n%s" % changelog)
        self.assertContains(
            changelog, "dd file ``e``",
            msg="Should contain at least a message of other commits... "
            "content of changelog:\n%s" % changelog)
        self.assertNotContains(
            changelog, "!minor",
            msg="Shouldn't contain !minor tagged commit neither... "
            "content of changelog:\n%s" % changelog)

    def test_provided_config_file(self):
        """Check provided reference with older name for perfect same result."""

        config_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..")
        configs = glob.glob(os.path.join(config_dir,
                                         "gitchangelog.rc.reference.v*"))
        for config in configs:
            out, err, errlvl = cmd(
                'GITCHANGELOG_CONFIG_FILENAME="%s" $tprog' % config)
            self.assertEqual(
                errlvl, 0,
                msg="Should not fail with config %r " % (config, ) +
                "Current stderr:\n%s" % indent(err))
            self.assertEqual(
                out, self.REFERENCE,
                msg="config %r output should match our reference output... "
                "diff of changelogs:\n%s"
                % (config,
                   '\n'.join(difflib.unified_diff(
                   self.REFERENCE.split("\n"),
                   out.split("\n"),
                   lineterm=""))))

    def test_with_filename_same_as_tag(self):
        w("""

            touch 0.0.1

        """)
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail even if filename same as tag name.")
        self.assertEqual(
            err, "",
            msg="No error message expected. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            out, self.REFERENCE,
            msg="Should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(out.split("\n"),
                                             self.REFERENCE.split("\n"),
                                             lineterm="")))

    def test_include_merge_options(self):
        """We must be able to define a small gitchangelog.rc that adjust only
        one variable of all the builtin defaults."""

        w("""cat <<EOF > .gitchangelog.rc

include_merge = False

EOF

            git checkout -b develop
            git commit -m "made on develop branch" --allow-empty
            git checkout master
            git merge develop --no-ff

        """)
        changelog = w('$tprog')
        self.assertNotContains(
            changelog, "Merge",
            msg="Should not contain commit with 'Merge' in it... "
            "content of changelog:\n%s" % changelog)

    def test_same_output_with_different_engine(self):
        """Reference implementation should match mustache and mako implem"""

        w("""cat <<EOF > .gitchangelog.rc

output_engine = mustache('restructuredtext')

EOF
        """)
        changelog = w('$tprog')
        self.assertEqual(
            changelog, self.REFERENCE,
            msg="Mustache output should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(self.REFERENCE.split("\n"),
                                             changelog.split("\n"),
                                             lineterm="")))

        w("""cat <<EOF > .gitchangelog.rc

output_engine = makotemplate('restructuredtext')

EOF
        """)
        changelog = w('$tprog')
        self.assertEqual(
            changelog, self.REFERENCE,
            msg="Mako output should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(self.REFERENCE.split("\n"),
                                             changelog.split("\n"),
                                             lineterm="")))

    def test_same_output_with_different_engine_incr(self):
        """Reference implementation should match mustache and mako implem"""

        w("""cat <<EOF > .gitchangelog.rc

output_engine = mustache('restructuredtext')

EOF
        """)
        changelog = w('$tprog 0.0.2..0.0.3')
        self.assertEqual(
            changelog, self.INCR_REFERENCE_002_003,
            msg="Mustache output should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(self.INCR_REFERENCE_002_003.split("\n"),
                                             changelog.split("\n"),
                                             lineterm="")))

        w("""cat <<EOF > .gitchangelog.rc

output_engine = makotemplate('restructuredtext')

EOF
        """)
        changelog = w('$tprog 0.0.2..0.0.3')
        self.assertEqual(
            changelog, self.INCR_REFERENCE_002_003,
            msg="Mako output should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(self.INCR_REFERENCE_002_003.split("\n"),
                                             changelog.split("\n"),
                                             lineterm="")))

    def test_provided_templates(self):
        """Run all provided templates at least once"""

        for label, directory in [("makotemplate", "mako"),
                                 ("mustache", "mustache")]:
            template_dir = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "..", "templates", directory)
            templates = glob.glob(os.path.join(template_dir, "*.tpl"))
            template_labels = [os.path.basename(f).split(".")[0]
                               for f in templates]
            for tpl in template_labels:
                w("""cat <<EOF > .gitchangelog.rc

output_engine = %s(%r)

EOF
                """ % (label, tpl))
                out, err, errlvl = cmd('$tprog')
                self.assertEqual(
                    errlvl, 0,
                    msg="Should not fail on %s(%r) " % (label, tpl) +
                    "Current stderr:\n%s" % indent(err))

    def test_unexistent_template_name(self):
        """Unexisting template should get a proper error message"""

        w("""cat <<EOF > .gitchangelog.rc

output_engine = mustache('doesnotexist')

EOF
        """)
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            errlvl, 1,
            msg="Should fail as template does not exist")
        self.assertEqual(
            out, "",
            msg="No stdout was expected since there was an error. "
            "Current stdout:\n%r" % out)
        self.assertContains(
            err, "doesnotexist",
            msg="There should be an error message mentioning 'doesnotexist'. "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "restructuredtext",
            msg="The error message should mention 'available'. "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "mustache",
            msg="The error message should mention 'mustache'. "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "restructuredtext",
            msg="The error message should mention 'restructuredtext'. "
            "Current stderr:\n%s" % err)

    def test_file_template_name(self):
        """Existing files should be accepted as valid templates"""

        w("""
             cat <<EOF > mytemplate.tpl
check: {{{title}}}
EOF
             cat <<EOF > .gitchangelog.rc

output_engine = mustache('mytemplate.tpl')

EOF
        """)

        reference = """check: Changelog
"""

        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed to find template")
        self.assertEqual(
            out, reference,
            msg="Mako output should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(reference.split("\n"),
                                             out.split("\n"),
                                             lineterm="")))

    def test_template_as_access_to_full_commit(self):
        """Existing files should be accepted as valid templates"""

        w("""
             cat <<'EOF' > mytemplate.tpl
% for version in data["versions"]:
${version["tag"]}
% for section in version["sections"]:
  ${section["label"]}:
% for commit in section["commits"]:
    - ${commit["commit"].subject}
% endfor
% endfor
% endfor
EOF
             cat <<EOF > .gitchangelog.rc

output_engine = makotemplate('mytemplate.tpl')

EOF
        """)

        reference = """\
None
  Changes:
    - chg: modified ``b`` XXX
0.0.3
  New:
    - new: add file ``e``, modified ``b``
    - new: add file ``c``
0.0.2
  Other:
    - add ``b`` with non-ascii chars \xe9\xe8\xe0\xe2\xa7\xb5 and HTML chars ``&<``
"""

        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed to find template")
        self.assertEqual(
            out, reference,
            msg="Mako output should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(reference.split("\n"),
                                             out.split("\n"),
                                             lineterm="")))


