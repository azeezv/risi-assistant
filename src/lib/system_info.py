import os
import platform
from datetime import datetime

class SystemInfo:
    USER_OS = f"{platform.system()} {platform.release()}"
    CURRENT_WORKING_DIRECTORY = os.getcwd()
    CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")