import re
import sys

from unittest import mock

import ansible
import pytest

from pkg_resources import parse_version

from pytest_ansible.has_version import has_ansible_v28


try:
    from _pytest.main import EXIT_INTERRUPTED  # type: ignore[attr-defined]
    from _pytest.main import EXIT_NOTESTSCOLLECTED  # type: ignore[attr-defined]
    from _pytest.main import EXIT_OK  # type: ignore[attr-defined]
    from _pytest.main import EXIT_TESTSFAILED  # type: ignore[attr-defined]
    from _pytest.main import EXIT_USAGEERROR  # type: ignore[attr-defined]
except ImportError:
    from _pytest.main import ExitCode

    EXIT_OK = ExitCode.OK
    EXIT_TESTSFAILED = ExitCode.TESTS_FAILED
    EXIT_USAGEERROR = ExitCode.USAGE_ERROR
    EXIT_INTERRUPTED = ExitCode.INTERRUPTED
    EXIT_NOTESTSCOLLECTED = ExitCode.NO_TESTS_COLLECTED

if sys.version_info[0] == 2:
    import __builtin__ as builtins  # NOQA
else:
    import builtins  # NOQA


def test_plugin_help(testdir):
    """Verifies expected output from of py.test --help"""

    result = testdir.runpytest("--help")
    result.stdout.fnmatch_lines(
        [
            # Check for the github args section header
            "pytest-ansible:",
            # Check for the specific args
            "  --inventory=ANSIBLE_INVENTORY, --ansible-inventory=ANSIBLE_INVENTORY",
            "  --host-pattern=ANSIBLE_HOST_PATTERN, --ansible-host-pattern=ANSIBLE_HOST_PATTERN",
            "  --connection=ANSIBLE_CONNECTION, --ansible-connection=ANSIBLE_CONNECTION",
            "  --user=ANSIBLE_USER, --ansible-user=ANSIBLE_USER",
            "  --check, --ansible-check",
            "  --module-path=ANSIBLE_MODULE_PATH, --ansible-module-path=ANSIBLE_MODULE_PATH",
            "  --become, --ansible-become",
            "  --become-method=ANSIBLE_BECOME_METHOD, --ansible-become-method=ANSIBLE_BECOME_METHOD",
            "  --become-user=ANSIBLE_BECOME_USER, --ansible-become-user=ANSIBLE_BECOME_USER",
            "  --ask-become-pass=ANSIBLE_ASK_BECOME_PASS, --ansible-ask-become-pass=ANSIBLE_ASK_BECOME_PASS",
            # Check for the marker in --help
            "  ansible (args)*Ansible integration",
        ]
    )


def test_plugin_markers(testdir):
    """Verifies expected output from of py.test --markers"""

    result = testdir.runpytest("--markers")
    result.stdout.fnmatch_lines(
        [
            "@pytest.mark.ansible(*args): Ansible integration",
        ]
    )


def test_report_header(testdir, option):
    """Verify the expected ansible version in the pytest report header."""

    result = testdir.runpytest(*option.args)
    assert result.ret == EXIT_NOTESTSCOLLECTED
    result.stdout.fnmatch_lines(
        [
            "ansible: %s" % ansible.__version__,
        ]
    )


def test_params_not_required_when_not_using_fixture(testdir, option):
    """Verify the ansible parameters are not required if the fixture is not used."""

    src = """
        import pytest
        def test_func():
            assert True
    """
    testdir.makepyfile(src)
    result = testdir.runpytest(*option.args)
    assert result.ret == EXIT_OK


@pytest.mark.parametrize(
    "fixture_name",
    [
        "ansible_adhoc",
        "ansible_module",
        "ansible_facts",
    ],
)
def test_params_required_when_using_fixture(testdir, option, fixture_name):
    """Verify the ansible parameters are required if the fixture is used."""

    src = """
        import pytest
        def test_func({0}):
            {0}
    """.format(
        fixture_name
    )
    testdir.makepyfile(src)
    result = testdir.runpytest(*option.args)
    assert result.ret == EXIT_USAGEERROR
    result.stderr.fnmatch_lines(
        [
            "ERROR: Missing required parameter --ansible-host-pattern/--host-pattern",
        ]
    )


@pytest.mark.parametrize(
    "required_value_parameter",
    [
        "--ansible-inventory",
        "--inventory",
        "--ansible-host-pattern",
        "--host-pattern",
        "--ansible-connection",
        "--connection",
        "--ansible-user",
        "--user",
        "--ansible-become-method",
        "--become-method",
        "--ansible-become-user",
        "--become-user",
        "--ansible-module-path",
        "--module-path",
    ],
)
def test_param_requires_value(testdir, required_value_parameter):
    """Verifies failure when not providing a value to a parameter that requires a value"""

    result = testdir.runpytest(*[required_value_parameter])
    assert result.ret == EXIT_USAGEERROR
    result.stderr.fnmatch_lines(
        [
            "*: error: argument *%s*: expected one argument" % required_value_parameter,
        ]
    )


def test_params_required_with_inventory_without_host_pattern(testdir, option):
    """Verify that a host pattern is required when an inventory is supplied."""
    src = """
        import pytest
        def test_func(ansible_module):
            assert True
    """
    testdir.makepyfile(src)
    result = testdir.runpytest(*option.args + ["--ansible-inventory", "local,"])
    assert result.ret == EXIT_USAGEERROR
    result.stderr.fnmatch_lines(
        [
            "ERROR: Missing required parameter --ansible-host-pattern/--host-pattern",
        ]
    )


@pytest.mark.requires_ansible_v1
def test_params_required_with_bogus_inventory_v1(testdir, option):
    src = """
        import pytest
        def test_func(ansible_module):
            assert True
    """
    testdir.makepyfile(src)
    with mock.patch("os.path.exists", return_value=False) as mock_exists:
        result = testdir.runpytest(
            *["--ansible-inventory", "bogus", "--ansible-host-pattern", "all"]
        )

    # Assert py.test exit code
    assert result.ret == EXIT_TESTSFAILED

    # Assert expected error output
    result.stdout.fnmatch_lines(
        [
            "*Unable to find an inventory file, specify one with -i ?",
        ]
    )

    # Assert mock open called on provided file
    mock_exists.assert_any_call("bogus")


@pytest.mark.skipif(
    parse_version(ansible.__version__) < parse_version("2.0.0")
    or parse_version(ansible.__version__) >= parse_version("2.4.0"),
    reason="requires ansible >= 2.0 and < 2.4",
)
def test_params_required_with_bogus_inventory_v2(testdir, option, recwarn):
    src = """
        import pytest
        def test_func(ansible_module):
            with pytest.warns(UserWarning, match="provided hosts list is empty, only localhost is available"):
                ansible_module.ping()
    """
    testdir.makepyfile(src)

    with mock.patch(
        "ansible.parsing.dataloader.DataLoader.path_exists", return_value=False
    ) as mock_exists:
        result = testdir.runpytest(
            *[
                "-vvvvvs",
                "--ansible-inventory",
                "bogus",
                "--ansible-host-pattern",
                "all",
            ]
        )

    # Assert py.test exit code
    assert result.ret == EXIT_OK

    # Assert mock open called on provided file
    mock_exists.assert_any_call("bogus")


@pytest.mark.requires_ansible_v24
@pytest.mark.skipif(has_ansible_v28, reason="requires ansible < 2.8")
def test_params_required_with_bogus_inventory_v24(testdir, option, recwarn):
    src = """
        import pytest
        def test_func(ansible_module):
            with pytest.warns(UserWarning) as record:
                ansible_module.ping()
            # Ensure at least one warning in the queue
            assert len(record) >= 1
            # Ensure the latest warning is the ansible localhost warning
            assert record[0].message.args[0] == "provided hosts list is empty, only localhost is available"

    """
    testdir.makepyfile(src)

    result = testdir.runpytest(
        *["-vvvvvs", "--ansible-inventory", "bogus", "--ansible-host-pattern", "all"]
    )

    # Assert py.test exit code
    assert result.ret == EXIT_OK

    # There appear to be '\n' newline characters within the output.  Using the join on errlines flattens the string for
    # easier comparison.
    assert re.search(
        r"Unable to parse .*/bogus as an inventory source", " ".join(result.errlines)
    )


@pytest.mark.requires_ansible_v1
def test_params_required_without_inventory_with_host_pattern_v1(testdir, option):
    src = """
        import pytest
        def test_func(ansible_module):
            assert True
    """
    testdir.makepyfile(src)
    result = testdir.runpytest(*option.args + ["--ansible-host-pattern", "all"])
    assert result.ret == EXIT_TESTSFAILED
    result.stdout.fnmatch_lines(
        [
            "*Unable to find an inventory file, specify one with -i ?",
        ]
    )


@pytest.mark.requires_ansible_v2
def test_params_required_without_inventory_with_host_pattern_v2(testdir, option):
    src = """
        import pytest
        def test_func(ansible_module):
            assert True
    """
    testdir.makepyfile(src)
    result = testdir.runpytest(*option.args + ["--ansible-host-pattern", "all"])
    assert result.ret == EXIT_OK

    # TODO - validate the following warning message
    # [WARNING]: provided hosts list is empty, only localhost is available
    if False:
        result.stderr.fnmatch_lines(
            [
                "*[WARNING]: Host file not found: /etc/ansible/hosts*",
                "*provided hosts list is empty, only localhost is available",
            ]
        )


def test_param_override_with_marker(testdir):
    src = """
        import pytest
        @pytest.mark.ansible(inventory='local,', connection='local', host_pattern='all')
        def test_func(ansible_module):
            ansible_module.ping()
    """
    testdir.makepyfile(src)
    result = testdir.runpytest(
        *[
            "-vvvvvs",
            "--tb",
            "native",
            "--ansible-inventory",
            "garbage,",
            "--ansible-host-pattern",
            "garbage",
            "--ansible-connection",
            "garbage",
        ]
    )
    assert result.ret == EXIT_OK

    # Mock assert the correct variables are set
