#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
    Dealing with transcripts
    
    JL Meunier - September 2017

    Copyright Naver(C) 2017 JL. Meunier

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
    
    Developed  for the EU project READ. The READ project has received funding 
    from the European Union’s Horizon 2020 research and innovation programme 
    under grant agreement No 674943.

"""
from __future__ import absolute_import
from __future__ import  print_function
from __future__ import unicode_literals

#    TranskribusCommands/do_LAbatch.py 3571 3820 8251 8252


#optional: useful if you want to choose the logging level to something else than logging.WARN
import sys, os, logging
from optparse import OptionParser
import json
from io import open


try: #to ease the use without proper Python installation
    import TranskribusPyClient_version
except ImportError:
    sys.path.append( os.path.dirname(os.path.dirname( os.path.abspath(sys.argv[0]) )) )
    import TranskribusPyClient_version

from TranskribusCommands import _Trnskrbs_default_url, __Trnskrbs_basic_options, _Trnskrbs_description, __Trnskrbs_do_login_stuff, _exit
from TranskribusPyClient.client import TranskribusClient
from TranskribusPyClient.common.IntegerRange  import IntegerRange as PageRangeSpec
from TranskribusPyClient.common.DateTimeRange import DateTimeRange as DateTimeRangeSpec
from TranskribusPyClient.TRP_FullDoc import TRP_FullDoc

from TranskribusPyClient.common.trace import traceln, trace

DEBUG = 0

description = """Managing the transcripts of one or several document(s) or of a whole collection.
""" + _Trnskrbs_description

usage = """%s <colId> <docId> [<page-ranges>] 
    [--last] 
    [--within <date>/<date>]+ [--at <date>]+ [--after <date>] [--before <date>] [--utc] 
    [--user <username>]+
    [--status <status>]+ 
    [--last_filtered]
    [--check_user <username>]+
    [--check_status <status>]+ 
    [--trp <file]
    [<operation>]

Operation is one of --list, --rm, --set_status

Use this command to selectively list or remove the transcripts of a document, or update their status.
This command works in 3 stages:
Step 1 - FILTERING: you can look at all transcripts per page or only the last one. Then you can filter 
        based on the page number, or the transcript date, status, author. The command does a AND of all
         filters, in other words, a selected transcript satisfies all filters. After filtering, you can 
         also keep only the last transcript per page.
Step 2 - CHECKING: you can check that the transcripts selected by the filter verify certain conditions
        , based on transcript status and author. If the condition is not met for one or more selected 
        transcript(s), the operation is not performed (apart the 'list' operation)
Step 3 - ACTING: an operation applies to the selected transcript, currently you can list, remove them 
        or update their status.

Page range is a comma-separated series of integer or pair of integers separated by a '-' 
For instance 1  or 1,3  or 1-4 or 1,3-6,8

Prefixing a username or a status by / negates the filter, e.g. --user=/jdoe .
    To escape a / at beginning of a value, use /, e.g. --user=//strangeusername

Date takes the form: 
        YYYY-MM-DDThh:mm:ss+HHMM  like 2017-09-04T18:30:20+0100 
        YYYY-MM-DDThh:mm:ss-HHMM  like 2017-09-04T18:30:20-0100 
        YYYY-MM-DDThh:mm:ssZ  like 2017-09-04T18:30:20Z 
        If you omit the time, than it is the first millisecond of the day (of the guessed timezone)
Alternatively, it can be a timestamp (number of milliseconds since 1970-01-01)
--utc option will show UTC times

--trp stores the trp data reflecting the filtered transcripts in the given file

"""%sys.argv[0]

class DoTranscript(TranskribusClient):
    sDefaultServerUrl = _Trnskrbs_default_url
    #--- INIT -------------------------------------------------------------------------------------------------------------    
    def __init__(self, trnkbsServerUrl, sHttpProxy=None, loggingLevel=logging.WARN):
        TranskribusClient.__init__(self, sServerUrl=self.sDefaultServerUrl, proxies=sHttpProxy, loggingLevel=loggingLevel)
    
    def filter(self, colId, docId
               , page_filter=None, time_filter=None, user_filter=(None,None), status_filter=(None,None)
               , bVerbose=False
               , bLast=False, bLastFiltered=False):
        """
        return a TRP containing the transcripts, excluding the ones filtered out.
        """
        if bLast:
            #consider only last transcript per page
            if bVerbose: traceln("\t[filter] ignore all but last transcript of each page")
            trp = TRP_FullDoc(self.getDocById(colId, docId, 1))
        else:
            trp = TRP_FullDoc(self.getDocById(colId, docId, -1))
    
        if page_filter:
            if bVerbose: 
                trace("\t[filter] as per page specification: %s"%page_filter)
                n0 = len(trp.getPageList())
            trp.filterPageList(page_filter)
            if bVerbose: 
                n1 = len(trp.getPageList())
                traceln(" --> %d pages in-scope (after excluding %d)"%(n1, n0-n1))
        
        for filter, filter_name, slot in [  (time_filter, "time", "timestamp")]:
            if filter:
                if bVerbose: 
                    trace("\t[filter] as per %s specification: %s"%(filter_name, filter))
                    n0 = len(trp.getTranscriptList())
                trp.filterTranscriptsBySlot(filter, slot)
                if bVerbose: 
                    n1 = len(trp.getTranscriptList())
                    traceln(" --> %d transcripts in-scope (after excluding %d)"%(n1, n0-n1))

        for (filter_pos, filter_neg), filter_name, slot in [  (user_filter, "user", "userName")
                                          , (status_filter, "status", "status")]:
            if filter_pos or filter_neg:
                if bVerbose: 
                    if filter_pos: trace("\t[filter] as per %s specification: keeping   %s"%(filter_name, filter_pos))
                    if filter_neg: trace("\t[filter] as per %s specification: excluding %s"%(filter_name, filter_neg))
                    n0 = len(trp.getTranscriptList())
                if filter_pos: trp.filterTranscriptsBySlot(filter_pos, slot)
                if filter_neg: trp.filterTranscriptsBySlot(filter_neg, slot, bNot=True)
                if bVerbose: 
                    n1 = len(trp.getTranscriptList())
                    traceln(" --> %d transcripts in-scope (after excluding %d)"%(n1, n0-n1))

        if bLastFiltered:
            if bVerbose: 
                trace("\t[filter] keep last filtered transcript per page")
                n0 = len(trp.getTranscriptList())
            trp.filterLastTranscript()
            if bVerbose: 
                n1 = len(trp.getTranscriptList())
                traceln(" --> %d transcripts in-scope (after excluding %d)"%(n1, n0-n1))
        return trp
    
    @classmethod
    def _getUnescapedValue(cls, s, cNeg='/'):
        """
        unescape the start of the string
        return a pair (bIsNegated, unescaped-string)
        e.g.  "jdoe" --> False, "jdoe"
        e.g.  "/jdoe" --> True, "jdoe"
        e.g.  "//jdoe" --> False, "/jdoe"
        e.g.  "///jdoe" --> True, "/jdoe"
        e.g.  "////jdoe" --> False, "//jdoe"
        """
        assert len(cNeg) == 1
        i = 0
        while i<len(s) and s[i]=='/': i += 1
        #i points to the first character which is not the negation character
        bNeg = bool(i%2)
        sPref, sSuf = s[:i].replace(cNeg+cNeg, cNeg), s[i:]  #i/2 might pose pb with Python3
        if bNeg: sPref = sPref[1:] # remove the slash
        return bNeg, sPref+sSuf
        
    @classmethod
    def splitPosNeg(cls, lSpecifiedValue, cNeg='/'):
        """
        Split the list of specified value into positive and negative value lists
        """
        if lSpecifiedValue == None: return None, None #convenience
        lbNegText = [cls._getUnescapedValue(s) for s in lSpecifiedValue]
        return (   [ s for b, s in lbNegText if b==False]
                ,  [ s for b, s in lbNegText if b==True ] )
        
    def check(self, trp, t_user_check=None, t_status_check=None, bVerbose=False):
        """
        Check those conditions, and raises a ValueError if some condition is not met
        return True
        """
        user_check_pos, user_check_neg = t_user_check
        if user_check_pos or user_check_neg:
            lUser = trp.getTranscriptUsernameList()
            if user_check_pos:
                if bVerbose: traceln("\t[check] required user(s): %s"%user_check_pos)
                if not set(user_check_pos).issuperset(set(lUser)):
                    if bVerbose:
                        lExtra = list(set(lUser).difference(set(user_check_pos)))
                        lExtra.sort()
                        traceln("\tERROR: selected transcript include those usernames: ", lExtra)
                    raise ValueError("Extra user(s) found.")
            if user_check_neg:
                if bVerbose: traceln("\t[check] excluded user(s): %s"%user_check_neg)
                if not set(user_check_neg).isdisjoint(set(lUser)):
                    if bVerbose:
                        lExtra = list(set(lUser).intersection(set(user_check_neg)))
                        lExtra.sort()
                        traceln("\tERROR: selected transcript include those usernames: ", lExtra)
                    raise ValueError("Excluded user(s) found.")
            
        status_check_pos, status_check_neg = t_status_check
        if status_check_pos or status_check_neg:
            lStatus = trp.getTranscriptStatusList()
            if status_check_pos:
                if bVerbose: traceln("\t[check] required status(es): %s"%status_check_pos)
                if not set(status_check_pos).issuperset(set(lStatus)):
                    if bVerbose:
                        lExtra = list(set(lStatus).difference(set(status_check_pos)))
                        lExtra.sort()
                        traceln("\tERROR: selected transcript include those status(es): ", lExtra)
                    raise ValueError("Extra status(es) found.")
            if status_check_neg:
                if bVerbose: traceln("\t[check] excluded status(es): %s"%status_check_neg)
                if not set(status_check_neg).isdisjoint(set(lStatus)):
                    if bVerbose:
                        lExtra = list(set(lStatus).intersection(set(status_check_neg)))
                        lExtra.sort()
                        traceln("\tERROR: selected transcript include those status(es): ", lExtra)
                    raise ValueError("Extra status(es) found.")

        return True
    
    def deleteTranscripts(self, trp, bVerbose=True):
        """
        Delete the transcripts listed in the trp
        """
        colId = trp.getCollectionId()
        ldTr = trp.getTranscriptList()
        
        for dTr in ldTr:
            docId = dTr["docId"]
            pnum = dTr["pageNr"]
            sKey = dTr["key"]
            if bVerbose:
                traceln("\tdeleting %s %s p%s transcript %s"%(colId, docId, pnum, sKey))
                traceln(self.deletePageTranscript(colId, docId, pnum, sKey))
        return True
    
    def setTranscriptStatus(self, trp, status, bVerbose=True):
        """
        Set the status of the transcripts listed in the trp
        """
        colId = trp.getCollectionId()
        ldTr = trp.getTranscriptList()
        
        for dTr in ldTr:
            docId = dTr["docId"]
            pnum = dTr["pageNr"]
            sTSId = dTr["tsId"]
            if bVerbose:
                traceln("\tsetting status to '%s' for %s %s p%s transcript %s"%(status, colId, docId, pnum, sTSId))
                traceln(self.updatePageStatus(colId, docId, pnum, sTSId, status, "setStatus by PyClient"))
        return True

    
#--- SELF-TESTs
def test_Escaping():
    assert (None, None) == DoTranscript.splitPosNeg(None)
    assert ([], []) == DoTranscript.splitPosNeg( [])
    assert (["jdoe"], [])       == DoTranscript.splitPosNeg( ["jdoe"])
    assert ([]      , ["jdoe"]) == DoTranscript.splitPosNeg( ["/jdoe"])
    
    assert ([""]    , [])       == DoTranscript.splitPosNeg( [""])
    assert ([]      , [""]) == DoTranscript.splitPosNeg( ["/"])

    assert (["/jdoe"], [])        == DoTranscript.splitPosNeg( ["//jdoe"])
    assert ([]       , ["/jdoe"]) == DoTranscript.splitPosNeg( ["///jdoe"])
    
    assert (["//jdoe"], [])         == DoTranscript.splitPosNeg( ["////jdoe"])
    assert ([]        , ["//jdoe"]) == DoTranscript.splitPosNeg( ["/////jdoe"])
    
    assert (["//jd/o/e/"], [])            == DoTranscript.splitPosNeg( ["////jd/o/e/"])
    assert ([]           , ["//jd/o/e/"]) == DoTranscript.splitPosNeg( ["/////jd/o/e/"])
    
    assert (["/jdoe", "pierre"], ["paul"]) == DoTranscript.splitPosNeg( ["//jdoe", "/paul", "pierre"] )
    
#--------------------------------------------------------------------------------------------------------------------------------------------                    
if __name__ == '__main__':
    version = "v1.0"

    #prepare for the parsing of the command line
    parser = OptionParser(usage=usage, version=version)
    parser.description = description
    
    #"-s", "--server",  "-l", "--login" ,   "-p", "--pwd",   "--https_proxy"    OPTIONS
    __Trnskrbs_basic_options(parser, DoTranscript.sDefaultServerUrl)
    parser.add_option("--last"          , dest='last'           , action="store_true" , default=False, help="filter (i.e. keep) only last transcript of each page before any filtering occurs.")
    parser.add_option("--after" , dest='after' , action="store", type="string", default=None         , help="filter (i.e. keep) transcripts created on or after this date.")
    parser.add_option("--before", dest='before', action="store", type="string", default=None         , help="filter (i.e. keep) transcripts created on or before this date.")
    parser.add_option("--within", dest='within', action="append", type="string", default=None        , help="filter (i.e. keep) transcripts created within this range(s) of dates.")
    parser.add_option("--at"    , dest='at'    , action="append", type="string", default=None        , help="filter (i.e. keep) transcripts created at a date(s).")
    parser.add_option("--user"  , dest='user'  , action="append", type="string", default=None        , help="filter (i.e. keep) transcripts that were authored by this or these users.")
    parser.add_option("--status", dest='status', action="append", type="string", default=None        , help="filter (i.e. keep) transcripts that have this or these status(es).")
    parser.add_option("--last_filtered" , dest='last_filtered'  , action="store_true" , default=False, help="filter (i.e. keep) only last transcript, if any, of each page (done after any other filter).")
    parser.add_option("--check_user"  , dest='check_user'   , action="append", type="string", default=None, help="Check that each filtered transcript was authored by one of these users.")
    parser.add_option("--check_status", dest='check_status' , action="append", type="string", default=None, help="Check that each filtered transcript have on of these statuses.")

    parser.add_option("--utc"   , dest='utc'     , action="store_true", default=False, help="Show UTC time.")
    parser.add_option("--trp"   , dest='trp'     , action="store", type="string", default=None, help="Store the TRP data reflecting the filtered transcripts in the given file.")
    
    parser.add_option("--list"      , dest='op_list'    , action="store_true", default=False, help="List   the filtered transcripts.")
    parser.add_option("--rm"        , dest='op_rm'      , action="store_true", default=False, help="Remove the filtered transcripts. (CAUTION)")
    parser.add_option("--set_status", dest='set_status' , action="store", type="string", default=None, help="Set the filtered transcripts' status.")
        
    # ---   
    #parse the command line
    (options, args) = parser.parse_args()
    proxies = {} if not options.https_proxy else {'https_proxy':options.https_proxy}

    # --- 
    doer = DoTranscript(options.server, proxies, loggingLevel=logging.WARN)
    __Trnskrbs_do_login_stuff(doer, options, trace=trace, traceln=traceln)
    # --- 
    try:                        colId = int(args.pop(0))
    except Exception as e:      _exit(usage, 1, e)
    try:                        docId = int(args.pop(0))
    except Exception as e:      _exit(usage, 1, e)
    #docId           = int(args.pop(0)) if args else None
    sPageRangeSpec  = args.pop(0)      if args else None

    if args:                    _exit(usage, 2, Exception("Extra arguments to the command"))

    #PAGE RANGE FILTER
    oPageRange = PageRangeSpec(sPageRangeSpec) if sPageRangeSpec else None
    
    #TIME RANGE FILTER
    if options.utc:  DateTimeRangeSpec.setUTC(True)
    oTimeRange = DateTimeRangeSpec()
    if options.before:
        oTimeRange.addEndsBefore(options.before)
    if options.after:
        oTimeRange.addStartsAfter(options.after)
    if options.within:
        for sA_slash_B in options.within:
            sA, sB = sA_slash_B.split("/")
            oTimeRange.addRange(sA, sB)
    if options.at:
        for sA in options.at:
            oTimeRange.addRange(sA, sA)
    if not oTimeRange: oTimeRange = None

    #FILTERS
    lUser  , lUserNeg   = doer.splitPosNeg(options.user)
    lStatus, lStatusNeg = doer.splitPosNeg(options.status)
    #CHECKs
    lUserCheck  , lUserCheckNeg   = doer.splitPosNeg(options.check_user   if options.check_user   else None)
    lStatusCheck, lStatusCheckNeg = doer.splitPosNeg(options.check_status if options.check_status else None)
    
    # --- 
    traceln("colid=%s  docid=%s"%(colId, docId))
    # get a filtered TRP data
    trp = doer.filter(colId, docId, page_filter=oPageRange
                      , time_filter=oTimeRange, user_filter=(lUser, lUserNeg), status_filter=(lStatus, lStatusNeg)
                      , bLast=options.last
                      , bLastFiltered=options.last_filtered
                      , bVerbose=True)

    #CHECKs
    try:
        doer.check(trp, t_user_check=(lUserCheck, lUserCheckNeg), t_status_check=(lStatusCheck, lStatusCheckNeg), bVerbose=True) 
    except ValueError:
        traceln(" --- ERROR ---")
        traceln(trp.report_short(warn="!"))
        traceln("ERROR: some check(s) failed.")
        sys.exit(3)

    if options.trp:
        #dump the Trp on stdout and list on stderr
        traceln(" - storing TRP data in %s"%options.trp)
#         with open(options.trp, "wb",encoding='utf-8') as fd: json.dump(trp.getTRP(), fd, sort_keys=True, indent=2, separators=(',', ': '))
        #sys.version_info(major=2, minor=7, micro=13, releaselevel='final', serial=0)
        if sys.version_info > (3,0):
            with open(options.trp, "wt",encoding='utf-8') as fd: 
                json.dump(trp.getTRP(), fd, sort_keys=True, indent=2, separators=(',', ': '))
        else:
            with open(options.trp, "wb") as fd: 
                json.dump(trp.getTRP(), fd, sort_keys=True, indent=2, separators=(',', ': '))
                
    traceln()
    
    if options.op_rm == True:
        #delete the transcripts remaining in trp !
        doer.deleteTranscripts(trp, bVerbose=True)
    elif options.set_status != None:
        doer.setTranscriptStatus(trp, options.set_status, bVerbose=True)
    else:
        #by default we list
        print(trp.report_short())
        traceln()
        traceln(trp.report_stat())
        
    traceln()      
    traceln("- Done")
    
    

    
    
    