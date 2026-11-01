"""Strict portable framed UTF-8 JSON. stdout is exclusively this transport."""
import json, struct
MAX_FRAME = 8 * 1024 * 1024
def exact(stream, size, allow_eof=False):
    result=bytearray()
    while len(result)<size:
        chunk=stream.read(size-len(result))
        if not chunk:
            if allow_eof and not result: return None
            raise EOFError('EOF during frame')
        result.extend(chunk)
    return bytes(result)
def read_frame(stream, maximum=MAX_FRAME):
    header=exact(stream,4,True)
    if header is None: return None
    size=struct.unpack('>I',header)[0]
    if size==0 or size>maximum: raise ValueError('Invalid frame length')
    data=exact(stream,size)
    value=json.loads(data.decode('utf-8',errors='strict'))
    if not isinstance(value,dict): raise ValueError('Frame must contain JSON object')
    return value
def encode(value):
    payload=json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    if len(payload)>MAX_FRAME: raise ValueError('Oversized outgoing frame')
    return struct.pack('>I',len(payload))+payload
