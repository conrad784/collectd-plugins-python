#!/usr/bin/env python
# a lot of inspiration taken from
# https://bitbucket.org/hlauer/axp/src/master/axp.py  (C) 2020-2021 Hermann Lauer
# for more information about the used pmu https://linux-sunxi.org/AXP209
# (C) 2021 Conrad Sachweh
#

import collectd

import base
import os

class Value:
    """calulate a value"""

    def __init__(self, path):
        """store offset and scale"""

        self.path = path + '_'
        self.scale = float(open(self.path + 'scale').read())
        self.offset = 0
        try:
          self.offset = int(open(self.path + 'offset').read())
        except IOError: pass

    def __call__(self):
        raw=int(open(self.path + 'raw').read())
        return (raw + self.offset) * self.scale


class BananapiPmicPlugin(base.Base):
    def __init__(self):
        base.Base.__init__(self)
        self.prefix = 'bananapi_pmic'
        self.names = {'usb_voltage':'in_voltage0',
	              'usb_current':'in_current0',
	              'usb_otg_voltage':'in_voltage1',
	              'usb_otg_current':'in_current1',
	              'pmic_temp':'in_temp',
	              'gpio0_voltage':'in_voltage3',
	              'gpio1_voltage':'in_voltage4',
	              'ips_voltage':'in_voltage5',
	              'battery_voltage':'in_voltage6',
	              'battery_charge_current':'in_current2',
	              'battery_discharge_current':'in_current3'}
        self.instance = '/sys/bus/platform/devices/axp20x-adc'
        filenames = os.listdir(self.instance)
        devicename = ""
        # auto-detect, can be overwritten by confi file
        for entry in filenames:
            if entry.startswith("iio"):
                devicename = entry
        self.instance = os.path.join(self.instance, devicename) + "/"

    def config_callback(self, conf):
        """Takes a collectd conf object and fills in the local config."""
        for node in conf.children:
            if node.key == "Verbose":
                if node.values[0] in ['True', 'true']:
                    self.verbose = True
            elif node.key == "Debug":
                if node.values[0] in ['True', 'true']:
                    self.debug = True
            elif node.key == "Prefix":
                self.prefix = node.values[0]
            elif node.key == "Instance":
                self.instance = node.values[0]
            else:
                collectd.warning("{}: unknown config key: {}".format(self.prefix, node.key))

    def get_data(self):
        self.measurements=[(k,Value(os.path.join(self.instance, v))) for k,v in self.names.items()]
        self.data = {}
        for k,v in self.measurements:
            while True:
                try:
                    self.data[k]=v()
                    break
                except TimeoutError as e:
                    self.logerror("read ({}) {}".format(k,e))
        return self.data

    def get_stats(self):
        stats = self.get_data()

        data = {self.prefix: {}}
        data[self.prefix][self.instance] = {self.instance: {}}

        for key, value in stats.items():
            data[self.prefix][self.instance][key] = value

        return data


def configure_callback(conf):
    """Received configuration information"""
    plugin.config_callback(conf)


def read_callback():
    """Callback triggerred by collectd on read"""
    plugin.read_callback()


try:
    plugin = BananapiPmicPlugin()
    collectd.register_config(configure_callback)
    collectd.register_read(read_callback, plugin.interval)
except Exception as e:
    collectd.error("BananapiPmicPlugin: failed to initialize BananapiPmic plugin: {}".format(e))


# if __name__=="__main__":
#     plugin = BananapiPmicPlugin()
#     data = plugin.get_stats()
#     print(data)
