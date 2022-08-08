import logging

import pytest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s test %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("ambassador")

from ambassador import IR, Config, EnvoyConfig
from ambassador.fetch import ResourceFetcher
from ambassador.utils import NullSecretHandler
from tests.utils import default_listener_manifests


def _get_envoy_config(yaml):
    aconf = Config()
    fetcher = ResourceFetcher(logger, aconf)
    fetcher.parse_yaml(default_listener_manifests() + yaml, k8s=True)

    aconf.load_all(fetcher.sorted())

    secret_handler = NullSecretHandler(logger, None, None, "0")

    ir = IR(aconf, file_checker=lambda path: True, secret_handler=secret_handler)

    assert ir

    return EnvoyConfig.generate(ir)


@pytest.mark.compilertest
def test_set_server_header_transformation():
    yaml = """
---
apiVersion: getambassador.io/v3alpha1
kind: Module
metadata:
  name: ambassador
  namespace: default
spec:
  config:
    server_header_transformation: PASS_THROUGH
---
apiVersion: getambassador.io/v3alpha1
kind: Mapping
metadata:
  name: ambassador
  namespace: default
spec:
  hostname: "*"
  prefix: /test/
  service: test:9999
"""
    econf = _get_envoy_config(yaml)
    expected = 96
    key_found = False

    conf = econf.as_dict()

    for listener in conf["static_resources"]["listeners"]:
        for filter_chain in listener["filter_chains"]:
            for f in filter_chain["filters"]:
                server_header_xform = f["typed_config"].get("server_header_transformation", None)
                assert (
                    server_header_xform is not None
                ), f"server_header_transformation not found on typed_config: {f['typed_config']}"

                print(f"Found server_header_transformation = {server_header_xform}")
                key_found = True
                assert expected == int(
                    server_header_xform
                ), "server_header_transformation must equal the value set on the ambassador Module"
    assert key_found, "server_header_transformation must be found in the envoy config"


@pytest.mark.compilertest
def test_set_max_request_header_v3():
    yaml = """
---
apiVersion: getambassador.io/v3alpha1
kind: Module
metadata:
  name: ambassador
  namespace: default
spec:
  config:
    server_header_transformation: PASS_THROUGH
---
apiVersion: getambassador.io/v3alpha1
kind: Mapping
metadata:
  name: ambassador
  namespace: default
spec:
  hostname: "*"
  prefix: /test/
  service: test:9999
"""
    econf = _get_envoy_config(yaml)
    expected = 96
    key_found = False

    conf = econf.as_dict()

    for listener in conf["static_resources"]["listeners"]:
        for filter_chain in listener["filter_chains"]:
            for f in filter_chain["filters"]:
                server_header_xform = f["typed_config"].get("server_header_transformation", None)
                assert (
                    server_header_xform is not None
                ), f"server_header_transformation not found on typed_config: {f['typed_config']}"

                print(f"Found server_header_transformation = {server_header_xform}")
                key_found = True
                assert expected == str(
                    server_header_xform
                ), "server_header_transformation must equal the value set on the ambassador Module"
    assert key_found, "server_header_transformation must be found in the envoy config"
