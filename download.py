# -*- coding: utf-8 -*-
"""
FITS Dash App
Quickly sketch and explore data tables and relations sae in FITS format 

Line-length:  84 (since thats VSCode on 1080 vertical)

@author: RCCG
"""
import numpy as np
import pandas as pd
import tempfile
import io
from sys import getsizeof
import re
import ast
from pprint import pprint

def unpack_vars(variables):
    """ unpack variables parsed via http request """
    for key in variables:
        if variables[key]:
            if variables[key][0] == '[':
                # Check for nested lists
                if variables[key][1] == '[':
                    # Insert commas between numbers, and between lists
                    variables[key] = re.sub(
                        r"([-\d]+)\s+([\d-]+)",
                        r"\1,\2",
                        variables[key].replace("\n ",",")
                    )
                    # Remove white spaces, translate to list, reformat as array
                    variables[key] = np.array(ast.literal_eval(variables[key].replace(" ", "")))
                else:
                    variables[key] = ast.literal_eval(variables[key])
            elif variables[key][0] == '{':
                # No handling for nested dictionaries
                variables[key] = ast.literal_eval(variables[key])
            elif variables[key][0] == "'":
                variables[key] = ast.literal_eval(variables[key])
    return variables

def generate_df(return_data, chunk_size_mb):
    """ send in chunks from one large dataframe """
    row_count = return_data[list(return_data.keys())[0]].shape[0]
    return_size_mb = np.sum([return_data[key].nbytes for key in return_data.keys()])/1024/1024
    chunk_size = int(row_count/(return_size_mb*chunk_size_mb))
    print("chunk size in rows: {:,.0f}".format(chunk_size))
    return_data = pd.DataFrame(return_data)
    i = 0
    yield return_data[i:i+chunk_size].to_csv(index=False, header=True)
    while i < row_count: 
        yield return_data[i:i+chunk_size].to_csv(index=False, header=False)
        i += chunk_size

def generate_tmp(return_data, chunk_size_mb):
    """ send in chunks from one large tempfile """
    tf = tempfile.TemporaryFile(mode='w+t', newline='')
    pd.DataFrame(return_data).to_csv(tf, index=False, encoding='utf-8')
    del return_data  # Free up space asap
    size = tf.tell()
    print("  File Size: {:,.2f} mb".format(size/1024/1024))
    tf.seek(0)
    chunk_size = chunk_size_mb*1024*1024
    print("  Chunk Size: {:,.2f} mb".format(chunk_size_mb))
    i = 0
    while i < size: 
        yield tf.read(chunk_size)
        i += chunk_size
    tf.close()

def generate_small_file(return_data, return_size_mb):
    """ send small file from memory """
    # String Buffer
    str_io = io.StringIO()
    pd.DataFrame(return_data).to_csv(str_io, index=False)
    del return_data  # free memory asap
    # Byte Buffer
    mem = io.BytesIO()
    mem.write(str_io.getvalue().encode('utf-8'))
    mem.seek(0)
    str_io.close()
    print("sizes:  {:.4f} -> {:.4f} mb".format(
        return_size_mb,
        getsizeof(mem)/1024/1024)
    )
    # Send File
    return mem
