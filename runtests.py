#!/usr/bin/env python

import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    print('Django: ', django.VERSION)
    print('Python: ', sys.version)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'django_ml_spam_filter.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(interactive=False)
    failures = test_runner.run_tests(['spam_filter'])
    sys.exit(bool(failures))
