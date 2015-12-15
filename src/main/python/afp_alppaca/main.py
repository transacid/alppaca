from __future__ import print_function, absolute_import, unicode_literals, division

import sys

from afp_alppaca.assume_role import AssumedRoleCredentialsProvider
from afp_alppaca.ims_interface import IMSCredentialsProvider
from afp_alppaca.scheduler import Scheduler
from afp_alppaca.webapp import WebApp
from afp_alppaca.util import setup_logging
from afp_alppaca.compat import OrderedDict


def run_scheduler_and_webserver(config):
    logging_config = None
    try:
        logger = setup_logging(config)
    except Exception:
        print("Could not setup logging with config '{0}'".format(
            logging_config), file=sys.stderr)
        raise
    logger.info("Alppaca starting up...")
    try:
        # Credentials is a shared object that connects the scheduler and the
        # bottle_app. The scheduler writes into it and the bottle_app reads
        # from it.
        credentials = OrderedDict()
        # initialize the credentials provider
        ims_host_port = '%s:%s' % (config['ims_host'], config['ims_port'])
        ims_protocol = config.get('ims_protocol', 'https')
        logger.info("Will get credentials from %s using %s", ims_host_port, ims_protocol)
        credentials_provider = IMSCredentialsProvider(ims_host_port, ims_protocol=ims_protocol)

        role_to_assume = config.get('assume_role')
        if role_to_assume:
            logger.info("Option assume_role set to '%s'", role_to_assume)
            credentials_provider = AssumedRoleCredentialsProvider(
                credentials_provider,
                role_to_assume,
                config.get('aws_proxy_host'),
                config.get('aws_proxy_port')
            )

        Scheduler(credentials, credentials_provider).refresh_credentials()
        # initialize and run the web app
        bind_ip = config.get('bind_ip', '127.0.0.1')
        bind_port = config.get('bind_port', '25772')
        logger.debug("Starting webserver on %s:%s", bind_ip, bind_port)
        webapp = WebApp(credentials)
        webapp.run(host=bind_ip, port=bind_port)
    except Exception:
        logger.exception("Error in Alppaca")
    finally:
        logger.info("Alppaca shutting down...")