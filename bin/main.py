#!/usr/bin/env python3

import logging
import configargparse
from chargestop.client import Client
from chargestop.driver import Driver
logger = logging.getLogger(__name__)

def main():
    parser = configargparse.ArgParser(description="Save money by stopping ChargePoint sessions if it appears that your car is done charging")
    parser.add_argument("-c", "--config-file", is_config_file=True, help='config file path')
    parser.add_argument("-u", "--username", required='True', help='chargepoint username')
    parser.add_argument("-p", "--password", required='True', help='chargepoint password')
    parser.add_argument("--company-name-whitelist", nargs='+', help="if specified, charging will only be stopped if the charger's company name is in the list")
    parser.add_argument("-v", "--verbose", action='store_true', help='enable debug-level logging (may output passwords)')
    args = parser.parse_args()

    # Log to stdout
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s : %(message)s"
    )

    client = Client(
        username=args.username,
        password=args.password
    )
    driver = Driver(
        client=client,
        company_name_whitelist=args.company_name_whitelist
    )
    driver.run()

if __name__ == '__main__':
    main()
