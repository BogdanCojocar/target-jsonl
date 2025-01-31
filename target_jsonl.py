#!/usr/bin/env python3

import argparse
import io
import json
import os
import sys
from datetime import datetime

import singer
from jsonschema import Draft4Validator, FormatChecker
from decimal import Decimal
import boto3

logger = singer.get_logger()


def emit_state(state):
    if state is not None:
        line = json.dumps(state)
        logger.debug('Emitting state {}'.format(line))
        sys.stdout.write("{}\n".format(line))
        sys.stdout.flush()


def float_to_decimal(value):
    '''Walk the given data structure and turn all instances of float into
    double.'''
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [float_to_decimal(child) for child in value]
    if isinstance(value, dict):
        return {k: float_to_decimal(v) for k, v in value.items()}
    return value


def persist_messages(messages, destination_path, s3_bucket, do_timestamp_file=True):
    state = None
    schemas = {}
    key_properties = {}
    validators = {}

    timestamp_file_part = '-' + datetime.now().strftime('%Y%m%dT%H%M%S') if do_timestamp_file else ''

    s3_messages = []
    s3_key = ''
    for message in messages:
        try:
            o = singer.parse_message(message).asdict()
        except json.decoder.JSONDecodeError:
            logger.error("Unable to parse:\n{}".format(message))
            raise
        message_type = o['type']
        if message_type == 'RECORD':
            if o['stream'] not in schemas:
                raise Exception(
                    "A record for stream {}"
                    "was encountered before a corresponding schema".format(o['stream'])
                )

            validators[o['stream']].validate(float_to_decimal(o['record']))

            filename = o['stream'] + timestamp_file_part + '.jsonl'
            filename = os.path.expanduser(os.path.join(destination_path, filename))

            with open(filename, 'a', encoding='utf-8') as json_file:
                json_file.write(json.dumps(o['record']) + '\n')
            s3_messages.append(json.dumps(o['record']) + '\n')
            s3_key = filename

            state = None
        elif message_type == 'STATE':
            logger.debug('Setting state to {}'.format(o['value']))
            state = o['value']
        elif message_type == 'SCHEMA':
            stream = o['stream']
            schemas[stream] = float_to_decimal(o['schema'])
            validators[stream] = Draft4Validator(float_to_decimal(o['schema']))
            key_properties[stream] = o['key_properties']
        else:
            logger.warning("Unknown message type {} in message {}".format(o['type'], o))

    s3 = boto3.client('s3')
    s3.put_object(
        Body=str(s3_messages)[1:-1],
        Bucket=s3_bucket,
        Key=s3_key
    )

    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Config file')
    args = parser.parse_args()

    if args.config:
        with open(args.config) as input_json:
            config = json.load(input_json)
    else:
        config = {}

    input_messages = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    state = persist_messages(input_messages, config.get('destination_path', ''), config.get('s3_bucket'), config.get('do_timestamp_file', True))

    emit_state(state)
    logger.debug("Exiting normally")


if __name__ == '__main__':
    main()
