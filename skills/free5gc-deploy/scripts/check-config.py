#!/usr/bin/env python3
"""Read-only consistency check for common single-UPF free5GC YAML schemas."""

import argparse
import ipaddress
import json
from pathlib import Path
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("Missing PyYAML; install python3-yaml and use /usr/bin/python3.")


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
    require(len(up_nodes) == 1, "This checker supports exactly one UPF; inspect other topologies manually")
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
    parser.add_argument("config_dir", type=Path)
    parser.add_argument("--allow-loopback", action="store_true",
                        help="Only for an explicitly chosen local RAN topology")
    args = parser.parse_args()
    try:
        documents = []
        for name in ("amfcfg.yaml", "smfcfg.yaml", "upfcfg.yaml"):
            with (args.config_dir / name).open() as stream:
                # BaseLoader keeps identifiers like 010203 and 000001 as strings.
                documents.append(yaml.load(stream, Loader=yaml.BaseLoader))
        result = check_config(*documents, allow_loopback=args.allow_loopback)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, yaml.YAMLError) as exc:
        result = {"status": "FAIL", "error": str(exc),
                  "action": "Inspect the selected release schema and configuration; no files were changed"}
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
