import pytest


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


@pytest.mark.old
def test_contacted_with_params(testdir, option):
    """FIXME"""

    src = """
        import pytest
        def test_func(ansible_module):
            contacted = ansible_module.ping()

            # assert contacted hosts ...
            assert contacted
            assert len(contacted) == len(ansible_module)
            for result in contacted.values():
                assert result.is_successful
                assert result['ping'] == 'pong'

    """
    testdir.makepyfile(src)
    result = testdir.runpytest_subprocess(
        *option.args
        + [
            "--ansible-inventory",
            str(option.inventory),
            "--ansible-host-pattern",
            "local",
        ]
    )
    assert result.ret == EXIT_OK
    assert result.parseoutcomes()["passed"] == 1


@pytest.mark.old
def test_contacted_with_params_and_inventory_marker(testdir, option):
    """FIXME"""
    src = """
        import pytest
        @pytest.mark.ansible(inventory='%s')
        def test_func(ansible_module):
            contacted = ansible_module.ping()

            # assert contacted hosts ...
            assert contacted
            assert len(contacted) == len(ansible_module)
            for result in contacted.values():
                assert result.is_successful
                assert result['ping'] == 'pong'

    """ % str(
        option.inventory
    )
    testdir.makepyfile(src)
    result = testdir.runpytest_subprocess(
        *option.args + ["--ansible-host-pattern", "local"]
    )
    assert result.ret == EXIT_OK
    assert result.parseoutcomes()["passed"] == 1


@pytest.mark.old
def test_contacted_with_params_and_host_pattern_marker(testdir, option):
    """FIXME"""
    src = """
        import pytest
        @pytest.mark.ansible(host_pattern='local')
        def test_func(ansible_module):
            contacted = ansible_module.ping()

            # assert contacted hosts ...
            assert contacted
            assert len(contacted) == len(ansible_module)
            for result in contacted.values():
                assert result.is_successful
                assert result['ping'] == 'pong'

    """
    testdir.makepyfile(src)
    result = testdir.runpytest_subprocess(
        *option.args
        + [
            "--ansible-inventory",
            str(option.inventory),
            "--ansible-host-pattern",
            "unreachable",
        ]
    )
    assert result.ret == EXIT_OK
    assert result.parseoutcomes()["passed"] == 1


@pytest.mark.old
def test_contacted_with_params_and_inventory_host_pattern_marker(testdir, option):
    """FIXME"""
    src = """
        import pytest
        @pytest.mark.ansible(inventory='%s', host_pattern='local')
        def test_func(ansible_module):
            contacted = ansible_module.ping()

            # assert contacted hosts ...
            assert contacted
            assert len(contacted) == len(ansible_module)
            for result in contacted.values():
                assert result.is_successful
                assert result['ping'] == 'pong'

    """ % str(
        option.inventory
    )
    testdir.makepyfile(src)
    result = testdir.runpytest_subprocess(
        *option.args
        + ["--ansible-inventory", "/dev/null", "--ansible-host-pattern", "unreachable"]
    )
    assert result.ret == EXIT_OK
    assert result.parseoutcomes()["passed"] == 1


@pytest.mark.old
def test_become(testdir, option):
    """Test --ansible-become* parameters.  This test doesn't actually 'sudo',
    but verifies that 'sudo' was attempted by asserting
    '--ansible-become-user' fails as expected.
    """
    src = """
        import pytest
        import ansible
        import re
        import os
        from pkg_resources import parse_version

        @pytest.mark.ansible(inventory='%s', host_pattern='localhost')
        def test_func(ansible_module):
            contacted = ansible_module.ping()
            # assert contacted hosts ...
            assert contacted
            assert len(contacted) == len(ansible_module)
            for result in contacted.values():
                # Assert test failed as expected
                if parse_version(ansible.__version__) < parse_version('2.4.0'):
                    assert 'failed' in result, "Missing expected field in JSON response: failed"
                    assert result['failed'], "Test did not fail as expected"

                # Assert expected failure message
                if parse_version(ansible.__version__) >= parse_version('2.0.0'):
                    assert 'msg' in result, "Missing expected field in JSON response: msg"
                    assert result['msg'].startswith('Failed to set permissions on the temporary files Ansible needs ' \
                        'to create when becoming an unprivileged user')
                else:
                    assert 'msg' in result, "Missing expected field in JSON response: msg"
                    assert 'sudo: unknown user: asdfasdf' in result['msg']
    """ % str(
        option.inventory
    )
    testdir.makepyfile(src)
    result = testdir.runpytest_subprocess(
        *option.args
        + [
            "--ansible-inventory",
            str(option.inventory),
            "--ansible-host-pattern",
            "localhost",  # run against a single host
            "--ansible-become",  # Enable become support
            "--ansible-become-user",
            "asdfasdf",  # Connect as asdfasdf
        ]
    )
    assert result.ret == EXIT_OK
    assert result.parseoutcomes()["passed"] == 1


@pytest.mark.old
def test_dark_with_params(testdir, option):
    """FIXME"""
    src = """
        import pytest
        from pytest_ansible.errors import (AnsibleConnectionFailure, AnsibleNoHostsMatch)
        def test_func(ansible_module):
            exc_info = pytest.raises(AnsibleConnectionFailure, ansible_module.ping)

            # assert no contacted hosts ...
            assert not exc_info.value.contacted, "%d hosts were contacted, expected %d" \
                % (len(exc_info.value.contacted), 0)

            # assert dark hosts ...
            assert exc_info.value.dark
    """
    testdir.makepyfile(src)
    result = testdir.runpytest_subprocess(
        *option.args
        + [
            "--ansible-inventory",
            str(option.inventory),
            "--ansible-host-pattern",
            "unreachable",
        ]
    )
    print("\n".join(result.stdout.lines))
    print("\n".join(result.stderr.lines))
    assert result.ret == EXIT_OK
    assert result.parseoutcomes()["passed"] == 1


@pytest.mark.old
def test_dark_with_params_and_inventory_marker(testdir, option):
    """FIXME"""
    src = """
        import pytest
        from pytest_ansible.errors import (AnsibleConnectionFailure, AnsibleNoHostsMatch)
        @pytest.mark.ansible(inventory='{inventory}')
        def test_func(ansible_module):
            exc_info = pytest.raises(AnsibleConnectionFailure, ansible_module.ping)

            # assert no contacted hosts ...
            assert not exc_info.value.contacted, "%d hosts were contacted, expected %d" \
                % (len(exc_info.value.contacted), 0)

            # assert dark hosts ...
            assert exc_info.value.dark
    """.format(
        inventory=str(option.inventory)
    )
    testdir.makepyfile(src)
    result = testdir.runpytest_subprocess(
        *option.args + ["--ansible-host-pattern", "unreachable"]
    )
    assert result.ret == EXIT_OK
    assert result.parseoutcomes()["passed"] == 1


@pytest.mark.old
def test_dark_with_params_and_host_pattern_marker(testdir, option):
    """FIXME"""
    src = """
        import pytest
        import ansible
        from pytest_ansible.errors import (AnsibleConnectionFailure, AnsibleNoHostsMatch)
        @pytest.mark.ansible(host_pattern='unreachable')
        def test_func(ansible_module):
            exc_info = pytest.raises(AnsibleConnectionFailure, ansible_module.ping)

            # assert no contacted hosts ...
            assert not exc_info.value.contacted, "%d hosts were contacted, expected %d" \
                % (len(exc_info.value.contacted), 0)

            # assert dark hosts ...
            assert exc_info.value.dark
    """
    testdir.makepyfile(src)
    result = testdir.runpytest_subprocess(
        *option.args
        + [
            "--ansible-inventory",
            str(option.inventory),
            "--ansible-host-pattern",
            "local",
        ]
    )
    assert result.ret == EXIT_OK
    assert result.parseoutcomes()["passed"] == 1


@pytest.mark.old
def test_dark_with_debug_enabled(testdir, option):
    """Verify that when verbosity is enabled, additional output is provided upon host failure."""
    src = """
        import pytest
        from pytest_ansible.errors import AnsibleConnectionFailure
        def test_func(ansible_module):
            ansible_module.ping()
    """
    testdir.makepyfile(src)
    result = testdir.runpytest_subprocess(
        *option.args
        + [
            "--ansible-inventory",
            str(option.inventory),
            "--ansible-host-pattern",
            "unreachable",
            "-v",
        ]
    )
    assert result.ret == EXIT_TESTSFAILED
    assert result.parseoutcomes()["failed"] == 1
    # FIXME - the following doesn't work on ansible-v2
    # result.stdout.fnmatch_lines([
    #     '*ESTABLISH CONNECTION FOR USER: *',
    #     '*REMOTE_MODULE ping',
    #     '*EXEC ssh *',
    # ])
