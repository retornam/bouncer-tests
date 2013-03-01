#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import requests
from urlparse import urlparse
from urllib import urlencode
from unittestzero import Assert

from base import Base


class TestRedirects(Base):

    # fails when run against stage - xfailed for https://bugzilla.mozilla.org/show_bug.cgi?id=801928
    @pytest.mark.xfail("config.getvalue('base_url') == 'http://download.allizom.org'")
    def test_that_checks_redirect_using_incorrect_query_values(self, testsetup):
        param = {
            'product': 'firefox-16.0b6',
            'lang': 'kitty_language',
            'os': 'stella'
        }
        url = testsetup.base_url
        response = self._head_request(url, params=param)

        Assert.equal(response.status_code, requests.codes.not_found, 'Failed on %s \nUsing %s' % (url, param))

        parsed_url = urlparse(response.url)
        Assert.equal(parsed_url.scheme, 'http',
        'Failed by redirected to HTTPS on %s \n \
        Using %s \n \
        Redirect to %s' % \
        (url, param, response.url))
        Assert.equal(parsed_url.netloc, urlparse(url).netloc, 'Failed on %s \nUsing %s' % (url, param))
        Assert.equal(parsed_url.query, urlencode(param), 'Failed on %s \nUsing %s' % (url, param))

    def test_that_checks_firefox_nineteen_redirects_for_win8(self,testsetup):
        #This test checks that the product firefox-19.0 redirects to firefox-19.0.1 on Windows 8
        #
        user_agent ="Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)"
        param = {
            'product': 'firefox-19.0',
            'lang': 'en-US',
            'os': 'win'
        }
        
        url= testsetup.base_url
        response = self._head_request(url, user_agent=user_agent, params=param)
        Assert.contains( '19.0.1', response.url)
    
    def test_that_checks_other_windows_user_agents_for_firefox_nineteen_redirects(self, testsetup):
        #This test checks that Windows user agents below NT 6.2 are redirected to firefox-19.0
        user_agent = "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)"
        param = {
            'product': 'firefox-19.0',
            'lang': 'en-US',
            'os': 'win'
        }
        url = testsetup.base_url
        response = self._head_request(url, user_agent=user_agent, params=param)
        Assert.contains("19.0.exe", response.url)
        
    def test_that_checks_redirect_using_locales_and_os(self, testsetup, lang, os):

        url = testsetup.base_url

        # Ja locale has a special code for mac
        if lang == 'ja' and os == 'osx':
            lang = 'ja-JP-mac'

        param = {
            'product': 'firefox-16.0b6',
            'lang': lang,
            'os': os
        }

        response = self._head_request(url, params=param)

        parsed_url = urlparse(response.url)

        Assert.equal(response.status_code, requests.codes.ok,
            'Redirect failed with HTTP status %s on %s \n \
            For %s\n \
            Redirected to %s' % \
            (response.status_code, url, param, response.url))
        Assert.equal(parsed_url.scheme, 'http', 'Failed on %s \nUsing %s' % (url, param))

    @pytest.mark.xfail(reason='there currently is not a stub installer -- xfailing until one lands in the wild')
    def test_stub_installer_redirect_for_en_us_and_win(self, testsetup):
        url = testsetup.base_url
        param = {
            'product': testsetup.product,
            'lang': 'en-US',
            'os': 'win'
        }

        response = self._head_request(url, params=param)

        parsed_url = urlparse(response.url)

        Assert.equal(response.status_code, requests.codes.ok, 'Failed on %s \nUsing %s' % (url, param))
        Assert.equal(parsed_url.scheme, 'https', 'Failed on %s \nUsing %s' % (url, param))
        Assert.equal(parsed_url.netloc, 'download-installer.cdn.mozilla.net', 'Failed on %s \nUsing %s' % (url, param))

    @pytest.mark.parametrize('product_alias', [
        {'product_name': 'firefox-beta-latest', 'lang': 'en-US'},
        {'product_name': 'firefox-latest-euballot', 'lang': 'en-GB'},
        {'product_name': 'firefox-latest', 'lang': 'en-US'},
        ])
    def test_redirect_for_firefox_aliases(self, testsetup, product_alias):

        if product_alias == {'product_name': 'firefox-latest', 'lang': 'en-US'}:
            pytest.xfail(reason='https://bugzilla.mozilla.org/show_bug.cgi?id=813968 - Alias returns 404')

        url = testsetup.base_url
        param = {
            'product': product_alias['product_name'],
            'os': 'win',
            'lang': product_alias['lang']
        }

        response = self._head_request(url, params=param)

        parsed_url = urlparse(response.url)

        if not (
            product_alias['product_name'] == 'firefox-latest-euballot' and
            "download.allizom.org" in testsetup.base_url
        ):
            Assert.equal(response.status_code, requests.codes.ok,
                'Redirect failed with HTTP status %s on %s \n \
                For %s\n \
                Redirected to %s' % \
                (response.status_code, url, param, response.url))
            Assert.equal(parsed_url.scheme, 'http', 'Failed on %s \nUsing %s' % (url, param))
            Assert.equal(parsed_url.netloc, 'download.cdn.mozilla.net', 'Failed on %s \nUsing %s' % (url, param))
            if (
                product_alias['product_name'] != 'firefox-nightly-latest' and
                product_alias['product_name'] != 'firefox-aurora-latest' and
                product_alias['product_name'] != 'firefox-latest-euballot'
            ):
                Assert.contains('/%s/' % 'win32', parsed_url.path)
