#!/usr/bin/python
# coding=utf-8
from ftplib import FTP
from ftplib import all_errors
import sys
import codecs
import csv
import paramiko
import sendmailt
import time
import psycopg2
from Ftptool import Ftpmrdo


reload(sys)
sys.setdefaultencoding('utf8')


def sqlselect(sqlstr, database="ltests", user="dbuser", password="123456", host="10.243.71.93", port="5432"):
    '''get rows of enbid from sql'''
    try:
        sqlconn = psycopg2.connect(
            database="ltests", user="dbuser", password="123456", host="10.243.71.93", port="5432")
        cur = sqlconn.cursor()
        # sdate=time.localtime()
        # datastr=sdate[0]+'-'+sdate[1]+'-'+sdate[2]
        # change time to year-month-day,string type
        sdate = time.strftime('%Y-%m-%d')
        print("selecting")
        cur.execute(sqlstr)
        rows = cur.fetchall()
        print(len(rows))
        sqlconn.close()
        return rows

    except Exception, e:
        print(str(e))
        getftpwrong = str(e)
        subject = '[SQL wrong]' + str(e)
        message = sendmailt.makemailtext("liyangsgs@ah.chinamobile.com", [
            "liyangsgs@ah.chinamobile.com", "cn.liyang@139.com"], subject, subject)
        sendmailt.quicksendmail(message)


def delmrfile(sqlrows, sendmail=1):
    '''delete file from sql,about zte,hw and others'''
    namezte = 'ZTE_NORTH'
    passwordzte = 'NDS123zte'
    dirlocal = '/home/eyann/mypython/t1/alertfileqci1/'
    dirpath = '/MR/'
    allsucc = 0
    allenb = 0
    allcell = 0
    resultlist = []
    ztefail = 0
    hwfail = 0
    ericfail = 0
    nokiafail = 0
    new = time.strftime('%Y-%m-%d %H:%M:%S')  # get filedir by data
    undo = 0  # undo  's number of enb is not execute

    getftpwrong = ''
    dictreslut = {}
    data = ''
    enblist = []
    success = 0

    numbercell = len(sqlrows)
    celllist = []
    numenb = 0
    enbdo = 0
    faillist = []
    succlist = []
    ftpmrdo = Ftpmrdo()

    for strtolist in sqlrows:
        # strtolist=t.split('|')
        data = str(strtolist[0])  # data is date,first cl of rows is date
        celllist.append(strtolist[1])
        enbid = strtolist[1].split('-')[0]
        omcip = strtolist[12]
        if enbid not in enblist:
            enblist.append(enbid)
            numenb += 1
            # print(numenb)
            if strtolist[3] == '中兴' or strtolist[10] == '中兴':
                try:
                    enbdo += 1
                    mrftpget = ftpmrdo.ftpconn(
                        omcip, namezte, passwordzte, 2121, 0)
                    dirtarget = '/MR/' + data + '/'
                    mrftpget.cwd(dirtarget + enbid + '/')
                    direnbid = []
                    # get all filename and dir to list named direnbid
                    mrftpget.dir('', direnbid.append)
                    diractryz = []
                    fileitemz = []
                    alllistz = []
                    for line in direnbid:
                        # bring the file and dir from list-direnbid
                        temp = line.split(' ')
                        while '' in temp:
                            temp.remove('')
                        if 'd' in temp[0]:
                            diractryz.append(temp[8])
                            alllistz.append(temp[8])

                        else:
                            fileitemz.append(temp[8])
                            alllistz.append(temp[8])
                            mrftpget.delete(temp[8])

                    mrftpget.cwd(dirtarget)
                    mrftpget.rmd(enbid)
                    mrftpget.quit()
                    succlist.append(
                        (enbid, omcip, 'success', new, 'zte'))
                except all_errors as e:
                    faillist.append(
                        (enbid, omcip, str(e), new, 'zte'))
                    ztefail += 1
                else:
                    success += 1

            elif strtolist[3] == '华为' or strtolist[10] == '华为':
                enbdo += 1
                try:

                    sftphw = paramiko.Transport(omcip, 22)
                    sftphw.connect(username='ossuser',
                                   password='Changeme_123')
                    sftp = paramiko.SFTPClient.from_transport(sftphw)

                    while '-' in data:  # 2018-01-01 to 20180101
                        data = data.replace('-', '')

                    delpath = '/export/home/omc/var/fileint/TSNBI/LTESpecial/' + data + '/' + enbid
                    listtemp = sftp.listdir(delpath)
                    for t in listtemp:
                        sftp.remove(delpath + '/' + t)
                    sftp.rmdir(delpath)

                    sftp.close()
                    sftphw.close()
                    succlist.append(
                        (enbid, omcip, 'success', new, 'hw'))

                except Exception, e:
                    # print(e)
                    faillist.append(
                        (enbid, omcip, str(e), new, 'hw'))
                    hwfail += 1
                else:
                    success += 1

            elif strtolist[3] == '爱立信' or strtolist[10] == '爱立信':
                try:
                    enbdo += 1
                    nofile = 0
                    nodir = 0
                    tempsucc = 0
                    while '-' in data:
                        data = data.replace('-', '')
                    mrftpget = ftpmrdo.ftpconn(
                        omcip, 'mruser', 'mruser', 21, 0)
                    # print(data)
                    minute = ['00', '15', '30', '45']
                    hour = ['05', '06', '07', '08', '09', '10', '11', '12', '13',
                            '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']
                    for h in hour:
                        for m in minute:
                            try:

                                dirtarget = '/opt/MR/data/northbound/files/' + data + h + m + '/'
                                delmre = 'TDD-LTE_MRE_ERICSSON_OMC1_' + \
                                    enbid + '_' + data + h + m + '00.xml.zip'
                                delmro = 'TDD-LTE_MRO_ERICSSON_OMC1_' + \
                                    enbid + '_' + data + h + m + '00.xml.zip'
                                delmrs = 'TDD-LTE_MRS_ERICSSON_OMC1_' + \
                                    enbid + '_' + data + h + m + '00.xml.zip'
                                print(delmre)

                                # dirtarget =
                                # '/opt/MR/data/northbound/files/' +
                                # data + h+m+'/'
                                delmref = 'FDD-LTE_MRE_ERICSSON_OMC1_' + \
                                    enbid + '_' + data + h + m + '00.xml.zip'
                                delmrof = 'FDD-LTE_MRO_ERICSSON_OMC1_' + \
                                    enbid + '_' + data + h + m + '00.xml.zip'
                                delmrsf = 'FDD-LTE_MRS_ERICSSON_OMC1_' + \
                                    enbid + '_' + data + h + m + '00.xml.zip'

                                print(dirtarget)

                                mrftpget.cwd(dirtarget)
                                mrftpget.delete(delmro)
                                mrftpget.delete(delmrs)
                                mrftpget.delete(delmre)

                                tempsucc += 1
                            except Exception, e:
                                if 'Delete operation failed' in str(e):
                                    nofile += 1
                                elif 'Failed to change directory' in str(e):

                                    nodir += 1
                                try:

                                    dirtarget = '/opt/MR/data/northbound/files/' + data + h + m + '/'
                                    delmref = 'FDD-LTE_MRE_ERICSSON_OMC1_' + \
                                        enbid + '_' + data + h + m + '00.xml.zip'
                                    delmrof = 'FDD-LTE_MRO_ERICSSON_OMC1_' + \
                                        enbid + '_' + data + h + m + '00.xml.zip'
                                    delmrsf = 'FDD-LTE_MRS_ERICSSON_OMC1_' + \
                                        enbid + '_' + data + h + m + '00.xml.zip'
                                    mrftpget.delete(delmrof)
                                    mrftpget.delete(delmrsf)
                                    mrftpget.delete(delmref)
                                    tempsucc += 1
                                except Exception, e:
                                    print(str(e))
                            continue
                    mrftpget.quit()

                    if tempsucc > 0:
                        success += 1
                        succlist.append(
                            (enbid, omcip, 'success', new, 'eric'))
                    else:
                        ericfail += 1

                        faillist.append(
                            (enbid, omcip, str(e), new, 'eric'))
                except all_errors as e:
                    # error_perm.
                    print(e)
                    ericfail += 1
                    faillist.append(
                        (enbid, omcip, str(e), new, 'eric'))

            elif strtolist[3] == '诺西' or strtolist[10] == '诺基亚':
                try:
                    enbdo += 1
                    while '-' in data:
                        data = data.replace('-', '')
                    mrftpget = ftpmrdo.ftpconn(
                        omcip, 'richuser', 'richr00t')

                    dirtarget = '/home/richuser/l3fw_mr/kpi_import/' + data + '/'
                    mrftpget.cwd(dirtarget + enbid + '/')
                    direnbid = []
                    mrftpget.dir('', direnbid.append)

                    diractrye = []
                    fileiteme = []
                    allliste = []
                    for line in direnbid:
                        temp = line.split(' ')  # temp
                        while '' in temp:
                            temp.remove('')
                        if 'd' in temp[0]:
                            diractrye.append(temp[8])
                            allliste.append(temp[8])

                        else:
                            fileiteme.append(temp[8])
                            allliste.append(temp[8])
                            mrftpget.delete(temp[8])

                    mrftpget.cwd(dirtarget)
                    mrftpget.rmd(enbid)
                    mrftpget.quit()
                    succlist.append(
                        (enbid, omcip, 'success', new, 'nokia'))
                except all_errors as e:

                    faillist.append(
                        (enbid, omcip, str(e), new, 'nokia'))
                    nokiafail += 1
                else:
                    success += 1

            elif strtolist[3] != '厂家名称':
                # print(strtolist[3]+strtolist[11])
                undo += 1

                faillist.append(
                    (enbid, omcip, strtolist[3], new, strtolist[7]))
            else:
                pass
# store the result and email
    with codecs.open('/home/eyann/mypython/t1/faillist.txt', 'ab', 'utf-8') as ff:
        if faillist:
            for item in faillist:
                if item:
                    s = ftpmrdo._transferContent(item)
                    ff.write(s + '\n')

    localdir='/home/eyann/mypython/t1/'
    fname='success'+time.strftime('%Y%m%d')+'.txt'
    succfile='/home/eyann/mypython/t1/success'+time.strftime('%Y%m%d')+'.txt'

    with codecs.open(succfile, 'wb', 'utf-8') as fs:
        if succlist:
            for item in succlist:
                if item:
                    s = ftpmrdo._transferContent(item)
                    fs.write(s + '\n')


    if sendmail == 1:
        
        resultstring = '时间：%s,涉及基站数量： %s,成功删除MR站点数量: %s 异常未执行站点数: %s,中兴失败数：%s,华为失败数：%s,爱立信失败数：%s,诺西失败数：%s' % (
            time.strftime('%Y-%m-%d %H:%M:%S'), numenb, success, undo, ztefail, hwfail, ericfail, nokiafail)
        print(resultstring)

        if numenb - success + undo > 0:

            masg = sendmailt.makemailmulti("liyangsgs@ah.chinamobile.com", ["liyangsgs@ah.chinamobile.com", "15905519913@139.com", "15156870507@139.com"], '[出现失败]' + resultstring, resultstring,
                                           '/home/eyann/mypython/t1/faillist.txt', succfile)
            sendmailt.quicksendmail(masg)

        elif time.localtime()[3] > 21 and numenb - success + undo == 0:
            masg = sendmailt.makemailmulti("liyangsgs@ah.chinamobile.com", ["liyangsgs@ah.chinamobile.com", "15905519913@139.com", "15156870507@139.com"], '[SuccessMsg]' + resultstring, resultstring,
                                           '/home/eyann/mypython/t1/faillist.txt', succfile)
            sendmailt.quicksendmail(masg)
    if time.localtime()[3] > 22:
        try:
            ftpup=ftpmrdo.ftpconn('10.243.71.93', 'ltests', 'ltests123')
            ftpmrdo.uploadfile(ftpup,localdir,'/plr/',fname)
        except Exception,e:
            print(str(e))
    return [numenb, success, undo, ztefail, hwfail, ericfail, nokiafail]


def delmr_from_ftp():

    try:
        ftpget = ftpmrdo.ftpconn('10.243.71.93', 'ltests', 'ltests123')
        newlistpart = ftpmrdo.getNewfile(
            ftpget, '/rt_sts/', dirlocal, 2, 'mr_qci_alertfile')
        oldlistall = ftpmrdo.makedirlist(
            ftpget, '/rt_sts', 2)  # 得到新文件后，更新老文件列表

    except Exception, e:
        getftpwrong = str(e)
        subject = '[FTP断链]' + getftpwrong
        message = sendmailt.makemailtext("liyangsgs@ah.chinamobile.com", [
                                         "liyangsgs@ah.chinamobile.com", "cn.liyang@139.com"], subject, subject)
        sendmailt.quicksendmail(message)

    if newlistpart:
        filenum = len(newlistpart)
        for new in newlistpart:
            print('this is file:%s,time is %s' %
                  (new, time.strftime('%Y-%m-%d %H:%M:%S')))
            ftpmrdo.downloadfile(ftpget, dirlocal, '/rt_sts/', new)
            with codecs.open(dirlocal + '/' + new, 'rb', 'utf-8') as f:
                target = f.readlines()
            for t in target:
                strtolist = t.split('|')
                rows.append(strtolist)
            fileresult = delmrfile(rows, filenum)
            allenb += fileresult[0]
            allsucc += fileresult[1]
            allundo += fileresult[2]
            allztefail += fileresult[3]
            allhwfail += fileresult[4]
            allericfail += fileresult[5]
            allnokiafail += fileresult[6]
            filenum = filenum - 1
        resultstring = '时间：%s,执行文件个数: %s ,:涉及基站数量： %s,成功删除MR站点数量: %s 异常未执行站点数: %s,中兴失败数：%s,华为失败数：%s,爱立信失败数：%s,诺西失败数：%s' % (
            time.strftime('%Y-%m-%d %H:%M:%S'), len(newlistpart), allenb, allsucc, allundo,allztefail,allhwfail,allericfail,allnokiafail)
        print(resultstring)  
    else:
        print('there is no new file in FTP')


def delmr_from_file(filename):
    

    # file rows with |
    with codecs.open(filename, 'rb', 'utf-8') as f:
        target = f.readlines()
    for t in target:
        strtolist = t.split('|')
        rows.append(strtolist) 

    delmrfile(rows)



if __name__ == '__main__':


    sdate = time.strftime('%Y-%m-%d')
    # print(sdate)
    sqls = "select day,cgi,city,vendor,covertype,scenario,cell_scenario,chinesename, \
        iscore,sts_flag,omc_vendor,omc_idx, omc_ip,plr_ul_qci1,ulqci1_tunzi_rate,ulqci1_dantong_rate, \
        ulqci1_total,plr_dl_qci1,dlqci1_tunzi_rate,dlqci1_dantong_rate,dlqci1_total \
        from networkstructure \
        where (((ulqci1_tunzi_rate>0.01 or plr_ul_qci1>0.01) and ulqci1_total>500) or ((dlqci1_tunzi_rate>0.01 or plr_dl_qci1>0.01) and dlqci1_total>500)) \
        and day>='%s' and day<='%s'" % (sdate, sdate)
    rows = sqlselect(sqls)
    delmrfile(rows)
    


