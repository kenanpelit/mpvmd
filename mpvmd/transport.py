import json
import struct
from typing import Dict


async def read(reader):
    data_size = struct.unpack('<I', await reader.read(4))[0]
    data = await reader.read(data_size)
    return json.loads(data.decode())


async def write(writer, message: Dict):
    data = json.dumps(message).encode()
    writer.write(struct.pack('<I', len(data)))
    writer.write(data)
    await writer.drain()
