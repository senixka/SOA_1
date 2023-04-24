import timeit
import pickle
import json
import msgpack
import yaml
from pympler.asizeof import asizeof
from test_message_pb2 import TestMessage
import google.protobuf.json_format as protobuf_funcs
import io
import xml.etree.ElementTree as ET
import avro.schema, avro.datafile


test_struct = {"strT" : "Hello world!",
              "intT" : 123456,
              "floatT" : 0.000023,
              "arrayIntT" : [-1, 23, 0, 7777],
              "arrayStrT" : ["Abra", "Cadabra"],
              "dictFloatT" : {"first": 0.0001, "second": 42.42},
              "dictStrT" : {"first": "Apple", "second": "Banana"}}


def serialize_native(data):
    return pickle.dumps(data)

def deserialize_native(data):
    return pickle.loads(data)


def serialize_json(data):
    return json.dumps(data)

def deserialize_json(data):
    return json.loads(data)


def serialize_msgpack(data):
    return msgpack.packb(data)

def deserialize_msgpack(data):
    return msgpack.unpackb(data)


def serialize_yaml(data):
    return yaml.dump(data)

def deserialize_yaml(data):
    return yaml.safe_load(data)


def serialize_protobuf(data):
    message = TestMessage()
    protobuf_funcs.ParseDict(data, message)
    return TestMessage.SerializeToString(message)

def deserialize_protobuf(data):
    message = TestMessage()
    message.ParseFromString(data)
    return protobuf_funcs.MessageToDict(message)


avro_schema = avro.schema.parse('''
{
    "type": "record",
    "name": "TestStruct",
    "fields": [
        {"name": "strT", "type": "string"},
        {"name": "intT", "type": "int"},
        {"name": "floatT", "type": "double"},
        {"name": "arrayIntT", "type": {"type": "array", "items": "int"}},
        {"name": "arrayStrT", "type": {"type": "array", "items": "string"}},
        {"name": "dictFloatT", "type": {"type": "map", "values": "double"}},
        {"name": "dictStrT", "type": {"type": "map", "values": "string"}}
    ]
}
''')

def serialize_avro(data):    
    buffer = io.BytesIO()
    
    writer = avro.datafile.DataFileWriter(buffer, avro.io.DatumWriter(), avro_schema)
    writer.append(data)
    writer.flush()
    
    result = buffer.getvalue()
    writer.close()
    return result

def deserialize_avro(data):
    buffer = io.BytesIO(data)
    
    reader = avro.datafile.DataFileReader(buffer, avro.io.DatumReader())
    for value in reader:
        parsed_data = value
    
    reader.close()
    return parsed_data



def serialize_xml(data):
    def serialize_xml_inner(parent, element, name):
        if isinstance(element, dict):
            e = ET.SubElement(parent, name, {"type": "dict"})
            for key, value in element.items():
                serialize_xml_inner(e, value, key)
        elif isinstance(element, list):
            e = ET.SubElement(parent, name, {"type": "list"})
            for value in element:
                serialize_xml_inner(e, value, "item")
        elif isinstance(element, int):
            ET.SubElement(parent, name, {"type": "int"}).text = str(element)
        elif isinstance(element, float):
            ET.SubElement(parent, name, {"type": "float"}).text = str(element)
        elif isinstance(element, str):
            ET.SubElement(parent, name, {"type": "str"}).text = str(element)
    
    
    root = ET.Element("TestStruct")
    serialize_xml_inner(root, data, "TestStruct")
    return ET.tostring(root).decode()

def deserialize_xml(data):
    def deserialize_xml_inner(element):
        if element.attrib.get("type") in ["dict", None]:
            return dict([(e.tag, deserialize_xml_inner(e)) for e in element])
        elif element.attrib.get("type") == "list":
            return [deserialize_xml_inner(e) for e in element]
        else:
            text = element.text.strip()
            
            if element.attrib.get("type") == "int":
                return int(text)
            elif element.attrib.get("type") == "float":
                return float(text)
            else:
                return text
        
    return deserialize_xml_inner(ET.fromstring(data))["TestStruct"]



REGISTRY = {"NATIVE": [serialize_native, deserialize_native],
            "JSON": [serialize_json, deserialize_json],
            "PROTOBUF": [serialize_protobuf, deserialize_protobuf],
            "MSGPACK": [serialize_msgpack, deserialize_msgpack],
            "YAML": [serialize_yaml, deserialize_yaml],
            "XML": [serialize_xml, deserialize_xml],
            "AVRO": [serialize_avro, deserialize_avro]}



def Test(test_type, test_iter=1000):
    # Prepare serializer and deserializer
    if test_type not in REGISTRY:
        return "Bad test_type arg"
    serializer, deserializer = REGISTRY[test_type]

    # Check that serializer and deserializer work correct
    data = serializer(test_struct)
    if deserializer(data) != test_struct:
        return "Fail deserializer(serializer) check"

    # Result time in microseconds
    serialize_time = int(timeit.Timer(lambda: serializer(test_struct)).timeit(number=test_iter) * 1_000_000 / test_iter)    
    deserialize_time = int(timeit.Timer(lambda: deserializer(data)).timeit(number=test_iter) * 1_000_000 / test_iter)

    return " - ".join([test_type, str(asizeof(data)), str(serialize_time) + "μs", str(deserialize_time) + "μs"]) + "\n"
