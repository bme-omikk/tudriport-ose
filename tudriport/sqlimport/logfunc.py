from ..common.config import getconfig
from ..common.db import getsqlutc

import os
import json
import shutil
import syslog

import gzip
import lzma
import tarfile

# Belső függvény
def _writelogfile(db, logstr):
    datetimeutc_sql = str(getsqlutc(db))
    f = open("%s/log-%s.log"%(getconfig('sqlimport.LOGDIR'), datetimeutc_sql[:10]), "a+")
    f.write("%s %s"%(datetimeutc_sql, logstr))
    f.close()

# Belső függvény
def _writesyslog(szint, logstr):
    loglevel = {
        'DEBUG': syslog.LOG_DEBUG,
        'INFO': syslog.LOG_INFO,
        'NOTICE': syslog.LOG_NOTICE,
        'WARNING': syslog.LOG_WARNING,
        'ERROR': syslog.LOG_ERR,
        'CRITICAL': syslog.LOG_CRIT,
    }.get(szint, syslog.LOG_CRIT)
    syslog.syslog(loglevel, logstr)


def writelog(db, tipus, szint, uzenet):
    writelog_id(db, tipus, szint, None, uzenet)

def writelog_id(db, tipus, szint, publication, uzenet):
    if szint in getconfig('sqlimport.HIDELOGLEVELS'):
        return

    pub_id_string = format_pubid_string(publication)

    if getconfig('sqlimport.UNIXSYSLOG') == 0:
        _writelogfile(db, "%10s %8s %s %s\n"%(tipus, szint, pub_id_string, uzenet))
    else:
        _writesyslog(szint, "%10s %s %s\n"%(tipus, pub_id_string, uzenet))

def format_pubid_string(publication):
    if publication is not None and isinstance(publication, dict):
        pub_id_string = "%8s[%s/%s]"%(publication.get('mtmt_pubid', None)
                                    , publication.get('type_id', None)
                                    , publication.get('subtype_id', None)
                                     )

        pub_id_string = pub_id_string.ljust(8+2+8+3) # szélességek: 8: pubid, 2: type_id, 8: subtypeid, 3: központozás, i.e. [/]
    else:
        pub_id_string = ''

    return pub_id_string

def historyf_write(historydir, maxfileperdir, realfname, outdata):
    subdir = None
    # utsó számozott mappa melyik?
    for d in sorted(next(os.walk(historydir))[1]):
        if len(d) == 5 and d.isdigit():
            subdir = d
    if not subdir:
        subdir = '00001'
        os.mkdir(historydir+'/'+subdir, 0o755)
    # ha elérte a fájlszám a maximumot a mappában --> új mappa és tar()
    elif len(os.listdir(historydir+'/'+subdir)) >= maxfileperdir:
        subdir_new = "%05d"%(int(subdir)+1)
        os.mkdir(historydir+'/'+subdir_new, 0o755)
        if getconfig('sqlimport.HISTORYCOMPRESS')[:3] == 'tar':
            compr = {'tar.gz':'gz', 'tar.xz':'xz'}.get(getconfig('sqlimport.HISTORYCOMPRESS'), 'tar')
            tarfilename = '%s/%05d.%s'%(historydir, int(subdir), getconfig('sqlimport.HISTORYCOMPRESS'))
            tar = tarfile.open('%s.tmp'%(tarfilename), 'w|%s'%(compr))
            origdir = os.getcwd()
            os.chdir(historydir); tar.add("%05d"%(int(subdir))); os.chdir(origdir)
            tar.close()
            os.rename('%s.tmp'%(tarfilename), tarfilename)
            print ("rmdir: %s/%05d"%(historydir, int(subdir)))
            shutil.rmtree("%s/%05d"%(historydir, int(subdir)))
        subdir = subdir_new

    # .gz .xz
    ext = ''
    if getconfig('sqlimport.HISTORYCOMPRESS') in ('gz', 'xz'):
        ext = '.'+getconfig('sqlimport.HISTORYCOMPRESS')
    dstfile = "%s/%s/%s%s"%(historydir, subdir, realfname, ext)

    # magát a kimenőfájlt tömörítjük? None vagy utólagos tar-olás esetén nem.
    if getconfig('sqlimport.HISTORYCOMPRESS') is None or getconfig('sqlimport.HISTORYCOMPRESS')[:3] == 'tar':
        f=open(dstfile, 'wb', 0o644)
    elif getconfig('sqlimport.HISTORYCOMPRESS') == 'gz':
        f=gzip.open(dstfile+'.gz', 'wb')
    elif getconfig('sqlimport.HISTORYCOMPRESS') == 'xz':
        f=lzma.open(dstfile+'.xz', 'wb')

    f.write(outdata)
    f.close()
    return dstfile


def writexmlhistory(db, xmldata, datetimeutc_sql):
    realfname = "%s-0000.xml"%(datetimeutc_sql.replace(' ', '_')) # 0000 hogy mappalistázáskor elöl legyen

    dstfile = historyf_write(getconfig('sqlimport.XMLHISTORY'), getconfig('sqlimport.MAXFILEPERDIR'), realfname, xmldata)
    writelog(db, 'SOFTWARE', 'INFO', 'A bejovo file %s allomanyba masolva.'%(dstfile))


def writejsonhistory(db, publication, authors, citations, datetimeutc_sql, seqnum):
    data = {'publication': publication, 'authors': authors, 'citations': citations}
    jsondata = (bytes(json.dumps(data, sort_keys=True, indent=2, separators=(',', ': '), ensure_ascii=False), 'utf-8'))
    realfname = "%s-%04d-%s.json"%(datetimeutc_sql.replace(' ', '_'), seqnum, publication['mtmt_pubid'])
    dstfile = historyf_write(getconfig('sqlimport.JSONHISTORY'), 2*getconfig('sqlimport.MAXFILEPERDIR'), realfname, jsondata)
    writelog_id(db, 'SOFTWARE', 'INFO', publication, 'A kozlemeny %s allomanyba kiirva.'%(dstfile))
