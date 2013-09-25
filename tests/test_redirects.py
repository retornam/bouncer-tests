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

    # fails when run against stage - xfailed for
    # https://bugzilla.mozilla.org/show_bug.cgi?id=801928
    @pytest.mark.xfail(
        "config.getvalue('base_url') == 'http://download.allizom.org'"
    )
    def test_that_checks_redirect_using_incorrect_query_values(self, base_url):
        param = {
            'product': 'firefox-16.0b6',
            'lang': 'kitty_language',
            'os': 'stella'
        }
        response = self._head_request(base_url, params=param)

        Assert.equal(
            response.status_code,
            requests.codes.not_found,
            self.response_info_failure_message(
                base_url,
                param,
                response
            )
        )

        parsed_url = urlparse(response.url)
        Assert.equal(
            parsed_url.scheme,
            'http',
            'Failed by redirected to incorrect scheme %s. \n %s' %
            (parsed_url.scheme, self.response_info_failure_message(
                base_url,
                param,
                response))
        )
        Assert.equal(
            parsed_url.netloc,
            urlparse(base_url).netloc,
            self.response_info_failure_message(
                base_url,
                param,
                response)
        )
        Assert.equal(
            parsed_url.query,
            urlencode(param),
            self.response_info_failure_message(
                base_url,
                param,
                response)
        )

    def test_that_checks_redirect_using_locales_and_os(
        self,
        base_url,
        lang,
        os
    ):
        # Ja locale has a special code for mac
        if lang == 'ja' and os == 'osx':
            lang = 'ja-JP-mac'

        param = {
            'product': 'firefox-16.0b6',
            'lang': lang,
            'os': os
        }

        response = self._head_request(base_url, params=param)

        parsed_url = urlparse(response.url)

        Assert.equal(
            response.status_code,
            requests.codes.ok,
            'Redirect failed with HTTP status %s. \n %s' %
            (response.status_code, self.response_info_failure_message(
                base_url,
                param,
                response))
        )
        Assert.equal(
            parsed_url.scheme,
            'http',
            'Failed by redirected to incorrect scheme %s. \n %s' %
            (parsed_url.scheme, self.response_info_failure_message(
                base_url,
                param,
                response))
        )

    @pytest.mark.xfail(reason='there currently is not a stub installer -- '
                       'xfailing until one lands in the wild')
    def test_stub_installer_redirect_for_en_us_and_win(self, base_url, product):
        param = {
            'product': product,
            'lang': 'en-US',
            'os': 'win'
        }

        response = self._head_request(base_url, params=param)

        parsed_url = urlparse(response.url)

        Assert.equal(
            response.status_code,
            requests.codes.ok,
            'Redirect failed with HTTP status %s. \n %s' %
            (response.status_code, self.response_info_failure_message(
                base_url,
                param,
                response))
        )

    @pytest.mark.parametrize('product_alias', [
        {'product_name': 'firefox-beta-latest', 'lang': 'en-US'},
        {'product_name': 'firefox-latest-euballot', 'lang': 'en-GB'},
        {'product_name': 'firefox-latest', 'lang': 'en-US'},
    ])
    def test_redirect_for_firefox_aliases(self, base_url, product_alias):

        if product_alias == {
            'product_name': 'firefox-latest',
            'lang': 'en-US'
        } and base_url == 'http://download.allizom.org':
            pytest.xfail(
                reason='https://bugzilla.mozilla.org/show_bug.cgi?id=813968 - '
                'Alias returns 404')

        param = {
            'product': product_alias['product_name'],
            'os': 'win',
            'lang': product_alias['lang']
        }

        response = self._head_request(base_url, params=param)

        parsed_url = urlparse(response.url)

        if not (
            product_alias['product_name'] == 'firefox-latest-euballot' and
            "download.allizom.org" in base_url
        ):
            Assert.equal(
                response.status_code,
                requests.codes.ok,
                'Redirect failed with HTTP status %s. \n %s' %
                (response.status_code, self.response_info_failure_message(
                    base_url,
                    param,
                    response))
            )
            if (
                product_alias['product_name'] != 'firefox-nightly-latest' and
                product_alias['product_name'] != 'firefox-aurora-latest' and
                product_alias['product_name'] != 'firefox-latest-euballot'
            ):
                Assert.contains('/%s/' % 'win32', parsed_url.path,
                                '\n %s' % self.response_info(response))

    def test_robotstxt_exists(self, base_url):

        url = '%s/robots.txt' % base_url
        response = self._head_request(url)

        Assert.equal(
            response.status_code,
            requests.codes.ok,
            'Robots.txt does not exist'
        )
