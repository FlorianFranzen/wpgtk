import errno
import pywal
import shutil
import sys
from random import shuffle
from os.path import realpath, isfile
from os import symlink, remove
from subprocess import Popen, call
from . import color, sample, config, files


def create_theme(filepath):
    filename = str(filepath).split("/").pop()
    shutil.copy2(filepath, config.WALL_DIR / filename)
    image = pywal.image.get(config.WALL_DIR / filename)
    colors = pywal.colors.get(image, config.WALL_DIR)
    pywal.export.color(colors,
                       "xresources",
                       config.XRES_DIR / (filename + ".Xres"))
    color_list = [val for val in colors['colors'].values()]
    sample.create_sample(color_list,
                         f=config.SAMPLE_DIR / (filename + '.sample.png'))


def set_theme(filename, cs_file, restore=False):
    if(isfile(config.WALL_DIR / filename)):
        if(not restore):
            color.execute_gcolorchange(cs_file)
            pywal.reload.gtk()
            pywal.reload.i3()
            pywal.reload.polybar()

        pywal.wallpaper.change(config.WALL_DIR / filename)
        image = pywal.image.get(config.WALL_DIR / cs_file)
        colors = pywal.colors.get(image, config.WALL_DIR)
        pywal.sequences.send(colors, False, config.WALL_DIR)
        pywal.export.color(colors, 'css', config.WALL_DIR / 'current.css')
        pywal.export.color(colors, 'shell', config.WALL_DIR / 'current.sh')

        init_file = open(config.WALL_DIR / 'wp_init.sh', 'w')
        init_file.writelines(['#!/bin/bash\n', 'wpg -r -s ' +
                              filename + ' ' + cs_file])
        init_file.close()
        Popen(['chmod', '+x', config.WALL_DIR / 'wp_init.sh'])
        call(['xrdb', '-merge', config.XRES_DIR / (cs_file + '.Xres')])
        call(['xrdb', '-merge', config.HOME / '.Xresources'])
        try:
            if config.wpgtk.getboolean('execute_cmd'):
                Popen(config.wpgtk['command'].split(' '))
                print("ERR:: malformed editor command", sys.stderr)
            symlink(config.WALL_DIR / filename, config.WALL_DIR / ".current")
        except Exception as e:
            if e.errno == errno.EEXIST:
                remove(config.WALL_DIR / ".current")
                symlink(config.WALL_DIR / filename,
                        config.WALL_DIR / ".current")
            else:
                raise e
    else:
        print("no such file, available files:")
        files.show_files()


def delete_theme(filename):
    cache_file = str(config.WALL_DIR / filename)
    remove(config.WALL_DIR / filename)
    remove(config.SAMPLE_DIR / (filename + '.sample.png'))
    remove(config.XRES_DIR / (filename + '.Xres'))
    remove(config.SCHEME_DIR /
           (cache_file.replace('/', '_').replace('.', '_') + ".json"))


def show_current():
    image = realpath(config.WALL_DIR / '.current').split('/').pop()
    print(image)
    return image


def shuffle_colors(filename):
    if(isfile(config.WALL_DIR + filename)):
        colors = color.read_colors(filename)
        shuffled_colors = colors[1:8]
        shuffle(shuffled_colors)
        colors = colors[:1] + shuffled_colors + colors[8:]
        sample.create_sample(colors, f=config.SAMPLE_DIR /
                             filename / '.sample.png')
        color.write_colors(filename, colors)


def auto_adjust_colors(filename):
    try:
        color_list = color.get_color_list(filename)
        color8 = color_list[0:1][0]
        if not config.wpgtk.getboolean('light_theme'):
            color8 = [color.add_brightness(color8, 18)]
            color_list = color_list[:8:]
            color_list += color8
            color_list += [color.add_brightness(x, 50)
                           for x in color_list[1:8:]]
        else:
            color8 = [color.reduce_brightness(color8, 18)]
            color_list = color_list[:8:]
            color_list += color8
            color_list += [color.reduce_brightness(x, 50)
                           for x in color_list[1:8:]]
        sample.create_sample(color_list,
                             f=config.SAMPLE_DIR /
                             (filename + '.sample.png'))
        color.write_colors(filename, color_list)
    except IOError:
        print(f'ERR:: file not available')