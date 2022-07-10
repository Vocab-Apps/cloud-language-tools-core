import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import cloudlanguagetools.servicemanager
import cloudlanguagetools.spacy

if __name__ == '__main__':
    logger = logging.getLogger()
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])    
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        stream=sys.stdout,
                        level=logging.INFO)    

    parser = argparse.ArgumentParser(description='Argos Translate utils')
    parser.add_argument('--action', choices=['install_all_packages'], required=True)

    args = parser.parse_args()

    if args.action == 'install_all_packages':
        cloudlanguagetools.spacy.install_all_packages()