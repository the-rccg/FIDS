# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 20:23:59 2019

@author: Robin
"""

##################################################################################
# Download Selection
##################################################################################
def selected_data_to_csv(selected_data_dict, xaxis_name, yaxis_name, caxis_name, saxis_name):
    if saxis_name:
        print("WARNING SIZE IS ADJUSTED FOR VISUALIZATION!!!")
    points = selected_data_dict['points']
    #print(points)
    num_points = len(points)
    if num_points == 0:
        return ""
    if num_points > 10000:
        print('WARNING large dataset parsing: {}'.format(num_points))
    from os import linesep 
    if not caxis_name and not saxis_name:
        csv_string = "description,{},{}".format(xaxis_name, yaxis_name) + linesep + "{}".format(linesep).join(['{}, {}, {}'.format(point['text'], point['x'], point['y']) for point in points])
    elif not saxis_name:
        csv_string = "description,{},{},{}".format(xaxis_name,yaxis_name,caxis_name) + linesep + "{}".format(linesep).join(['{}, {}, {}, {}'.format(point['text'], point['x'], point['y'], point['marker.color']) for point in points])
    #elif not caxis_name:
    #    csv_string = "description,{},{},{}".format(xaxis_name,yaxis_name,saxis_name) + linesep + "{}".format(linesep).join(['{}, {}, {}, {}'.format(point['text'], point['x'], point['y'], point['marker.size']) for point in points])
    #elif caxis_name and saxis_name:
    #    csv_string = "description,{},{},{}, {}".format(xaxis_name,yaxis_name,caxis_name,saxis_name) + linesep + "{}".format(linesep).join(['{}, {}, {}, {}, {}'.format(point['text'], point['x'], point['y'], point['marker.color'], point['marker.size']) for point in points])
    else:
        import pandas as pd
        csv_string = pd.DataFrame(points).to_csv()
    print(csv_string)
    return csv_string

def download_selected(selected_data, xaxis_name, yaxis_name, caxis_name, saxis_name):
    if type(selected_data) == dict:
        import urllib.parse
        return "data:text/csv;charset=utf-8,%EF%BB%BF" + urllib.parse.quote(selected_data_to_csv(selected_data, xaxis_name, yaxis_name, caxis_name, saxis_name), encoding="utf-8")
    else:
        return 
    #from flask import send_file
    #send_file(csv,
    #            #mimetype='text/csv',
    #            attachment_filename='selection.csv',
    #            as_attachment=True)
    

##################################################################################
# Allow Downloading Entire Brick
##################################################################################
def update_download_link(file_list):
    '''  '''
    if not file_list or file_list == "None":
        return 
    if type(file_list) is list:
        print(file_list)
        return '/dash/download?value={}'.format(",".join(file_list))
        #file_value = file_value[0]
    filepath = settings['folderpath'] + file_list
    from os.path import isfile
    if not isfile(filepath):
        return
    else:
        return '/dash/download?value={}'.format(file_list)

def download_file():
    from flask import request, send_file
    filename = request.args.get('value')
    file_list = filename.split(',')
    print("download: ", file_list)
    filepath_list = [settings['folderpath'] + filename for filename in file_list]
    filepath = filepath_list[0]  # TODO: Allow downloading of multiple files
    return send_file(filepath,
                #mimetype='text/csv',
                attachment_filename=filename,
                as_attachment=True)
##################################################################################