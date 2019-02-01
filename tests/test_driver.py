import pytest

import logging
from unittest import mock
from unittest.mock import patch
from chargestop.driver import Driver
from chargestop.client import Client
from chargestop.client import Session

LOW_POWER_SESSION = Session(
    is_active=True,
    is_fully_charged=False,
    is_paid=True,
    company_name='ACME',
    power_kw=0.01,
    session_id=376124401,
    device_id=151925,
    port_number=1
)

HIGH_POWER_SESSION = LOW_POWER_SESSION._replace(
    power_kw=4.56,
)

INACTIVE_SESSION = LOW_POWER_SESSION._replace(
    is_active=False,
    power_kw=0
)

@patch('chargestop.driver.time.sleep', return_value=None)
def test_active_sesssion_low_power_stops_charging(patched_sleep):
    client_mock = mock.Mock(spec=Client, autospec=True)
    client_mock.get_charging_session.return_value = LOW_POWER_SESSION

    driver = Driver(client=client_mock, company_name_whitelist=['Contoso', 'ACME'])
    driver._run_until(lambda state: str(state) == 'WaitForNewSession')

    client_mock.stop_charging.assert_called_once_with(LOW_POWER_SESSION)

@patch('chargestop.driver.time.sleep', return_value=None)
def test_stops_two_different_sessions(patched_sleep):
    client_mock = mock.Mock(spec=Client, autospec=True)
    client_mock.get_charging_session.return_value = LOW_POWER_SESSION

    driver = Driver(client=client_mock, company_name_whitelist=['Contoso', 'ACME'])
    driver._run_until(lambda state: str(state) == 'WaitForNewSession')

    client_mock.stop_charging.assert_called_once_with(LOW_POWER_SESSION)

    new_high_power_session = HIGH_POWER_SESSION._replace(session_id=1158)
    client_mock.get_charging_session.return_value = new_high_power_session
    driver._run_until(lambda state: str(state) == 'MonitorPowerUsage')

    new_low_power_session = LOW_POWER_SESSION._replace(session_id=1158)
    client_mock.get_charging_session.return_value = new_low_power_session
    driver._run_until(lambda state: str(state) == 'WaitForNewSession')

    client_mock.stop_charging.assert_called_with(new_low_power_session)
