"""This file opens an example file for benchmarking performance"""

import time

from nemreader import NEMFile

start = time.process_time()
m = NEMFile("examples/large_example.zip")
df = m.get_data_frame_wide()
if df is None:
    raise ValueError("No data frame returned")
end = time.process_time()
print(f"Time to load data frame: {end - start:.2f} seconds")
