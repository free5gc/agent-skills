#!/usr/bin/env python3
"""Read-only consistency check for common single-UPF free5GC YAML schemas."""

import argparse
import ipaddress
from pathlib import Path
import re
import sys

try:
    import yaml
except ImportError:
    print("UNAVAILABLE [config] Python3/PyYAML required; no YAML fallback")
    sys.exit(2)


class UnsupportedSchema(Exception):
    """Selected topology is outside this checker's scope."""


class UniqueLoader(yaml.BaseLoader):
    """Keep identifier widths and reject YAML duplicate keys."""


def unique_mapping(loader, node):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in mapping:
            raise ValueError("duplicate YAML key")
        mapping[key] = loader.construct_object(value_node)
    return mapping


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def ipv4(value, name, allow_loopback=False, allow_any=False):
    address = ipaddress.IPv4Address(value)
    require(not address.is_multicast and str(address) != "255.255.255.255",
            f"{name} must be a unicast address")
    require(allow_any or not address.is_unspecified, f"{name} cannot advertise 0.0.0.0")
    require(allow_loopback or not address.is_loopback,
            f"{name} is loopback; configure a gNB-reachable address")
    return str(address)


def slice_key(value):
    sst = int(value["sst"])
    sd = value.get("sd", "")
    require(0 <= sst <= 255, "SST must be between 0 and 255")
    require(not sd or re.fullmatch(r"[0-9a-fA-F]{6}", sd), "SD must preserve six hex digits")
    return sst, sd.lower()


def check_config(amf, smf, upf, allow_loopback=False):
    amf = amf["configuration"]
    smf = smf["configuration"]
    n2 = [ipv4(addr, "AMF N2", allow_loopback) for addr in amf["ngapIpList"]]
    require(n2, "AMF needs an N2 address")
    supported_slices = set()
    plmns = []
    for item in amf["plmnSupportList"]:
        plmn = item["plmnId"]
        require(re.fullmatch(r"\d{3}", plmn["mcc"]) and
                re.fullmatch(r"\d{2,3}", plmn["mnc"]), "Preserve MCC/MNC string widths")
        plmns.append(plmn)
        supported_slices.update(slice_key(value) for value in item["snssaiList"])
    for tai in amf["supportTaiList"]:
        require(tai["plmnId"] in plmns, "TAI PLMN is not supported")
        require(re.fullmatch(r"[0-9a-fA-F]{6}", tai["tac"]), "TAC must be six hex digits")
    amf_dnns = set(amf["supportDnnList"])
    offered = set()
    for item in smf["snssaiInfos"]:
        snssai = slice_key(item["sNssai"])
        require(snssai in supported_slices, f"SMF slice {snssai} is absent from AMF")
        for info in item["dnnInfos"]:
            dnn = info["dnn"]
            require(dnn in amf_dnns, f"SMF DNN {dnn} is absent from AMF")
            offered.add((snssai, dnn))
    require(offered, "SMF offers no slice/DNN")

    topology = smf["userplaneInformation"]
    up_nodes = [(name, node) for name, node in topology["upNodes"].items()
                if node["type"] == "UPF"]
    if len(up_nodes) != 1:
        raise UnsupportedSchema()
    upf_name, node = up_nodes[0]
    an_names = {name for name, item in topology["upNodes"].items() if item["type"] == "AN"}
    require(any((link["A"] == upf_name and link["B"] in an_names) or
                (link["B"] == upf_name and link["A"] in an_names)
                for link in topology["links"]), "SMF topology has no AN-to-UPF link")
    require(node["nodeID"] == upf["pfcp"]["nodeID"], "SMF/UPF PFCP nodeID mismatch")
    require(node["addr"] == upf["pfcp"]["addr"], "SMF/UPF PFCP address mismatch")

    listeners = {ipv4(item["addr"], "UPF N3", allow_loopback, allow_any=True)
                 for item in upf["gtpu"]["ifList"] if item.get("type") == "N3"}
    require(listeners, "UPF has no N3 listener")
    endpoints = set()
    n3_dnns = set()
    for interface in node["interfaces"]:
        if interface["interfaceType"] == "N3":
            for address in interface["endpoints"]:
                address = ipv4(address, "SMF N3 endpoint", allow_loopback)
                require(address in listeners or "0.0.0.0" in listeners,
                        f"SMF N3 endpoint {address} does not match UPF listener")
                endpoints.add(address)
            n3_dnns.update(interface["networkInstances"])
    require(endpoints, "SMF advertises no N3 endpoint")

    upf_pools = {(item["dnn"], ipaddress.IPv4Network(item["cidr"])) for item in upf["dnnList"]}
    mapped = set()
    report = []
    for item in node["sNssaiUpfInfos"]:
        snssai = slice_key(item["sNssai"])
        for info in item["dnnUpfInfoList"]:
            dnn = info["dnn"]
            require((snssai, dnn) in offered, f"UPF mapping {snssai}/{dnn} is not offered by SMF")
            require(dnn in n3_dnns, f"DNN {dnn} is absent from N3 networkInstances")
            pools = [ipaddress.IPv4Network(pool["cidr"]) for pool in info["pools"]]
            require(pools, f"DNN {dnn} has no UE pool")
            for pool in pools:
                require(any(dnn == upf_dnn and pool.subnet_of(upf_pool)
                            for upf_dnn, upf_pool in upf_pools),
                        f"SMF pool {dnn}/{pool} is not covered by UPF dnnList")
            for static in info.get("staticPools", []):
                subnet = ipaddress.IPv4Network(static["cidr"])
                require(any(dnn == upf_dnn and subnet.subnet_of(upf_pool)
                            for upf_dnn, upf_pool in upf_pools),
                        f"Static pool {subnet} is not covered by UPF dnnList")
            mapped.add((snssai, dnn))
            report.append({"sst": snssai[0], "sd": snssai[1], "dnn": dnn,
                           "ue_pools": [str(pool) for pool in pools]})
    require(offered <= mapped, "An offered SMF slice/DNN has no UPF pool mapping")
    return {"status": "PASS", "n2_addresses": n2, "n2_port": int(amf.get("ngapPort", "38412")),
            "n3_endpoints": sorted(endpoints), "plmns": plmns,
            "tracking_areas": amf["supportTaiList"], "slice_dnns": report,
            "scope": "Static common-schema checks only; inspect host routing, NF readiness, and NSSF separately"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    args = parser.parse_args()
    try:
        documents = []
        for name in ("amfcfg.yaml", "smfcfg.yaml", "upfcfg.yaml"):
            path = args.repo / "config" / name
            try:
                size = path.stat().st_size
            except FileNotFoundError:
                size = None
            if size is None:
                print("FAIL [config] required core YAML file missing")
                return 1
            if size > 1_000_000:
                print("UNKNOWN [config] configuration exceeds bounded parser scope")
                return 2
            with path.open() as stream:
                documents.append(yaml.load(stream, Loader=UniqueLoader))
        check_config(*documents, allow_loopback=True)
    except PermissionError:
        print("UNKNOWN [config] permission denied")
        return 2
    except (UnsupportedSchema, KeyError, TypeError, AttributeError):
        print("UNKNOWN [config] unsupported/incomplete schema; inspect selected version")
        return 2
    except (ValueError, yaml.YAMLError):
        # Exceptions can contain config values; do not disclose them.
        print("FAIL [config] invalid YAML or proven static configuration mismatch; inspect privately")
        return 1
    except OSError:
        print("UNKNOWN [config] files not observable")
        return 2
    print("PASS [config] common single-UPF static consistency; runtime/NSSF/subscriber not checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
