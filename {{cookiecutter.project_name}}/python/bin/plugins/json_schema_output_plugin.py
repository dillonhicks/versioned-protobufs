#!/usr/bin/env python
"""
Generate a JSON Schema Representation - more of a debug tool

Taken from:
   http://www.expobrain.net/2015/09/13/create-a-plugin-for-google-protocol-buffer/

"""
import sys
from itertools import chain
import json

from google.protobuf.compiler import plugin_pb2 as plugin
from google.protobuf.descriptor_pb2 import DescriptorProto, EnumDescriptorProto


def generate_code(request, response):
    for proto_file in request.proto_file:
        output = []

        # Parse request
        for item, package in traverse(proto_file):
            data = {
                'package': proto_file.package or '&lt;root&gt;',
                'filename': proto_file.name,
                'name': item.name,
            }

            if isinstance(item, DescriptorProto):
                data.update({
                    'type': 'Message',
                    'properties': [{'name': f.name, 'type': int(f.type), 'type_name': f.type_name, 'options': f.options.packed} for f in item.field]
                })

            elif isinstance(item, EnumDescriptorProto):
                data.update({
                    'type': 'Enum',
                    'values': [{'name': v.name, 'value': int(v.number)}
                               for v in item.value]
                })

            output.append(data)

        # Fill response
        f = response.file.add()
        f.name = proto_file.name + '.json'
        f.content = json.dumps(output, indent=2)


def _traverse(package, items):
    top_items = []
    enums = []
    nested_items = []
    for item in items:
        top_items.append((item, package))

        if not isinstance(item, DescriptorProto):
            continue

        for enum in item.enum_type:
            enums.append((enum, package))

        for nested in item.nested_type:
            nested_package = package + item.name

            for nested_item in _traverse(nested, nested_package):
                nested_items.append((nested_item, nested_package))

    return chain(chain(top_items, enums), nested_items)


def traverse(proto_file):

    return chain(
        _traverse(proto_file.package, proto_file.enum_type),
        _traverse(proto_file.package, proto_file.message_type),
    )


if __name__ == '__main__':
    # Read request message from stdin
    data = sys.stdin.read()

    # Parse request
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(data)

    # Create response
    response = plugin.CodeGeneratorResponse()

    # Generate code
    generate_code(request, response)

    # Serialise response message
    output = response.SerializeToString()

    # Write to stdout
    sys.stdout.write(output)
