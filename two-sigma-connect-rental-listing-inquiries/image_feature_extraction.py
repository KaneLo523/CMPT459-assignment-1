import os
import sys
import re
import operator
from zipfile import ZipFile
from subprocess import check_output
from PIL import Image, ImageStat
from skimage.io import imread
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

count = 1 #to get the first image only

def exploreFiles():

    root_dir = os.getcwd() #get the current directory
    folder = []

    #read all the files
    for root, sub_dirs, _ in os.walk(root_dir):
        for dir in sub_dirs:
            dir_path = os.path.join(root, dir)
            di = os.path.basename(dir_path)
            if(di.isnumeric()):
                entries = os.listdir(dir_path)
                #print (len(entries))
                for entry in entries:
                    folder.append(di)
    #print (folder)
    return folder

def exploreImages():
    root_dir = os.getcwd() #get the current directory
    images_list = []
    complete_images_list = []

    #read all the files
    for root, sub_dirs, _ in os.walk(root_dir):
        for dir in sub_dirs:
            dir_path = os.path.join(root, dir)
            dir_basename = os.path.basename(dir_path)
            if(dir_basename.isnumeric()):
                entries = os.listdir(dir_path)
                for entry in entries:
                    images_list.append(entry) #add all the images belonging to the listing_id to the images_list
                if len(images_list) != 0:
                   complete_images_list.append((dir_basename,images_list)) #an array of tuples(folder name, folder images)
                images_list = []

    return complete_images_list

def process_image(path):
    global count
    path = './images_sample/'+path[0:7]+'/'+path 
    image = Image.open(path, 'r')

    width = image.width
    height = image.height

    #calculate pixels
    img = imread(path, as_gray = True)
    pixels = (np.reshape(img, (height*width))).shape[0]

    #mean brightness for the images
    stat = ImageStat.Stat(image)
    bright = stat.mean[0]

    # image intensity
    rgb_im = image.convert('RGB')
    r, g, b = rgb_im.getpixel((1, 1))
    intensity = (r+g+b) / 3
    
    #saturation
    max_color = max(r,g,b)
    min_color = min(r,g,b)
    sat = (max_color - min_color) / (max_color + min_color)

    if count == 1: #color histogram for one image only
        r, g, b = image.split() #split the image into regions

        bins = list(range(256))
        plt.plot(bins, r.histogram(), 'r')
        plt.plot(bins, g.histogram(), 'g')
        plt.plot(bins, b.histogram(), 'b')
        plt.title("Color Histogram", fontsize=18)
        plt.xlabel('Color Value')
        plt.ylabel('Pixel count')
            
        plt.savefig("first_image.png")
        count = count+1
            
    #return mean values
    return width,height,bright,np.mean(sat),intensity, pixels


def process_row(row, image_files):
    result = []
    for image in image_files:
        if image[0] == str(row.listing_id):
            result = np.array([process_image(x) for x in image[1]])
            
    result = np.mean(result,axis=0)
    row['image_width'] = result[0]
    row['image_height'] = result[1]
    row['image_brightness'] = result[2]
    row['image_saturation'] = result[3]
    row['image_intensity'] = result[4]
    row['pixels'] = result[5]

    return row


def main():

    with ZipFile('images_sample.zip', 'r') as zipObj:
        zipObj.extractall() #Extract all the contents of zip file in current directory

    df = pd.read_json('train.json.zip')
    folder_files = exploreFiles()
    image_files = exploreImages()
    df = df[df.listing_id.isin(folder_files)]
    # df = df.filter(['photos', 'listing_id'])
    df['num_images'] = df.apply(lambda x: len(x['photos']), axis = 1)
    df = df[df['num_images'] != 0]
    df = df.apply(lambda row: process_row(row, image_files),axis=1)
    print (df)

    #do some plots
    plt.figure(figsize=(20,6))
    d = df[['image_saturation', 'image_brightness', 'image_width', 'image_height', 'num_images','interest_level']]
    sns.pairplot(d, hue="interest_level" )
 
    plt.savefig("stats.png")


if __name__ == "__main__":
    main()