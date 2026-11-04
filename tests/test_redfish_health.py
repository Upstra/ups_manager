import unittest

from data_retriever.redfish_health import parse_health

THERMAL = {
    "Temperatures": [
        {"Name": "01-Inlet Ambient", "ReadingCelsius": 31, "UpperThresholdNonCritical": 42, "UpperThresholdCritical": 46, "Status": {"State": "Enabled", "Health": "OK"}},
        {"Name": "02-CPU 1", "ReadingCelsius": 68, "Status": {"State": "Enabled", "Health": "OK"}},
    ],
    "Fans": [{"Name": "Fan 1", "Reading": 34, "Status": {"State": "Enabled", "Health": "OK"}}],
}
POWER = {
    "PowerControl": [{"PowerConsumedWatts": 412, "PowerCapacityWatts": 1600}],
    "PowerSupplies": [
        {"Name": "PSU 1", "Status": {"State": "Enabled", "Health": "OK"}, "PowerCapacityWatts": 800, "LastPowerOutputWatts": 412},
        {"Name": "PSU 2", "Status": {"State": "Absent"}},
    ],
}
SYSTEM = {"Model": "ProLiant DL380 Gen11", "SerialNumber": "CZ2D1F0ABC", "PowerState": "On", "Status": {"HealthRollup": "Warning"}}


class RedfishHealthTest(unittest.TestCase):
    def test_full_response(self):
        health = parse_health(THERMAL, POWER, SYSTEM, "iLO 5")
        self.assertEqual(health["thermal"]["inletC"], 31)
        self.assertEqual(health["thermal"]["inletCritC"], 46)
        self.assertEqual(health["thermal"]["maxCpuC"], 68)
        self.assertEqual(health["power"]["consumedW"], 412)
        self.assertEqual(health["system"]["health"], "Warning")

    def test_missing_inlet_sensor(self):
        thermal = {"Temperatures": [THERMAL["Temperatures"][1]]}
        health = parse_health(thermal, {}, {}, None)
        self.assertIsNone(health["thermal"]["inletC"])
        self.assertIsNone(health["power"]["consumedW"])
        self.assertEqual(health["power"]["supplies"], [])

    def test_absent_supply_stays_listed(self):
        supplies = parse_health(THERMAL, POWER, SYSTEM, "iLO 5")["power"]["supplies"]
        self.assertEqual(len(supplies), 2)
        self.assertEqual(supplies[1], {"name": "PSU 2", "state": "Absent", "health": None, "capacityW": None, "outputW": None})


if __name__ == "__main__":
    unittest.main()
