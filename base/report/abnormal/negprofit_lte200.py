#-*- coding:utf-8 -*-
__author__ = 'liubf'

import datetime
import decimal
import json

import xlwt as xlwt
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from base.models import Kgprofit,BasPurLog
from base.report.common import Method as reportMth
from base.utils import DateUtil,MethodUtil as mtu
from base.report.common import Excel


def query(date):
    rbacDepartList, rbacDepart = reportMth.getRbacDepart(11)
    rbacClassList, rbacClass = reportMth.getRbacClass()

    karrs = {}
    karrs.setdefault("bbdate", "{start}".format(start=date))
    karrs.setdefault("profit__lte", "{profit}".format(profit=-200))
    karrs.setdefault("shopid__in", rbacDepartList)
    karrs.setdefault("deptid__in", rbacClassList)

    rlist = Kgprofit.objects\
            .values("bbdate", "sdate", "shopid", "shopname", "goodsid", "goodsname", "deptid",
                    "deptname", "qty", "profit", "stockqty", "truevalue", "costvalue") \
            .filter(**karrs).order_by("bbdate", "shopid", "goodsid", "sdate")

    formate_data(rlist)
    data = {"rlist": list(rlist)}

    return data

@cache_page(60 * 2 ,key_prefix='abnormal_negprofit_lte_200')
@csrf_exempt
def index(request):
     yesterday = DateUtil.get_day_of_day(-1)

     qtype = mtu.getReqVal(request, "qtype", "1")
     #操作日志
     if not qtype:
         qtype = "1"
     path = request.path
     today = datetime.datetime.today()
     ucode = request.session.get("s_ucode")
     uname = request.session.get("s_uname")
     BasPurLog.objects.create(name="负毛利大于200",url=path,qtype=qtype,ucode=ucode,uname=uname,createtime=today)

     if qtype == "1":
         data = query(yesterday)
         return render(request, "report/abnormal/negprofit_lte200.html", data)
     else:
         fname = yesterday.strftime("%m.%d") + "_abnormal_negprofit_lte200.xls"
         return export(fname,yesterday)


def export(fname,yesterday):
    if not Excel.isExist(fname):
        data = query(yesterday)
        createExcel(fname, data['rlist'])
    res = {}
    res['fname'] = fname
    return HttpResponse(json.dumps(res))

def createExcel(fname,data):
    wb = xlwt.Workbook(encoding='utf-8',style_compression=0)
    writeDataToSheet1(wb,data)
    Excel.saveToExcel(fname, wb)


def writeDataToSheet1(wb,data):
    sheet = wb.add_sheet("负毛利大于200",cell_overwrite_ok=True)

    titles = [[("负毛利大于200" ,0,1,15)],
              [("机构编码",0,1,1),("机构名称",1,1,1),("销售日期",2,1,1),("商品编码",3,1,1),("商品名称",4,1,1),
               ("管理类别编码",5,1,1),("管理类别名称",6,1,1),("销售金额",7,1,1),("销售数量",8,1,1),("成本金额",9,1,1),
               ("亏损金额",10,1,1),("库存数量",11,1,1),("解释原因",12,1,1),("解决方案",13,1,1),("解决时间",14,1,1)],
              ]

    keylist = ['shopid','shopname','sdate','goodsid','goodsname','deptid','deptname','truevalue','qty',
               'costvalue','profit','stockqty','solvereason','solvesolution','solvetime']
    widthlist = [800,1000,800,800,2000,800,800,800,800,800,800,800,800,800,800]

    mtu.insertTitle2(sheet,titles,keylist,widthlist)
    mtu.insertCell2(sheet,2,data,keylist,None)

def formate_data(rlist):
    for rows in rlist:
        for k in rows.keys():
            item = rows[k]
            if isinstance(item,decimal.Decimal):
                rows[k] = "%0.2f" % float(item)
            if isinstance(item,datetime.datetime):
                rows[k] = item.strftime("%Y-%m-%d")

