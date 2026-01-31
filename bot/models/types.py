from enum import IntEnum, Enum

class QobuzQuality(IntEnum):
    MP3 = 5
    LOSSLESS = 6        # CD Quality (16-bit / 44.1kHz)
    HIRES96 = 7       # 24-bit <= 96kHz
    HIRES192 = 27     # 24-bit > 96kHz


class TidalQuality(Enum):
    LOW = 'LOW'
    HIGH = 'HIGH'
    LOSSLESS = 'LOSSLESS'
    HI_RES = 'MAX'


class TidalSpatial(Enum):
    OFF = 'OFF'
    ATMOS_AC3 = 'ATMOS AC3 JOC'
    ATMOS_AC4 = 'ATMOS AC4'
    SONY_360RA = 'Sony 360RA'