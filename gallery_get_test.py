import os, re, csv
import gallery_get, reddit_get
from gallery_utils import *
from optparse import OptionParser

DEST_ROOT = gallery_get.DEST_ROOT
INPUT_PATH = "gallery_get_test_input.csv"
OUTPUT_PATH = "gallery_get_test_output.csv"
FAILED_TEST_CASES = []

parser = OptionParser()
parser.add_option(
        '--noprompt', dest='noprompt', action='store_true', default=False,
        help='don\'t prompt for extra galleries')
parser.add_option(
        '--input', dest='input_path', default=INPUT_PATH,
        help='input CSV for testing (same format as output)')
(options, args) = parser.parse_args()


### TESTING CLASSES

class GalleryTest(object):
  def __init__(self, debugname):
    self.debugname = debugname
    self.title = ""
    self.files = []
    self.size = 0
    self.status = None
    print("")
    print("Testing " + debugname)

  def post_run(self, root, success, params):
    
    if root:
      self.title = encode_safe(os.path.basename(root))
      for (dirpath, dirnames, filenames) in os.walk(root):
        self.files += filenames
        for filename in filenames:
          self.size += os.path.getsize(os.path.join(dirpath,filename))
    self.status = True if (success and root and self.size) else False
    if not self.status:
      FAILED_TEST_CASES.append("DOWNLOADS FAILED in %s: Please check messages above." % self.debugname)
    if params:
      self.compare(*params)


  def _compare_internal(self, real_val, expected_val, name, allow_greater=False):
    global FAILED_TEST_CASES
    if expected_val and (real_val != expected_val):
      if allow_greater and (real_val > expected_val):
        FAILED_TEST_CASES.append("TEST NEEDS UPDATE for %s: %s = %s (expected %s)" % (self.debugname, name, str(real_val), str(expected_val)))
      else:
        FAILED_TEST_CASES.append("TEST FAILED in %s: %s = %s (expected %s)" % (self.debugname, name, str(real_val), str(expected_val)))
        self.status = False

  def compare(self, title="", num_files=0, size=0):
    global FAILED_TEST_CASES
    self._compare_internal(self.title, title, "title")
    self._compare_internal(len(self.files), int(num_files), "number of files", True)
    self._compare_internal(self.size, int(size), "total size", True)
    return self.status


class GalleryGetTest(GalleryTest):
  def __init__(self, params):
    self.url = params[0]
    GalleryTest.__init__(self, self.url)

    root = gallery_get.run_wrapped(self.url, "", flushJobs=False)
    success = gallery_get.flush_jobs()
    self.post_run(root, success, params[1:])


class RedditGetTest(GalleryTest):
  def __init__(self, params):
    self.user = params[0]
    GalleryTest.__init__(self, self.user)

    root = reddit_get.run_wrapped(self.user, "", False)
    success = gallery_get.flush_jobs()
    self.post_run(root, success, params[1:])


### REPORTING METHODS

def read_input(input_path):
  rows = []
  if os.path.exists(input_path):
    report_file = open(input_path,"r")
    reader = csv.reader(report_file)
    rows = list(reader)[1:]
    report_file.close()
  return rows


def write_report(results, output_path):
  if not results:
    print("Nothing to test!")
    return

  report = ["URL/User,Title,Files,Size"]
  for result in results:
    report.append("%s,%s,%d,%d" % (result.debugname, result.title, len(result.files), result.size))

  file = open(output_path,"w")
  file.write("\n".join(report))
  file.close()

  print("")
  if FAILED_TEST_CASES:
    print("="*40)
    print("\n".join(FAILED_TEST_CASES))
    print("="*40)

  succeeded = sum(test.status == True for test in results)
  failed = sum(test.status == False for test in results)
  pending = sum(test.status == None for test in results)
  if pending > 0:
    print("Summary: %d succeeded, %d failed, %d ready to add" % (succeeded, failed, pending))
  else:
    print("Summary: %d succeeded, %d failed" % (succeeded, failed))
  print("Results written to %s" % output_path)
  print("")


### RUN TESTS AND WRITE REPORT

tests = read_input(options.input_path)
if not options.noprompt:
  while True:
    extra_test = str_input("Extra URL or Reddit user to test (blank for none): ")
    if extra_test:
      tests.append([extra_test])
    else:
      break

results = []
for row in tests:
  if re.match("\A[A-Za-z0-9_]+\Z", row[0]):
    results.append(RedditGetTest(row))
  else:
    results.append(GalleryGetTest(row))

write_report(results, OUTPUT_PATH)

