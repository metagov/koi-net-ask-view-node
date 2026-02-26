from rid_lib.types import KoiNetNode
from koi_net.config.full_node import (
    FullNodeConfig, 
    KoiNetConfig, 
    ServerConfig, 
    NodeProfile, 
    NodeProvides
)


class MyNodeConfig(FullNodeConfig):
    koi_net: KoiNetConfig = KoiNetConfig(
        node_name="my-node-name",   # human readable name for your node
        node_profile=NodeProfile(
            provides=NodeProvides(
                event=[],   # RID types of provided events
                state=[]    # RID types of provided state
            )
        ),
        rid_types_of_interest=[KoiNetNode] # RID types this node should subscribe to
    )