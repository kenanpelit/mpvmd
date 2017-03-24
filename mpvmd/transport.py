import json
import struct
from typing import Optional, Dict


async def read(reader) -> Optional[Dict]:
    data_size_raw = await reader.read(4)
    if not data_size_raw:
        return None
    data_size = struct.unpack('<I', data_size_raw)[0]
    data = await reader.read(data_size)
    return json.loads(data.decode())


async def write(writer, message: Dict):
    data = json.dumps(message).encode()
    writer.write(struct.pack('<I', len(data)))
    writer.write(data)
    await writer.drain()
