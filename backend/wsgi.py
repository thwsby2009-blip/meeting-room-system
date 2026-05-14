import sys
path = '/home/thwsby/meeting-room-system/backend'
if path not in sys.path:
    sys.path.insert(0, path)

import os
os.environ['DATABASE_PATH'] = os.path.join(path, 'meeting_room.db')

from main import app
application = app
