import time
import sys
import logging
from abc import ABC
from abc import abstractmethod

WAIT_TO_MONITOR_POLL_FREQUENCY_MINUTES = 15
MONITOR_POLL_FREQUENCY_MINUTES = 2

logger = logging.getLogger(__name__)

class Driver:
    def __init__(self, *, client, company_name_whitelist):
        self.client = client
        self.company_name_whitelist = company_name_whitelist
        self.state = WaitToMonitor(self)

    def run(self):
        self._run_until(lambda state: False)

    """Used for unit testing where we want to run until a certain state"""
    def _run_until(self, predicate):
        self.client.login()
        while not predicate(self.state):
            logger.debug("Running {}".format(self.state))
            self.state = self.state.run()


class State(ABC):
    def __init__(self, driver):
        self.driver = driver
        self.client = driver.client

    """
    Run the current current state and return the next state once complete
    """
    @abstractmethod
    def run(self):
        pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__

class WaitToMonitor(State):
    def run(self):
        logger.info("Checking every {} minutes for an charging session to monitor".format(WAIT_TO_MONITOR_POLL_FREQUENCY_MINUTES))
        while True:
            session = self.client.get_charging_session()

            if session.is_active:
                logger.info("Found an active session: {}".format(session))
                if not session.is_paid:
                    logger.info("Not monitoring this session because it is free")
                    return WaitForNewSession(self.driver, session)
                if self.driver.company_name_whitelist is not None and session.company_name not in self.driver.company_name_whitelist:
                    logger.info("Not monitoring this session because company name {} is not in the whitelist {}".format(
                        session.company_name, self.driver.company_name_whitelist))
                    return WaitForNewSession(self.driver, session)

                return MonitorPowerUsage(self.driver, session)

            logger.debug("The most recent session is not active: {}".format(session))
            time.sleep(WAIT_TO_MONITOR_POLL_FREQUENCY_MINUTES * 60)

class MonitorPowerUsage(State):
    def __init__(self, driver, session_to_monitor):
        super().__init__(driver)
        self.session_to_monitor = session_to_monitor
        self.low_power_usage_count = 0

    def run(self):
        logger.info("Monitoring the session every {} minutes to check if charging is likely done".format(MONITOR_POLL_FREQUENCY_MINUTES))
        while True:
            session = self.client.get_charging_session()

            if session.session_id != self.session_to_monitor.session_id:
                logger.info("The most recent session has changed: {}".format(session))
                return WaitToMonitor(self.driver)
            if not session.is_active:
                logger.info("Session no longer active: {}".format(session))
                return WaitToMonitor(self.driver)

            if _power_usage_low(session):
                self.low_power_usage_count = self.low_power_usage_count + 1
                logger.debug("Power usage has been low for {} iteration: {}".format(self.low_power_usage_count, session))
            else:
                self.low_power_usage_count = 0
                logger.debug("Power usage is not currently low: {}".format(session))

            # TODO configure this
            if self.low_power_usage_count >= 3:
                logger.info("Power usage has been low for a while: {}".format(session))
                return StopCharging(self.driver, session)

            if session.is_fully_charged:
                logger.info("Station thinks the car is fully charged: {}".format(session))
                return StopCharging(self.driver, session)

            time.sleep(MONITOR_POLL_FREQUENCY_MINUTES * 60)

def _power_usage_low(session):
    # TODO configure this
    return session.power_kw < 0.1

class StopCharging(State):
    def __init__(self, driver, session):
        super().__init__(driver)
        self.session = session

    def run(self):
        logger.info("Attempting to stop charging")
        self.client.stop_charging(self.session)
        logger.info("Stopped charging successfully")
        return WaitForNewSession(self.driver, self.session)

class WaitForNewSession(State):
    def __init__(self, driver, current_session):
        super().__init__(driver)
        self.current_session = current_session

    def run(self):
        logger.info("Checking every {} minutes for a new charging session".format(WAIT_TO_MONITOR_POLL_FREQUENCY_MINUTES))
        while True:
            session = self.client.get_charging_session()
            if session.session_id != self.current_session.session_id:
                logger.info("Found a new session: {}".format(session))
                return WaitToMonitor(self.driver)

            logger.debug("The session is still the same as before: {}".format(session))

            time.sleep(WAIT_TO_MONITOR_POLL_FREQUENCY_MINUTES * 60)
