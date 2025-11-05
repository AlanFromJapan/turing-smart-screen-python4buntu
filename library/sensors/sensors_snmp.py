import os
import threading
import time
import asyncio
import json
from pysnmp.hlapi.v1arch.asyncio import *

import library.sensors.sensors as sensors
from library.log import logger

__config = None

def initialize_snmp(config_file_path: str = "config/snmp_config.json") -> bool:
    """ Initialize any SNMP config . """
    global __config
    if not os.path.exists(config_file_path):
        logger.error(f"SNMP config file not found: {config_file_path}")
        return False

    with open(config_file_path, "r") as f:
        __config = json.load(f)
        # Initialize SNMP settings from config
        # sensors.snmp_host = __config.get("snmp_host", "localhost")
        # sensors.snmp_community = __config.get("snmp_community", "public")
        # sensors.snmp_port = __config.get("snmp_port", 161)

    return True


def get_snmp_wellknown(host_nickname: str, oid_descr: str):
    """ Get SNMP value for a well-known host and OID Description from config. """
    global __config
    if __config is None:
        logger.error("SNMP not initialized. Call initialize_snmp() first.")
        return False, None

    host_info = next((server for server in __config.get("servers", []) if server.get("nickname") == host_nickname), None)
    if not host_info:
        logger.error(f"Host nickname '{host_nickname}' not found in config.")
        return False, None

    oid = next((oid for oid in host_info.get("oids", []) if oid.get("description") == oid_descr), None)
    if not oid:
        logger.error(f"OID description '{oid_descr}' not found for host '{host_nickname}'.")
        return False, None

    result, value = get_snmp(
        host=host_info.get("server"),
        oid=oid.get("oid"),
        port=host_info.get("port", 161),
        community=host_info.get("community", "public"),
        dyn_check=oid.get("dyn_check")
    )

    # Post-process the value if needed
    if oid.get("post_process"):
        try:
            local_vars = {'value': value}
            check = "value = " + oid.get("post_process")
            exec(check, {}, local_vars)
            value = local_vars['value']
        except Exception as e:
            logger.error(f"Error in post-processing SNMP value: {e} on OID '{oid_descr}' for host '{host_nickname}'")
            return False, None

    return result, value


def get_snmp(host: str, oid: str, port: int = 161, community: str = "public", dyn_check:str= None):
    """ Wrapper to run the async SNMP GET in a sync way. """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(__snmp_get(host, oid, port, community, dyn_check))
    loop.close()
    return result


async def __snmp_get(host: str, oid: str, port: int = 161, community: str = "public", dyn_check:str= None):
    """ Perform an SNMP GET request asynchronously. """
    with SnmpDispatcher() as snmpDispatcher:
        iterator = await get_cmd(
            snmpDispatcher,
            CommunityData(community, mpModel=0),
            await UdpTransportTarget.create((host, port)),
            (oid, None),
        )

        errorIndication, errorStatus, errorIndex, varBinds = iterator

        if errorIndication:
            logger.error(f"SNMP error indication: {errorIndication}")
            return False, None

        elif errorStatus:
            logger.error(
                "{} at {}".format(
                    errorStatus.prettyPrint(),
                    errorIndex and varBinds[int(errorIndex) - 1][0] or "?",
                )
            )
            return False, None
        else:
            for varBind in varBinds:
                logger.debug(" = ".join([x.prettyPrint() for x in varBind]))

                # Dynamic exec of code to check value True/False
                if dyn_check:
                    try:
                        check = "response = True if " + dyn_check + " else False"
                        local_vars = {'response': None, 'value': varBind[1].prettyPrint()}
                        exec(check, {}, local_vars)
                        response = local_vars['response']
                        logger.debug(f"Dynamic check '{dyn_check}' evaluated to {response}")
                        if not response:
                            return False, varBind[1].prettyPrint()
                        else:
                            return True, varBind[1].prettyPrint()

                    except ValueError:
                        logger.error(f"Invalid dynamic check value: {dyn_check}")
                        return False, None
                else:
                    return True, varBind[1].prettyPrint()
    return False, None