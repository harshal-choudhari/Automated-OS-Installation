#!/usr/bin/python
import subprocess
import sys
import ConfigParser
import logging

def configParserObj(fileName):
	try:
		conf = ConfigParser.ConfigParser()
		conf.read(fileName)
		return conf
	except IOError as exception:
		logging.error(exception)
		sys.exit(1)

def getLoggingLevel(level):
    #{'logging.CRITICAL':50, 'logging.ERROR':40, 'logging.WARNING':30, 'logging.INFO':20, 'logging.DEBUG':10}
    #logging level works with int values which are specified above. this function converts user level to actual value of logging.
    return int(conf.get('common-config',level))

def getSectionValue(section, option):
    try:
        result = conf.get(section, option)
        logging.debug('reading variable {} with value {} from {} file. status:SUCCESS'.format(option, result, sys.argv[1]))
        return result
    except ConfigParser.NoSectionError as exception:
        logging.debug('tried reading variable {} from {} file. status:FAIL dumping exception log below'.format(option, sys.argv[1]))
        logging.error(exception)
        #if error occurs process can read from default config file 
        try:
            defaultConf = ConfigParser.ConfigParser()
            defaultConf.read('default.conf')
            result = defaultConf.get(section, option)
            logging.debug('Due to error reading from default configuration file {}. variable name {} with value {}'.format('default.conf', option, result))
            return result
        except IOError as exception:
            logging.error('Unable to read from default config file')
            sys.exit(1)

def execute(cmd):
    try:
    	subprocess.call(cmd,shell=True)
        logging.debug(cmd)
    except Exception  as e:
        logging.error(e)

def generateISO():
    #loopdir and cd folders are temp folders thats why they are hardcoded
    execute("mkdir loopdir >> /dev/null 2>&1")
    execute("mount -o loop {} loopdir >> /dev/null 2>&1".format(isoFile))
    execute("mkdir cd")
    execute("rsync -a -H --exclude=TRANS.TBL loopdir/ cd >> /dev/null 2>&1")
    execute("umount loopdir >> /dev/null 2>&1")
    execute("gunzip cd/install.amd/initrd.gz >> /dev/null 2>&1")
    execute("echo 'preseed.cfg' | cpio -o -H newc -A -F cd/install.amd/initrd >> /dev/null 2>&1")
    execute("gzip cd/install.amd/initrd >> /dev/null 2>&1")
    execute("cd cd")
    execute("md5sum `find -follow -type f` > md5sum.txt >> /dev/null 2>&1")
    execute("cd ../")
    execute("genisoimage -o test.iso -r -J -no-emul-boot -boot-load-size 4 -boot-info-table -b isolinux/isolinux.bin -c isolinux/boot.cat cd >> /dev/null 2>&1")
    execute("rm -rf cd/ loopdir/ md5sum.txt test.iso >> /dev/null 2>&1")
    execute("chown -R {}:{} guest.img".format(user,group))

def generateIMG():
    execute("qemu-img create -f {} {} {} >> /dev/null 2>&1".format(fileFormat,imgName,imgSize))
    execute("qemu-system-x86_64 -cdrom test.iso -hda {} -m {} -netdev tap,id=tap0 -device e1000,netdev=tap0".format(imgName, ramSize))

if __name__=='__main__':
    conf = configParserObj(sys.argv[1])
    loggingLevel = conf.get('createImg', 'logging-level')
    logFormat = '%(asctime)s %(levelname)s %(lineno)d %(process)d %(message)s'
    logging.basicConfig(filename='generate-debian-img.log', level=getLoggingLevel(loggingLevel), format=logFormat)
    isoFile = getSectionValue('createImg', 'isoFile')
    fileFormat = getSectionValue('createImg', 'fileFormat')
    imgName = getSectionValue('createImg', 'imgName')
    imgSize = getSectionValue('createImg', 'imgSize')
    ramSize = getSectionValue('createImg', 'ramSize')
    user = getSectionValue('createImg', 'user')
    group = getSectionValue('createImg', 'group')
    generateISO()
    generateIMG()
