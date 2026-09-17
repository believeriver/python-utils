import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.switch import Switch


def test_get_or_create_and_fetch():
    sw = Switch.get_or_create(
        hostname="sw-3f-edge-01",
        ip_address="192.168.10.11",
        hardware_model="C2960L",
        switch_type="L2",
        role="edge",
        location="3F 北側",
        data_vlan=110,
    )
    print("created/updated:", sw.id, sw.hostname, sw.location)

    active = Switch.fetch_all_active()
    print("active switches:", active)

    one = Switch.fetch_by_hostname("sw-3f-edge-01")
    print("fetched one:", one)


if __name__ == "__main__":
    test_get_or_create_and_fetch()