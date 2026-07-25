import time

async def bom_log(s):
  print(f'[{time.ctime()}] {s}', flush=True)
