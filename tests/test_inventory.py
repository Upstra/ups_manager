import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from data_retriever.inventory import event_record, host_record, vm_record


class InventoryTest(unittest.TestCase):
    def test_powered_on_vm_has_cpu_percent(self):
        record = vm_record("vm-1", {
            "name": "db-pg-02",
            "runtime.powerState": "poweredOn",
            "runtime.host": SimpleNamespace(_moId="host-33"),
            "summary.quickStats.overallCpuUsage": 4600,
            "summary.runtime.maxCpuUsage": 18400,
            "summary.quickStats.uptimeSeconds": 120,
        })
        self.assertEqual(record["hostMoid"], "host-33")
        self.assertEqual(record["cpuPercent"], 25.0)
        self.assertEqual(record["uptimeSeconds"], 120)

    def test_powered_off_vm_and_host_without_capacity(self):
        vm = vm_record("vm-2", {
            "runtime.powerState": "poweredOff",
            "summary.quickStats.overallCpuUsage": 0,
            "summary.runtime.maxCpuUsage": 0,
        })
        host = host_record("host-1", {
            "summary.quickStats.overallCpuUsage": 1000,
            "summary.hardware.cpuMhz": 2000,
            "summary.hardware.numCpuCores": 4,
            "summary.quickStats.overallMemoryUsage": 512,
        })
        self.assertIsNone(vm["cpuPercent"])
        self.assertIsNone(vm["uptimeSeconds"])
        self.assertEqual(host["cpuPercent"], 12.5)
        self.assertIsNone(host["memoryPercent"])

    def test_event_record(self):
        event = SimpleNamespace(
            key=884213,
            createdTime=datetime(2026, 11, 4, 20, 5, 10, tzinfo=timezone.utc),
            userName="VSPHERE.LOCAL\\svc-upstra",
            vm=SimpleNamespace(vm=SimpleNamespace(_moId="vm-1042"), name="db-pg-02"),
            host=SimpleNamespace(host=SimpleNamespace(_moId="host-33"), name="esx-03"),
            fullFormattedMessage="db-pg-02 on esx-03 in DC-1 is powered off",
            eventTypeId=None,
        )
        record = event_record(event)
        self.assertEqual(record["createdAt"], "2026-11-04T20:05:10.000Z")
        self.assertEqual(record["vmMoid"], "vm-1042")
        self.assertEqual(record["hostName"], "esx-03")
        self.assertEqual(record["type"], "SimpleNamespace")


if __name__ == "__main__":
    unittest.main()
