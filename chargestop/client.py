import logging
import requests
from collections import namedtuple

logger = logging.getLogger(__name__)

MOBILEAPI_ENDPOINT = 'https://webservices.chargepoint.com/backend.php/mobileapi/v3'
ACTIVITY_ENDPOINT = 'https://mc.chargepoint.com/map-prod/v2'

Session = namedtuple('Session', ['is_active', 'is_fully_charged', 'is_paid', 'company_name', 'power_kw', 'session_id', 'device_id', 'port_number'])

"""A client that talks to the ChargePoint API"""
class Client:
    def __init__(self, *, username, password):
        self.username = username
        self.password = password
        self._user_id = None
        self._session = requests.Session()

    def login(self):
        request = {
            'validate_login': {
                'user_name': self.username,
                'password': self.password
            }
        }
        logger.debug("Sending login request: {}".format(request))
        response = self._session.post(MOBILEAPI_ENDPOINT, json=request)
        logger.debug("Recieved login response: {}".format(response.text))

        login_data = self._check_for_success(response)

        # Other APIs want user_id as a number, so it's converted right here
        self._user_id = int(login_data['user_id'])

        logger.info("Successfully logged in as {}".format(self.username))

    def stop_charging(self, session):
        if not self._user_id:
            raise RuntimeError("User id not known yet. Perhaps login was not yet successful?")

        request = {
            'user_id': self._user_id,
            'stop_session': {
                'device_id': session.device_id,
                'port_number': session.port_number
            }
        }
        logger.debug("Sending stop charging request: {}".format(request))
        response = self._session.post(MOBILEAPI_ENDPOINT, json=request)
        logger.debug("Recieved stop charging response: {}".format(response.text))

        self._check_for_success(response)
        logger.info("Successfully stopped charging for session {}".format(session))

    def get_charging_session(self):
        if not self._user_id:
            raise RuntimeError("User id not known yet. Perhaps login was not yet successful?")

        request = {
            'user_id': self._user_id,
            'charging_activity': {
                'page_size': 1
            }
        }
        logger.debug("Sending charging activity request: {}".format(request))
        response = self._session.get(ACTIVITY_ENDPOINT, json=request)
        logger.debug("Recieved charging activity response: {}".format(response.text))

        activity_data = self._check_for_success(response)

        most_recent_session = activity_data['session_info'][0]
        return Session(
            is_active=self._get_is_active(most_recent_session),
            is_paid=self._get_is_paid(most_recent_session),
            is_fully_charged=most_recent_session['current_charging']=='fully_charged',
            company_name=most_recent_session['company_name'],
            power_kw=most_recent_session['power_kw'],
            session_id=most_recent_session['session_id'],
            device_id=most_recent_session['device_id'],
            port_number=most_recent_session['outlet_number']
        )

    def _get_is_active(self, most_recent_session):
        current_charging = most_recent_session['current_charging']
        if current_charging == 'in_use':
            return True
        elif current_charging == 'waiting':
            return True
        elif current_charging == 'fully_charged':
            return True
        elif current_charging == 'done':
            return False
        else:
            raise RuntimeError("Unhandled 'current_charging' state: {}".format(current_charging))

    def _get_is_paid(self, most_recent_session):
        payment_type = most_recent_session['payment_type']
        if payment_type == 'paid':
            return True
        elif payment_type == 'free':
            return False
        else:
            raise RuntimeError("Unhandled 'payment_type' state: {}".format(payment_type))

    def _check_for_success(self, response):
        if response.status_code != 200:
            raise RuntimeError("Got an unsuccessful HTTP status of {} with response {}".format(response.status, response.text))

        response_dict = response.json()

        # This is how the ACTIVITY_ENDPOINT typically relays errors
        if 'error' in response_dict:
            raise RuntimeError("Response contained an error: {}".format(response_dict))

        if len(response_dict.items()) != 1:
            raise RuntimeError("Response was expected to contain a single top-level key-value pair but was {}".format(response_dict))
        data = next(iter(response_dict.values()))

        # This is how the MOBILEAPI_ENDPOINT typically relays errors
        if data.get('status') == False:
            raise RuntimeError("Response contained an error: {}".format(response_dict))

        return data
