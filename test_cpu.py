import os

cpu_count = os.cpu_count()
print(f"Available logical CPUs: {cpu_count}")