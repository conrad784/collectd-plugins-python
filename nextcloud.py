#!/usr/bin/env python

import collectd

import base


class NextcloudPlugin(base.Base):
    def __init__(self):
        base.Base.__init__(self)
        self.prefix = 'nextcloud'
        self.schema = "https"
        self.monitoring_path = "/ocs/v2.php/apps/serverinfo/api/v1/info?format=json"

    def get_data(self):
        import requests
        url = "{}://{}{}".format(self.schema, self.instance, self.monitoring_path)
        ret = requests.get(url, auth=(self.username, self.password))
        self.ret = ret
        self.text = ret.text
        if ret.ok:
            return_data = ret.json()["ocs"]["data"]
            self.data = return_data
            self.nextcloud_data = self.data["nextcloud"]
            self.server_data = self.data["server"]
            self.activeUsers = self.data["activeUsers"]

            return self.data
        else:
            return

    def get_stats(self):
        _ = self.get_data()
        data = {self.prefix: {}}

        data[self.prefix][self.instance] = {"users": {},
                                            "storage": {},
                                            "server": {}}
        data[self.prefix][self.instance]["users"] = {"user_count": self.user_count,
                                                     "user_active": self.user_active}

        data[self.prefix][self.instance]["storage"] = {"num_files": self.nextcloud_data["storage"]["num_files"],
                                                       "num_shares": self.nextcloud_data["shares"]["num_shares"]}
        data[self.prefix][self.instance]["server"] = {"freespace": self.nextcloud_data["system"]["freespace"],
                                                      "mem_used": self.mem_used}
        return data

    @property
    def user_count(self):
        if self.nextcloud_data:
            return self.nextcloud_data["storage"]["num_users"]
        else:
            return

    @property
    def user_active(self):
        if self.nextcloud_data:
            return self.activeUsers["last5minutes"]
        else:
            return

    @property
    def mem_used(self):
        if self.nextcloud_data:
            mem_total = self.nextcloud_data["system"]["mem_total"]
            mem_free = self.nextcloud_data["system"]["mem_free"]
            return mem_total-mem_free
        else:
            return


def configure_callback(conf):
    """Received configuration information"""
    plugin.config_callback(conf)


def read_callback():
    """Callback triggerred by collectd on read"""
    plugin.read_callback()


try:
    plugin = NextcloudPlugin()
    collectd.register_config(configure_callback)
    collectd.register_read(read_callback, plugin.interval)
except Exception as e:
    collectd.error("nextcloud: failed to initialize nextcloud plugin: {}".format(e))
