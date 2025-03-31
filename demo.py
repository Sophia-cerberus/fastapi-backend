import os
file = "a/b/c.py"
file_name, file_ext = os.path.splitext(file)
print(file_name, file_ext)