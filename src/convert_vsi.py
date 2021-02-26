from os import system, remove
import argparse
import platform

legal_formats = {
    '.png',
    '.tif',
    '.jpg',
    '.gif',
}

def convert_vsi(format):
    if format not in legal_formats:
        raise Exception(
            'format should be one of the following: {}. format was {}' \
            .format(str(list(legal_formats)), format)
        )
    # print('saving arguments for ' + format)
    # createSuffixFile(format)
    print('loading ImageJ')
    if platform.system() == 'Linux':
        print('----------------------------')
        system('./Fiji.app/ImageJ-linux64 --console -batch convert_vsi.ijm')
        print('----------------------------')
        print('ImageJ finish')
        print('removing suffix file')
        # removeSuffixFile()
    elif platform.system() == 'Windows':
        system('start Fiji.app\ImageJ-win64 -batch convert_vsi.ijm')
    else:
        print('platform not yet supported for .vsi conversion; Windows and Linux only')

def createSuffixFile(format):
    with open('suffix.txt', 'w') as fp:
        fp.write(format + '\n')

def removeSuffixFile():
    remove('suffix.txt')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Operate convert_vsi.ijm macro from cmd'
    )
    parser.add_argument(
        '--format', type=str, default='.jpg', help='format to convert to'
    )
    args = parser.parse_args()

    convert_vsi(args.format)
