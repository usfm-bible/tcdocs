
import os, re, zipfile
import pytest
import usfmtc
import xml.etree.ElementTree as et

def pytest_addoption(parser):
    parser.addoption("-D","--dir",help="Directory to search for test data (tests, usx files, dbl zips)")
    parser.addoption("-M","--matchdir",help="Only process directories that match this regular expression")

def pytest_report_teststatus(report, config):
    category, short, verbose = report.outcome, '.', report.outcome.upper()
    short = "F"
    if report.passed:
        short = "."
    elif report.skipped:
        short = "s"
    if report.when in ('setup', 'teardown', 'collect'):
        if category == "failed":
            category = "error"
            short = 'E'
        else:
            category = ""
    if config.getvalue('verbose') < 0:
        short = None
    return (category, short, verbose)

@pytest.hookimpl(hookwrapper=True)
def pytest_sessionfinish(session, exitstatus):
    if session.config.option.tbstyle == "auto":
        session.config.option.tbstyle = "short" if session.config.getvalue("verbose") >= 0 else "no"
    yield
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    if tr is None:
        return
    reports = tr.getreports("failed")
    summary = {}
    for r in reports:
        mod, f = r.location[2].split("[")
        f = os.path.splitext(os.path.basename(f.rstrip("]")))[0]
        summary.setdefault(mod, []).append(f)
    tr.write_line("")
    for k, v in sorted(summary.items()):
        tr.write_line("{} ({}): {}".format(k, len(v), ", ".join(v)))

def pytest_generate_tests(metafunc):
    jobs = []
    basedir = metafunc.config.getoption("dir")
    if basedir is None:
        basedir = os.path.join(os.path.dirname(__file__), '..', "tests")
    for dp, db, fn in os.walk(basedir):
        for f in fn:
            if f.lower().endswith(".zip"):
                jobs.extend(zip_getfiles(os.path.join(dp, f)))
            elif f.lower() == "origin.xml" or f.lower().endswith(".usx"):
                jobs.extend(dir_getfiles(dp))
                break
    m = None
    matchr = metafunc.config.getoption("matchdir")
    if matchr is not None:
        m = re.compile(matchr)
        jobs = [j for j in jobs if m.search(j[0])]
    if len(jobs):
        metafunc.parametrize(("projectdir", "projectfile"), jobs, scope="session")

def zip_getfiles(zipname):
    allfiles = []
    with zipfile.ZipFile(zipname, "r") as zf:
        for fn in zf.namelist():
            if fn.lower().endswith(".usx"):
                allfiles.append((zipname, fn))
    return allfiles

def dir_getfiles(pdir):
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
            u = usfmtc.readFile(testfile, informat="usx")
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
            return u

