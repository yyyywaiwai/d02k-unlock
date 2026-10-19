import ctypes
import subprocess
import sys
import time

devices = subprocess.run(['fastboot', 'devices'], capture_output=True, text=True, check=True)
if len([line for line in devices.stdout.splitlines() if line.strip()]) != 1:
    raise SystemExit('exactly one fastboot device must be connected')
# shortcut: USB reset targets the sole 18d1:d00d device; match USB serial if multiple are needed.
lib = ctypes.CDLL('/opt/homebrew/lib/libusb-1.0.dylib')
lib.libusb_init.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
lib.libusb_open_device_with_vid_pid.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16]
lib.libusb_open_device_with_vid_pid.restype = ctypes.c_void_p
lib.libusb_reset_device.argtypes = [ctypes.c_void_p]
lib.libusb_close.argtypes = [ctypes.c_void_p]
lib.libusb_exit.argtypes = [ctypes.c_void_p]
ctx = ctypes.c_void_p()
assert lib.libusb_init(ctypes.byref(ctx)) == 0
handle = lib.libusb_open_device_with_vid_pid(ctx, 0x18D1, 0xD00D)
assert handle, 'Huawei fastboot USB device not present'
try:
    assert lib.libusb_reset_device(handle) == 0
finally:
    lib.libusb_close(handle)
    lib.libusb_exit(ctx)
time.sleep(0.5)
result = subprocess.run(['fastboot', *sys.argv[1:]], timeout=180)
raise SystemExit(result.returncode)
