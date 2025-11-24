import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Set lower level for some noisy libraries if needed
    logging.getLogger("aiokafka").setLevel(logging.WARNING)

logger = logging.getLogger("chat4all")
