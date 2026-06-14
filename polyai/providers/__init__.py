from polyai.providers.base import BaseProvider
from polyai.providers.ovhcloud import OVHcloudProvider
from polyai.providers.pollinations import PollinationsProvider
from polyai.providers.mlvoca import MlvocaProvider
from polyai.providers.devtoolbox import DevToolboxProvider

PROVIDER_REGISTRY: dict = {
    "ovhcloud": OVHcloudProvider,
    "pollinations": PollinationsProvider,
    "mlvoca": MlvocaProvider,
    "devtoolbox": DevToolboxProvider,
}

__all__ = [
    "BaseProvider",
    "OVHcloudProvider",
    "PollinationsProvider",
    "MlvocaProvider",
    "DevToolboxProvider",
    "PROVIDER_REGISTRY",
]
