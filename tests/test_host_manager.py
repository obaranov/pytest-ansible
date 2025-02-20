import pytest

from ansible.errors import AnsibleError
from conftest import ALL_HOSTS
from conftest import NEGATIVE_HOST_PATTERNS
from conftest import NEGATIVE_HOST_SLICES
from conftest import POSITIVE_HOST_PATTERNS
from conftest import POSITIVE_HOST_SLICES


pytestmark = [
    pytest.mark.unit,
]


def test_len(hosts):
    assert len(hosts) == len(ALL_HOSTS)


def test_keys(hosts):
    sorted_keys = hosts.keys()
    sorted_keys.sort()
    assert sorted_keys == ALL_HOSTS


@pytest.mark.parametrize("host_pattern, num_hosts", POSITIVE_HOST_PATTERNS)
def test_contains(host_pattern, num_hosts, hosts):
    assert host_pattern in hosts, "{0} not in hosts".format(host_pattern)


@pytest.mark.parametrize("host_pattern, num_hosts", NEGATIVE_HOST_PATTERNS)
def test_not_contains(host_pattern, num_hosts, hosts):
    assert host_pattern not in hosts


@pytest.mark.parametrize("host_pattern, num_hosts", POSITIVE_HOST_PATTERNS)
def test_getitem(host_pattern, num_hosts, hosts):
    assert hosts[host_pattern]


@pytest.mark.parametrize("host_pattern, num_hosts", NEGATIVE_HOST_PATTERNS)
def test_not_getitem(host_pattern, num_hosts, hosts):
    with pytest.raises(KeyError):
        assert hosts[host_pattern]


@pytest.mark.parametrize("host_pattern, num_hosts", POSITIVE_HOST_PATTERNS)
def test_getattr(host_pattern, num_hosts, hosts):
    assert hasattr(hosts, host_pattern)


@pytest.mark.parametrize("host_slice, num_hosts", POSITIVE_HOST_SLICES)
def test_slice(host_slice, num_hosts, hosts):
    assert len(hosts[host_slice]) == num_hosts, "%s != %s for %s" % (
        len(hosts[host_slice]),
        num_hosts,
        host_slice,
    )


@pytest.mark.parametrize("host_slice", NEGATIVE_HOST_SLICES)
def test_not_slice(host_slice, hosts):
    with pytest.raises(KeyError):
        hosts[host_slice]


@pytest.mark.parametrize("host_pattern, num_hosts", NEGATIVE_HOST_PATTERNS)
def test_not_getattr(host_pattern, num_hosts, hosts):
    assert not hasattr(hosts, host_pattern)
    with pytest.raises(AttributeError):
        getattr(hosts, host_pattern)


# This should probably be made more generic for all options (and moved elsewhere)
@pytest.mark.ansible_v1_xfail(raises=AnsibleError)
def test_defaults(request):
    from ansible.constants import DEFAULT_TRANSPORT

    plugin = request.config.pluginmanager.getplugin("ansible")
    hosts = plugin.initialize(config=request.config, request=request)

    # from pytest_ansible.host_manager import get_host_manager
    # hosts = get_host_manager(inventory='unknown.example.com,')
    assert "connection" in hosts.options
    assert hosts.options["connection"] == DEFAULT_TRANSPORT
