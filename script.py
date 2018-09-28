
import urllib2
import json
import unittest
from time import sleep

__author__ = "Amitay Shahar"


class HttpClient(object):
    """
    Will handle HTTP calls, implementation of the API calls for server.
    """
    @staticmethod
    def request(url, method, data=None, headers={}, origin_req_host=None, unverifiable=False):
        req = urllib2.Request(url, headers=headers, data=data, origin_req_host=origin_req_host,
                              unverifiable=unverifiable)
        req.get_method = method
        TRIES_NUMBER = 2
        TRY_DELAY_SEC = 1
        err_msg = ''
        for i in xrange(TRIES_NUMBER):
            print 'Trying to send HTTP call (API), try number {0} out of {1}'.format(i, TRIES_NUMBER)
            try:
                res = urllib2.urlopen(req)
                print 'HTTP call succeeded'
                return res
            except urllib2.HTTPError, e:
                err_msg = 'HTTPError = ' + str(e.code) + ": " + e.read()
                sleep(TRY_DELAY_SEC)
            except urllib2.URLError, e:
                err_msg = 'URLError = ' + str(e)
                sleep(TRY_DELAY_SEC)

        # If we reached here, all of our server reporting trials have failed.
        raise RuntimeError('Requesting the server failed even after all the retries! - ', err_msg)


class TestForInterview(unittest.TestCase):
    @staticmethod
    def _call_api(api_server, api_call, method, body=None):
        """
        handles actual API calls
        :param api_server: requires API prefix to run. (mostly the server url)
        :param api_call: requires API postfix to run. (mostly the action or detailed call)
        :param method: required method. possible values: PUT, GET, POST
        :param body: optional, if API call requires a body - this is the place to put it
        :return: API results as is.
        """
        full_api = '{0}{1}'.format(api_server, api_call)
        print 'Started API call {0} to server {1}'.format(api_call, api_server)
        try:
            request = HttpClient.request(full_api, lambda: method, data=body, headers={'Content-Type': 'application/json'})
        except Exception, e:
            raise Exception("creating request {0} Failed: {1}".format(full_api, str(e)))
        try:
            response = request.read()
            api_result = json.loads(response)
        except Exception, e:
            raise Exception("Calling API {0} Failed: {1}".format(full_api, str(e)))
        print 'API call ended successfully'
        return api_result

    def _validate_results(self, api_results, dict_to_validate, count=0):
        """
        Will validate existence of 'dict_to_validate' inside 'api_results'
        :param api_results: api results from server, still in json format (dictionary)
        :param dict_to_validate: dictionary of values to search in api, can be dictionary or list
        :return: error message, if empty - no errors. (no exception on purpose, I want to go over ALL dictionaries
                 and then return message with missing values)
        """
        print 'Going to search values from dictionary in api results, nesting depth: {0}'.format(count)
        err_msg = ''
        res = list()
        for key in dict_to_validate:
            if isinstance(dict_to_validate.get(key), dict):
                # if nested dictionary - recursive call with inner values (for "Promotion" section)
                err_msg += self._validate_results(api_results[key], dict_to_validate.get(key), count+1)
            elif isinstance(api_results, list):
                # if nested list - search "contains" in favor of "Description" section
                if not res:
                    # filter only relevant results for current key
                    res = filter(lambda lambda_results: lambda_results[key] == dict_to_validate.get(key), api_results)
                # convert to dictionary
                res_dict = dict(pair for d in res for pair in d.items())
                if dict_to_validate.get(key) not in res_dict[key]:
                    err_msg += '[Error]: Key {0} got other value ({1}) then expected ({2})\n'.format(key, res_dict[key], dict_to_validate.get(key))
            else:
                # else just search for value inside api
                if dict_to_validate.get(key) != api_results[key]:
                    err_msg += '[Error]: Key {0} got other value ({1}) then expected ({2})\n'.format(key, api_results[key], dict_to_validate.get(key))
        return err_msg

    def test_should_pass(self):
        """
        This should pass, dictionary got expected values.
        1. Call API
        2. Build dictionary with values to search and validate (nested dict for 'Promotions')
        3. Call validate function and pass or fail test
        """
        print '\n**********\nGoing to test happy path'
        api_server = 'https://api.tmsandbox.co.nz'
        api_call = '/v1/Categories/6327/Details.json?catalogue=false'
        dict_to_validate = {'Name': 'Carbon credits', 'CanRelist': True, 'Promotions': {'Name': 'Gallery', 'Description': '2x larger image'}}
        result = self._call_api(api_server=api_server, api_call=api_call, method='GET')
        validate_results = self._validate_results(result, dict_to_validate)
        self.assertFalse(validate_results, 'Test Failed, errors are {0}'.format(validate_results))
        print '**********\nTest PASSED'

    def test_should_fail(self):
        """
        This test should fail:
            'Promotions' got name 'Basic' with the description of 'Gallery'
        1. Call API
        2. Build dictionary with values to search and validate (nested dict for 'Promotions')
        3. Call validate function and pass or fail test
        """
        print '\n**********\nGoing to test failure flow'
        api_server = 'https://api.tmsandbox.co.nz'
        api_call = '/v1/Categories/6327/Details.json?catalogue=false'
        dict_to_validate = {'Name': 'Carbon credits', 'CanRelist': True, 'Promotions': {'Name': 'Basic', 'Description': '2x larger image'}}
        result = self._call_api(api_server=api_server, api_call=api_call, method='GET')
        validate_results = self._validate_results(result, dict_to_validate)
        self.assertTrue(validate_results, 'Test Failed, Got wrong error message')
        print '**********\nTest PASSED'

    def test_should_fail_consecutive(self):
        """
        This test should fail with several errors:
            None existing name
            'CanRelist' is False instead of True
        1. Call API
        2. Build dictionary with values to search and validate (nested dict for 'Promotions')
        3. Call validate function and pass or fail test
        """
        print '\n**********\nGoing to test consecutive failure flow'
        api_server = 'https://api.tmsandbox.co.nz'
        api_call = '/v1/Categories/6327/Details.json?catalogue=false'
        dict_to_validate = {'Name': 'Some Other Name', 'CanRelist': False, 'Promotions': {'Name': 'Gallery', 'Description': '2x larger image'}}
        result = self._call_api(api_server=api_server, api_call=api_call, method='GET')
        validate_results = self._validate_results(result, dict_to_validate)
        self.assertTrue(validate_results, 'Test Failed, Got wrong error message')
        print '**********\nTest PASSED'

if __name__ == '__main__':
    unittest.main()
