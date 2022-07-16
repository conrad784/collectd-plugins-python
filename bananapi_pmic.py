#!/usr/bin/env python
# a lot of implementation taken from
# https://bitbucket.org/hlauer/axp/src/master/axp.py  (C) 2020-2021 Hermann Lauer

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
        self.prefix = 'pmic'
        self.names = {'acinV':'in_voltage0',
	              'acinI':'in_current0',
	              'vbusV':'in_voltage1',
	              'vbusI':'in_current1',
	              'temp':'in_temp',
	              'gpio0V':'in_voltage3',
	              'gpio1V':'in_voltage4',
	              'ipsoutV':'in_voltage5',
	              'batV':'in_voltage6',
	              'batOI':'in_current2',
	              'batII':'in_current3'}
        self.path = '/sys/bus/platform/devices/axp20x-adc/iio:device0'

    def get_data(self):
        self.measurements=[(k,Value(os.path.join(self.path, v))) for k,v in self.names.items()]
        self.data = {}
        for k,v in self.measurements:
            while True:
                try:
                    self.data[k]=v()
                    break
                except TimeoutError as e:
                    print("read ({}) {}".format(k,e))
        return self.data

    def get_stats(self):
        stats = self.get_data()

        data = {self.prefix: {}}
        data[self.prefix][self.instance] = {self.path: {}}

        for key, value in stats.items():
            data[self.prefix][self.instance][self.path][key] = value

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
