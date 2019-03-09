#!/usr/bin/env python
# mainly taken from https://github.com/rochaporto/collectd-openstack

import collectd
import datetime
import traceback


class Base(object):
    def __init__(self):
        self.username = 'admin'
        self.password = 'admin'
        self.verbose = False
        self.debug = False
        self.prefix = ''
        self.instance = 'localhost'
        self.interval = 10.0

    def config_callback(self, conf):
        """Takes a collectd conf object and fills in the local config."""
        for node in conf.children:
            if node.key == "Username":
                self.username = node.values[0]
            elif node.key == "Password":
                self.password = node.values[0]
            elif node.key == "Instance":
                self.instance = node.values[0]
            elif node.key == "Verbose":
                if node.values[0] in ['True', 'true']:
                    self.verbose = True
            elif node.key == "Debug":
                if node.values[0] in ['True', 'true']:
                    self.debug = True
            elif node.key == "Prefix":
                self.prefix = node.values[0]
            elif node.key == 'Interval':
                self.interval = float(node.values[0])
            else:
                collectd.warning("{}: unknown config key: {}".format(self.prefix, node.key))

    def dispatch(self, stats):
        """
        Dispatches the given stats.

        stats should be something like:

        {'plugin': {'plugin_instance': {'type': {'type_instance': <value>, ...}}}}
        """
        if not stats:
            collectd.error("{}: failed to retrieve stats".format(self.prefix))
            return

        self.logdebug("dispatching {} new stats :: {}".format(len(stats), stats))
        try:
            for plugin in stats.keys():
                for plugin_instance in stats[plugin].keys():
                    for group in stats[plugin][plugin_instance].keys():
                        group_value = stats[plugin][plugin_instance][group]
                        if not isinstance(group_value, dict):
                            self.dispatch_value(plugin, plugin_instance, group, None, group_value)
                        else:
                            for type_instance in stats[plugin][plugin_instance][group].keys():
                                self.dispatch_value(plugin, plugin_instance,
                                                    group, type_instance,
                                                    stats[plugin][plugin_instance][group][type_instance])
        except Exception as exc:
            collectd.error("{}: failed to dispatch values :: {} :: {}".format(self.prefix, exc,
                                                                              traceback.format_exc()))

    def dispatch_value(self, plugin, plugin_instance, group, type_instance, value):
        """Looks for the given stat in stats, and dispatches it"""
        self.logdebug("dispatching value {}.{}.{}.{}={}".format(plugin, plugin_instance,
                                                                group, type_instance, value))

        val = collectd.Values(type='gauge')
        val.plugin = plugin
        val.plugin_instance = plugin_instance
        # the documentation says it must be initialized with a valid type from
        # the types.db, but it works also with any other string and is easier
        # to "group" by this in Grafana
        # maybe this fails for other databases than InfluxDB? then revert back to
        # val.type_instance="{}-{}".format(group, type_instance)
        if type_instance is not None:
            val.type = group
            val.type_instance = type_instance
        else:
            val.type_instance = group
        val.values = [value]
        val.interval = self.interval
        val.dispatch()
        self.logdebug("sent metric {}.{}.{}.{}.{}".format(plugin, plugin_instance,
                                                          group, type_instance, value))

    def read_callback(self):
        try:
            start = datetime.datetime.now()
            stats = self.get_stats()
            self.logverbose("collectd new data from service :: took {} seconds".format((datetime.datetime.now() - start).seconds))
        except Exception as exc:
            collectd.error("{}: failed to get stats :: {} :: {}".format(self.prefix, exc,
                                                                        traceback.format_exc()))
        self.dispatch(stats)

    def get_stats(self):
        collectd.error('Not implemented, should be subclassed')

    def logverbose(self, msg):
        if self.verbose:
            collectd.info("{}: {}".format(self.prefix, msg))

    def logdebug(self, msg):
        if self.debug:
            collectd.info("{}: {}".format(self.prefix, msg))
