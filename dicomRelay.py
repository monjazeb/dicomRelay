import json
import logging
import pynetdicom

from pynetdicom import AE, evt, debug_logger, AllStoragePresentationContexts
from pynetdicom.sop_class import CTImageStorage, EnhancedCTImageStorage, LegacyConvertedEnhancedCTImageStorage
from pynetdicom.sop_class import MRImageStorage, EnhancedMRImageStorage, LegacyConvertedEnhancedMRImageStorage
from pynetdicom.sop_class import Verification
from pynetdicom.presentation import build_context

# Load Configuration from config.json file
config = {
    "relay": {
        "ip": "127.0.0.1",
        "ae_title": "RELAY",
        "port": 11112
    },
    "forward": {
        "ip": "127.0.0.1",
        "ae_title": "FORWARD",
        "port": 11113
    },
    "debug": True,
    "anonymize": True
}

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    relay = config.get('relay')
    forward = config.get('forward')
    RELAY_AET = relay.get('ae_title')# This relay's AE Title
    LISTEN_PORT = relay.get('port')  # Port to listen for incoming DICOM images 
    FORWARD_HOST = forward.get('ip')  # PACS or DICOM receiver address
    FORWARD_AET = forward.get('ae_title')  # PACS AE Title
    FORWARD_PORT = forward.get('port')  # PACS or DICOM receiver port
except:
    logging.error('The <config.json> file is damaged. Defaults loaded. Relounch.')
    with open('config.json', 'w') as f:
        json.dump(config, f)
    exit(1)

# Setup logging to use the StreamHandler at the debug level
if config['debug']:
    debug_logger()
    l = logging.getLogger('pynetdicom')
    logging.basicConfig(filename='dicom.log', encoding='utf-8', level=logging.DEBUG)
#  >--------------------------------------------------------------------------------<

# Handler for c_echo request
def handle_echo(event, logger):
    requestor = event.assoc.requestor
    timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"{requestor.ae_title} ({requestor.address}, {requestor.port}) at {timestamp}")
    # Return a *Success* status
    return 0x0000

# Handler to forward received DICOM datasets
def handle_store(event, logger):
    global c
    ds = event.dataset
    ds.file_meta = event.file_meta

    requestor = event.assoc.requestor
    timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    logger.error(f"{requestor.ae_title} ({requestor.address}, {requestor.port}) at {timestamp}")
    if config['anonymize']:
        ds.remove_private_tags()
    # Set up AE for forwarding
    ae = AE(ae_title=RELAY_AET)
    ae.requested_contexts = [
        build_context(CTImageStorage),
        build_context(EnhancedCTImageStorage),
        build_context(MRImageStorage),
        build_context(EnhancedMRImageStorage),
        ]

    assoc = ae.associate(FORWARD_HOST, FORWARD_PORT, ae_title=FORWARD_AET)
    if assoc.is_established:
        status = assoc.send_c_store(ds)
        assoc.release()
        return status
    else:
        print("Could not associate with Reciever")
        return 0xA700  # Refused: Out of Resources

# Set up the relay AE
ae = AE(ae_title=RELAY_AET)
ae.supported_contexts = AllStoragePresentationContexts
ae.add_supported_context(Verification)

handlers = [
    (evt.EVT_C_ECHO,  handle_echo,  [logging.getLogger('pynetdicom')]),
    (evt.EVT_C_STORE, handle_store, [logging.getLogger('pynetdicom')]),
            ]

logging.info(f"({RELAY_AET}) listening on port {LISTEN_PORT} and forwarding to ({FORWARD_AET}) {FORWARD_HOST}:{FORWARD_PORT}")
ae.start_server(('', LISTEN_PORT), evt_handlers=handlers, block=True, )
