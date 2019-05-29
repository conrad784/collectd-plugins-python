#!/usr/bin/env python

import collectd

import base


class EmbyPlugin(base.Base):
    def __init__(self):
        base.Base.__init__(self)
        self.prefix = 'emby'
        self.schema = "http"
        self.port = 8096

    def get_data(self):
        import requests
        self.base_url = "{}://{}:{}/emby".format(self.schema, self.instance, self.port)
        headers = {"X-Emby-Token": self.password}
        # system_info = "{}/System/Info?".format(self.base_url)
        # ret_system = requests.get(system_info, headers=headers)
        # user_info = "{}/Users/{}/Items?Recursive=true".format(self.base_url,
        #                                                       self.username)
        sessions = "{}/Sessions".format(self.base_url)
        # ret_user = requests.get(user_info, headers=headers)
        ret_sessions = requests.get(sessions, headers=headers)
        self.sessions = ret_sessions
        if ret_sessions.ok:
            return_data = ret_sessions.json()
            self.data = return_data

            return self.data
        else:
            return

    def get_stats(self):
        sessions = self.get_data()
        session_count = 0
        if sessions:
            for s in sessions:
                if s.get("Client") in ["collectd"]:
                    continue
                session_count += 1

        data = {self.prefix: {}}

        data[self.prefix][self.instance] = {"users": {}}
        data[self.prefix][self.instance]["users"] = {"sessions_active": session_count}

        return data


def configure_callback(conf):
    """Received configuration information"""
    plugin.config_callback(conf)


def read_callback():
    """Callback triggerred by collectd on read"""
    plugin.read_callback()


try:
    plugin = EmbyPlugin()
    collectd.register_config(configure_callback)
    collectd.register_read(read_callback, plugin.interval)
except Exception as e:
    collectd.error("emby: failed to initialize emby plugin: {}".format(e))


# if __name__=="__main__":
#     from secret import *
#     plugin = EmbyPlugin()
#     plugin.instance = emby_instance
#     plugin.apikey = emby_apikey
#     plugin.user = emby_user
