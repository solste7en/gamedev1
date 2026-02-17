"""
Brawler character classes.
"""

from .base import Brawler
from .colt import Colt
from .shelly import Shelly
from .piper import Piper
from .edgar import Edgar

BRAWLER_CLASSES = {
    'colt': Colt,
    'shelly': Shelly,
    'piper': Piper,
    'edgar': Edgar
}

__all__ = ['Brawler', 'Colt', 'Shelly', 'Piper', 'Edgar', 'BRAWLER_CLASSES']
