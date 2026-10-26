"""Read-only Windows resolution and per-monitor DPI evidence probe."""
import ctypes
from ctypes import wintypes
import sys

u32=ctypes.windll.user32
shcore=ctypes.windll.shcore
class MONITORINFO(ctypes.Structure):
    _fields_=[("cbSize",wintypes.DWORD),("rcMonitor",wintypes.RECT),("rcWork",wintypes.RECT),("dwFlags",wintypes.DWORD)]
records=[]
@ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HMONITOR,wintypes.HDC,ctypes.POINTER(wintypes.RECT),wintypes.LPARAM)
def each(monitor,dc,rect,data):
    info=MONITORINFO();info.cbSize=ctypes.sizeof(info)
    u32.GetMonitorInfoW(monitor,ctypes.byref(info))
    x=wintypes.UINT();y=wintypes.UINT()
    hr=shcore.GetDpiForMonitor(monitor,0,ctypes.byref(x),ctypes.byref(y))
    records.append({"bounds":(info.rcMonitor.left,info.rcMonitor.top,info.rcMonitor.right,info.rcMonitor.bottom),
                    "work":(info.rcWork.left,info.rcWork.top,info.rcWork.right,info.rcWork.bottom),
                    "dpi_hr":hr,"dpi":(x.value,y.value)})
    return True
u32.EnumDisplayMonitors(0,0,each,0)
print("Windows version",sys.getwindowsversion())
print("system_dpi",u32.GetDpiForSystem(),"monitor_count",len(records))
for index,row in enumerate(records,1):print("monitor",index,row)
