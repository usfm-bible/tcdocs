
import os, re, zipfile
import pytest
import usfmtc
import xml.etree.ElementTree as et

def pytest_addoption(parser):
    parser.addoption("-D","--dir",help="Directory to search for test data (tests, usx files, dbl zips)")
    parser.addoption("-M","--matchdir",help="Only process directories that match this regular expression")

def pytest_generate_tests(metafunc):
    jobs = []
    basedir = metafunc.config.getoption("dir")
    print(basedir)
    if basedir is None:
        basedir = os.path.join(os.path.dirname(__file__), '..', "tests")
    for dp, db, fn in os.walk(basedir):
        for f in fn:
            if f.lower().endswith(".zip"):
                jobs.extend(zip_getfiles(os.path.join(dp, f)))
            elif f.lower() == "origin.xml" or f.lower().endswith(".usx"):
                jobs.extend(dir_gettestfiles(dp))
                break
            elif f.lower().endswith(".usfm") or f.lower().endswith(".sfm"):
                if basedir == dp:
                    jobs.append((dp, f))
    m = None
    matchr = metafunc.config.getoption("matchdir")
    if matchr is not None:
        m = re.compile(matchr)
        jobs = [j for j in jobs if m.search(j[0])]
    if len(jobs):
        metafunc.parametrize(("projectdir", "projectfile"), jobs, scope="session")

def zip_getfiles(zipname):
    allfiles = []
    try:
        with zipfile.ZipFile(zipname, "r") as zf:
            for fn in zf.namelist():
                if fn.lower().endswith(".usx"):
                    allfiles.append((zipname, fn))
    except zipfile.BadZipFile:
        pass
    return allfiles

def dir_gettestfiles(pdir):
    allfiles = []
    for fn in os.listdir(pdir):
        if fn.lower().endswith(".usx"):
            allfiles.append((pdir, fn))
    if not len(allfiles):
        testfile = os.path.join(pdir, "origin.xml")
        if os.path.exists(testfile):
            allfiles.append((pdir, "origin.xml"))
    return allfiles

@pytest.fixture(scope="module")
def usfm(projectdir, projectfile):
    if projectdir.lower().endswith(".zip"):
        with zipfile.ZipFile(projectdir, "r") as zf:
            if projectfile in zf.namelist():
                with zf.open(projectfile, "r") as inf:
                    u = usfmtc.readFile(inf, informat="usx")
                    u.fname = projectfile
                    u.base = projectdir
                    u.xfails = []
                    return u
    elif os.path.isdir(projectdir):
        testfile = os.path.join(projectdir, projectfile)
        if os.path.exists(testfile):
            u = usfmtc.readFile(testfile, informat="usx" if projectfile.endswith(".xml") else None)
            u.fname = projectfile
            u.base = projectdir
            u.xfails = []
            if projectfile == 'origin.xml':
                meta = os.path.join(projectdir, 'metadata.xml')
                if os.path.exists(meta):
                    doc = et.parse(meta)
                    xf = doc.findtext('.//pytest')
                    if xf:
                        u.xfails = xf.split(' ')
            u.addesids()
            return u

def pytest_report_teststatus(report, config):
    restype = {"passed": "", "failed": "+", "skipped": "-"}
    failtype = {"test_simple.py::test_textinnotes": "n"}
    if report.when == "call":
        tid = report.nodeid[:report.nodeid.find("[")]       # "module::testfn[zipfilepath-inzippath]"
        if report.outcome == "failed":
            short = failtype.get(tid, restype["failed"])
        else:
            short = restype[report.outcome]
        return report.outcome, short, report.outcome.upper()

@pytest.hookimpl(hookwrapper=True)
def pytest_sessionfinish(session, exitstatus):
    if session.config.option.tbstyle == "auto":
        session.config.option.tbstyle = "no"
        session.config.option.no_summary = True
    yield
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    if tr is None:
        return
    reports = tr.getreports("failed")
    summary = {}
    base = session.config.option.dir
    for r in reports:
        m = re.match(r"^(.*?)\[(.*?)-(.*?)\]", r.location[2])
        if m:
            test, zfile, zcontent = m.groups()
            zname = os.path.relpath(zfile, base)
            summary.setdefault(test, {}).setdefault(zname, []).append(os.path.splitext(os.path.basename(zcontent))[0])
    tr.write_line("")
    for t, i in sorted(summary.items()):
        for k, v in sorted(i.items()):
            tr.write_line("{}:{} ({}): {}".format(t, k, len(v), ", ".join(v)))

